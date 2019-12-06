from os import environ

API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
MONGO_AUTH_COLLECTION = 'google_credentials'
HEROKU_APP_NAME = 'botorganizer2019'
URL = "https://{}.herokuapp.com/".format(HEROKU_APP_NAME)
MONGO_AUTH_COLLECTION = 'google_credentials'

TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = environ.get('TELEGRAM_BOT_URL')
CLIENT_CONFIG_DATA = {
    "web":
        {
            "client_id": environ.get('GOOGLE_CLIENT_ID'),
            "project_id": environ.get('GOOGLE_PROJECT_ID'),
            "auth_uri": environ.get('GOOGLE_AUTH_URI'),
            "token_uri": environ.get('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url":
            environ.get('GOOGLE_AUTH_CERT_URI'),
            "client_secret": environ.get('GOOGLE_CLIENT_SECRET')}
        }
MONGO_URI = environ.get('MONGODB_URI')+'?retryWrites=false'
SECRET_KEY = environ.get('FLASK_SESSION_KEY')
