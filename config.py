"""
Config file passes a configuration object to app.py, setting the paramaters for flask. Right now, we hard code many of our
configuration settings, but in the future, we should look into loading these from environment variables.

Base config contains all config settings that apply regardless of environment.
"""

from os import path, environ
from secrets import choice
from string import ascii_letters, digits
import datetime as dt

# Set the base directory to be the absolute path to this file
basedir = path.abspath(path.dirname(__file__))


class BaseConfig(object):

    # Direct SQLALCHEMY to the database through the environment variable (hosted) or the local psql database if running locally

    if environ.get('DEV_ENV') == ('prod' or 'staging'):
        SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') + '?sslmode=require'
    else:
        SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') 
    
    DEBUG = True  # should only be used for development

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Tells all exceptions and their responses to propagate up to the server
    PROPAGATE_EXCEPTIONS = True

    JWT_ACCESS_TOKEN_EXPIRES = dt.timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = dt.timedelta(minutes=1)
    # 1 day before csrf times out
    WTF_CSRF_TIME_LIMIT = 86400

    # Allow blacklisting for access and refresh tokens
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # JWT tokens will be found in the cookies
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = True

    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/refresh'
    JWT_COOKIE_CSRF_PROTECT = False

    # allows for referrer to not match origin for csrf token
    WTF_CSRF_SSL_STRICT = False

    # get the secret key for api encryption. This needs to be moved to getting a secure environment variable and is one of
    # the most insecure things about this app. People should never ever be able to see the secret key
    SECRET_KEY = environ.get('SECURE_KEY') or ''.join(
        choice(ascii_letters + digits) for i in range(64))

    # allow only these headers to bypass cors
    CORS_HEADERS = 'Content-Type, X-CSRFToken'


class DevelopmentConfig(BaseConfig):
    # algorithm hashing rounds (reduced for testing purposes only!)
    # store as string in env variable
    # couldnt get it to be recognized by the tests if in config obj
    environ["PASSWORD_HASH_ROUNDS"] = "4"


class TestingConfig(BaseConfig):
    environ["PASSWORD_HASH_ROUNDS"] = "4"

    # Enable the TESTING flag to disable the error catching during request handling
    # so that you get better error reports when performing test requests against the application.
    TESTING = True
    DEBUG = False

    # Disable CSRF tokens in the Forms (only valid for testing purposes!)
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    environ["PASSWORD_HASH_ROUNDS"] = "30000"

    TESTING = False
