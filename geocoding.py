"""
Python script for batch geocoding of addresses using the Google Geocoding API.
This script allows for massive lists of addresses to be geocoded for free by pausing when the
geocoder hits the free rate limit set by Google (2500 per day).  If you have an API key for paid
geocoding from Google, set it in the API key section.
Addresses for geocoding can be specified in a list of strings "addresses". In this script, addresses
come from a csv file with a column "Address". Adjust the code to your own requirements as needed.
After every 500 successul geocode operations, a temporary file with results is recorded in case of
script failure / loss of connection later.
Addresses and data are held in memory, so this script may need to be adjusted to process files line
by line if you are processing millions of entries.
Shane Lynn
5th November 2016
"""
import pandas as pd
import requests
import logging
import time
import settings

from geopandas.tools import geocode


def get_google_results(address, api_key=None, return_full_response=False):
    """
    Get geocode results from Google Maps Geocoding API.

    Note, that in the case of multiple google geocode reuslts, this function returns details of the FIRST result.

    @param address: String address as accurate as possible. For Example "18 Grafton Street, Dublin, Ireland"
    @param api_key: String API key if present from google.
                    If supplied, requests will use your allowance from the Google API. If not, you
                    will be limited to the free usage of 2500 requests per day.
    @param return_full_response: Boolean to indicate if you'd like to return the full response from google. This
                    is useful if you'd like additional location details for storage or parsing later.
    """
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}".format(address)
    if api_key is not None:
        geocode_url = geocode_url + "&key={}".format(api_key)

    results = requests.get(geocode_url)
    results = results.json()

    if len(results['results']) == 0:
        output = {
            "formatted_address": None,
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "google_place_id": None,
            "type": None,
            "postcode": None
        }
    else:
        answer = results['results'][0]
        output = {
            "formatted_address": answer.get('formatted_address'),
            "latitude": answer.get('geometry').get('location').get('lat'),
            "longitude": answer.get('geometry').get('location').get('lng'),
            "accuracy": answer.get('geometry').get('location_type'),
            "google_place_id": answer.get("place_id"),
            "type": ",".join(answer.get('types')),
            "postcode": ",".join([x['long_name'] for x in answer.get('address_components')
                                  if 'postal_code' in x.get('types')])
        }

    output['input_string'] = address
    output['number_of_results'] = len(results['results'])
    output['status'] = results.get('status')
    if return_full_response is True:
        output['response'] = results

    return output


def check_google_api_connection():
    """
    :return:
    """
    test_result = get_google_results("London, England", settings.API_KEY, settings.RETURN_FULL_RESULTS)
    if (test_result['status'] != 'OK') or (test_result['formatted_address'] != 'London, UK'):
        logging.warning("There was an error when testing the Google Geocoder.")
        raise ConnectionError(
            'Problem with test results from Google Geocode - check your API key and internet connection.')


def google_geocoding(input_filename, output_filename, key):
    """
    :param input_filename:
    :param output_filename:
    :param key:
    :return:
    """
    results = []

    check_google_api_connection()
    data = pd.read_csv(input_filename, encoding='utf8', sep=';')

    if settings.ADDRESS_COLUMN not in data.columns:
        raise ValueError("Missing Address column in input data")

    addresses = data[settings.ADDRESS_COLUMN].tolist()

    for address in addresses:
        geocoded = False
        while geocoded is not True:
            try:
                geocode_result = get_google_results(address, key,
                                                    return_full_response=settings.RETURN_FULL_RESULTS)
            except Exception as e:
                logging.exception(e)
                logging.error("Major error with {}".format(address))
                logging.error("Skipping!")
                geocoded = True

            # If we're over the API limit, backoff for a while and try again later.
            if geocode_result['status'] == 'OVER_QUERY_LIMIT':
                logging.info("Hit Query Limit! Backing off for a bit.")
                time.sleep(settings.BACKOFF_TIME * 60)  # sleep for 30 minutes
                geocoded = False
            else:
                # If we're ok with API use, save the results
                # Note that the results might be empty / non-ok - log this
                if geocode_result['status'] != 'OK':
                    logging.warning("Error geocoding {}: {}".format(address, geocode_result['status']))
                logging.debug("Geocoded: {}: {}".format(address, geocode_result['status']))
                results.append(geocode_result)
                geocoded = True

        if len(results) % 100 == 0:
            logging.info("Completed {} of {} address".format(len(results), len(addresses)))

        if len(results) % 500 == 0:
            pd.DataFrame(results).to_csv("{}_bak".format(output_filename))

    logging.info("Finished geocoding all addresses")
    pd.DataFrame(results).to_csv(output_filename, encoding='utf8')


def pandas_geocoding(input, output, provider, key):
    """
    Usage: python main.py -in /data/technite/csv/medicos.csv -out
    /data/technite/shp/output-medicos.shp -api geocoding -verbose True
    :param input:
    :param output:
    :param provider:
    :param key:
    :return:
    """
    logging.info("Reading CSV file...")
    data = pd.read_csv(input, encoding='utf8', sep=';')

    logging.info("Geocoding addresses using pandas geocode...")
    if provider == 'google':
        geo = geocode(data[settings.ADDRESS_COLUMN], provider=provider, api_key=key)
    else:
        geo = geocode(data[settings.ADDRESS_COLUMN], provider=provider)

    join = geo.join(data)

    logging.info("Saving shapefile...")
    join.to_file(output)
