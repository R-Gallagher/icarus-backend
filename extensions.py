from os import environ

import redis

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

api = Api()
cors = CORS()
db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()
csrf = CSRFProtect()
redis_store = redis.from_url(environ.get('REDIS_URL'))
