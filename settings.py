from decouple import config

API_KEY = config('API_KEY', default='YOUR_API')
BACKOFF_TIME = 30
RETURN_FULL_RESULTS = False

ADDRESS_COLUMN = 'bairro'
