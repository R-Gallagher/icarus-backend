from flask import after_this_request, request
from flask_jwt_extended import (fresh_jwt_required, get_jwt_identity,
                                unset_jwt_cookies)
from flask_restful import Resource
from models.user import UserModel
from resources.strings import GENERIC_ERROR_HAS_OCCURRED

class UserIsLoggedInAs(Resource):
    """
    GET
    Used to get the email address of the current user, for display in the top
    right profile menu
    """
    @fresh_jwt_required
    def get(self):
        try:
            user = UserModel.find_by_uuid(get_jwt_identity())
        except:
            return {"message": "Invalid access credentials."}, 400
        return {"email": user.email, "name": user.name, "profile_picture": user.profile_picture_link,  "is_initial_setup_complete": user.is_initial_setup_complete}, 200


class UserIsAuthenticated(Resource):
    """
    GET
    Determine if user is authenticated based on JWT
    """
    @fresh_jwt_required
    def get(self):
        try:
            UserModel.find_by_uuid(get_jwt_identity())
        except:
            return {"message": "Invalid access credentials."}, 400

        return True, 200
