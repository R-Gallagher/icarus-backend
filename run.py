from app import app, create_app_production
from config import ProductionConfig
from extensions import api
from api import add_resources
from jwt_add import add_jwt

add_resources(app, api)
add_jwt()

app = create_app_production(ProductionConfig)