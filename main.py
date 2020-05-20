import sys
import time
import logging
import argparse
import geocoding
import settings

from coloredlogs import ColoredFormatter


def main(input, output, api):
    """
    :param input:
    :param output:
    :param api:
    :return:
    """
    start_time = time.time()

    if api == 'geocoding':
        geocoding.pandas_geocoding(input, output, 'nominatim', settings.API_KEY)

    end_time = time.time()
    logging.info("Whole process completed! [Time: {0:.5f} seconds]!".format(end_time - start_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Set of usefull scripts to use Google APIs')
    parser.add_argument('-api', action="store", dest='api', help='Select the Google API you want to use')
    parser.add_argument('-in', action="store", dest='input', help='Input CSV file')
    parser.add_argument('-out', action="store", dest='output', help='Output SHP file')
    parser.add_argument('-verbose', action="store", dest='verbose', help='Print log of processing')
    args = parser.parse_args()

    if bool(args.verbose):
        log = logging.getLogger('')

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        cf = ColoredFormatter("[%(asctime)s] {%(filename)-15s:%(lineno)-4s} %(levelname)-5s: %(message)s ")
        ch.setFormatter(cf)
        log.addHandler(ch)

        fh = logging.FileHandler('logging.log')
        fh.setLevel(logging.INFO)
        ff = logging.Formatter("[%(asctime)s] {%(filename)-15s:%(lineno)-4s} %(levelname)-5s: %(message)s ",
                               datefmt='%Y.%m.%d %H:%M:%S')
        fh.setFormatter(ff)
        log.addHandler(fh)

        log.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")

    main(args.input, args.output, args.api)
