from flask_restful import Resource
from flask_jwt_extended import fresh_jwt_required
from models.specialty import SpecialtyModel
from marshmallow import ValidationError
from schemas.specialty import SpecialtySchema

specialty_schema = SpecialtySchema()
specialty_list_schema = SpecialtySchema(many=True)


class SpecialtyList(Resource):
    @fresh_jwt_required
    def get(self):
        return {'specialties': specialty_list_schema.dump(SpecialtyModel.find_all())}, 200