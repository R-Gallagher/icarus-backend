from datetime import datetime, timedelta

from blacklist import revoke_token
from flask import after_this_request, request
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                fresh_jwt_required, get_jwt_identity,
                                get_raw_jwt, jwt_refresh_token_required,
                                set_access_cookies, set_refresh_cookies,
                                unset_jwt_cookies)
from flask_restful import Resource
from flask_wtf.csrf import generate_csrf
from marshmallow import ValidationError
from models.user import UserModel
from schemas.user.user_auth import UserLoginSchema
from security import check_encrypted_password
from resources.strings import GENERIC_ERROR_HAS_OCCURRED

user_login_schema = UserLoginSchema()


class UserLogin(Resource):
    """
    POST
    Takes in an email and a password for authentication. The email is used to find the user in the database,
    and the password input is compared to the 
    """

    def post(self):
        try:
            data = user_login_schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        user = UserModel.find_by_email(data['email'])

        if not user:
            return {"message": "There is no account associated with that email"}, 401

        # Compare the encrypted password in the database to the data passed in from the user input
        # If passwords match, return an access token and a refresh token to the user
        if check_encrypted_password(data['password'], user.password):

            access_token = create_access_token(identity=user.uuid, fresh=True)
            refresh_token = create_refresh_token(identity=user.uuid)

            @after_this_request
            def set_response_cookies(response):
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response

            user.last_active = datetime.utcnow()
            user.save_to_db()
            return {
                        "message": "User Login successful!", 
                        "u": user.uuid, 
                        "user_type": user.user_type, 
                        "is_confirmed": user.is_confirmed, 
                        "is_initial_setup_complete": user.is_initial_setup_complete
                    }, 200

        return {"message": "Invalid Credentials!"}, 401


class UserLogout(Resource):
    """
    POST
    Logs a user out by taking their current JWT token and adding it to the blacklist. JWT is required.
    """
    # This definitely needs to change if we are doing a caching system of JWT Token Refresh, which is probably the
    # more secure and production-ready way of doing things. More research required.
    @fresh_jwt_required
    def post(self):
        # jti --> JWT unique identifier
        jti = get_raw_jwt()['jti']
        # revoke token based on its jti
        if jti:
            revoke_token(jti)
            @after_this_request
            def set_response_cookies(response):
                unset_jwt_cookies(response)
                return response

            return {"message": "Successfully logged out."}, 200
        return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400


class TokenRefresh(Resource):
    """
    POST
    Generates & issues a new fresh access token to a logged in user without an email and password, 
    all that is required is the a refresh token

    Requires a fresh JWT Token
    """
    @jwt_refresh_token_required
    def post(self):
        # Get the identity of the current user by their JWT, grant them a new access fresh access token.
        current_user = get_jwt_identity()
        if current_user:
            access_token = create_access_token(
                identity=current_user, fresh=True)
            refresh_token = create_refresh_token(identity=current_user.uuid)

            @after_this_request
            def set_response_cookies(response):
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response

            return {'message': "successful refresh"}, 200
        return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400


class UserCsrf(Resource):
    """
    GET
    CSRF token for access to all these lovely resources!
    """

    def get(self):
        xs = generate_csrf()
        return {'xs': xs}, 200
