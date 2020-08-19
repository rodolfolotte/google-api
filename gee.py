import pickle
import os.path

from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Api:
    """ Shows basic usage of the Apps Script API.
    Call the Apps Script API to create a new script project, upload a file to the
    project, and log the script's URL to the user.
    """

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/script.projects']

    SAMPLE_CODE = '''
    function helloWorld() {
      console.log("Hello, world!");
    }
    '''.strip()

    SAMPLE_MANIFEST = '''
    {
      "timeZone": "America/New_York",
      "exceptionLogging": "CLOUD"
    }
    '''.strip()

    def call_api(self):
        """Calls the Apps Script API.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('script', 'v1', credentials=creds)

        try:
            # Create a new project
            request = {'title': 'My Script'}
            response = service.projects().create(body=request).execute()

            # Upload two files to the project
            request = {
                'files': [{
                    'name': 'hello',
                    'type': 'SERVER_JS',
                    'source': self.SAMPLE_CODE
                }, {
                    'name': 'appsscript',
                    'type': 'JSON',
                    'source': self.SAMPLE_MANIFEST
                }]
            }
            response = service.projects().updateContent(
                body=request,
                scriptId=response['scriptId']).execute()
            print('https://script.google.com/d/' + response['scriptId'] + '/edit')
        except errors.HttpError as error:
            # The API encountered a problem.
            print(error.content)
