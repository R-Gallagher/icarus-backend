from flask_restful import Resource
from flask_jwt_extended import fresh_jwt_required
from models.designation import DesignationModel
from marshmallow import ValidationError
from schemas.designation import DesignationSchema

designation_schema = DesignationSchema()
designation_list_schema = DesignationSchema(many=True)


class DesignationList(Resource):
    @fresh_jwt_required
    def get(self):
        return {'designations': designation_list_schema.dump(DesignationModel.find_all())}, 200