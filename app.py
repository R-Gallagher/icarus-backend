from models.user import UserModel, ProviderModel, AdminModel
from models.specialty import SpecialtyModel
from models.provider_type import ProviderTypeModel
from models.language import LanguageModel
from models.designation import DesignationModel
from models.procedural_wait_time import ProceduralWaitTimeModel
from models.address import AddressModel
from flask import Flask
from extensions import cors, db, jwt, ma, csrf  # , tali
from flask_restful import Resource
from os import environ
from flask_migrate import Migrate

# instantiate up here to keep access to app open to other modules
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app, db)

# APPLICATION FACTORIES
# as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

def create_app_production(Configuration):

    # adds all the configuration parameters to the flask app
    app.config.from_object(Configuration)

    # calls the app factory function
    register_extensions_production(app)
    return app


def register_extensions_production(app):
    """Register Flask extensions."""

    from extensions import api
    api.init_app(app)
    cors.init_app(app, supports_credentials=True)
    # need this for true prod
    cors.init_app(
        app, 
        resources={
            r"/*": {"origins": "https://www.icarusmed.com"}
        }, 
        supports_credentials=True)

    jwt.init_app(app)
    csrf.init_app(app)

    return None


def create_app_test(Configuration):
    from api import add_resources
    from extensions import api, cors, jwt, ma, csrf
    from jwt_add import add_jwt
    from config import TestingConfig

    api.app = app
    add_resources(app, api)
    add_jwt()

    app.config.from_object(TestingConfig)
    register_extensions_test(app)
    return app


def register_extensions_test(app):
    cors.init_app(app, supports_credentials=True)
    jwt.init_app(app)
    csrf.init_app(app)

    return None


if environ.get('DEV_ENV') == 'testing':
    from config import TestingConfig
    create_app_test(TestingConfig)

