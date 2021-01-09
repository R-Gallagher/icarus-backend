from flask_restful import Resource
from flask_jwt_extended import fresh_jwt_required
from models.language import LanguageModel
from marshmallow import ValidationError
from schemas.language import LangaugeSchema

language_schema = LangaugeSchema()
language_list_schema = LangaugeSchema(many=True)


class LanguageList(Resource):
    @fresh_jwt_required
    def get(self):
        return {'languages': language_list_schema.dump(LanguageModel.find_all())}, 200