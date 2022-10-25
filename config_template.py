import os

# Data
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'cs224w_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'vagrant')

DATABASE_URL = 'postgresql://' + POSTGRES_USER + ':' \
                + POSTGRES_PASSWORD + '@' \
                + POSTGRES_HOST + ':' \
                + POSTGRES_PORT + '/' \
                + POSTGRES_DATABASE

# google api key
def get_google_key():
    return "mYgOoGlEkeY"