from datetime import timedelta
from threading import Thread
from time import time

from flask import after_this_request, request
from flask_jwt_extended import (create_access_token, fresh_jwt_required,
                                get_jwt_identity, decode_token)
from flask_restful import Resource
from marshmallow import ValidationError
from models.user import UserModel
from resources.user.utils.send_users_emails import send_password_reset_email
from schemas.user.user_password import (UserForgotPasswordRequestSchema,
                                        UserForgotPasswordResetSchema,
                                        UserSettingsPasswordResetSchema)
from security import check_encrypted_password, encrypt_password
from blacklist import revoke_token
from resources.strings import GENERIC_ERROR_HAS_OCCURRED

user_forgot_password_request_schema = UserForgotPasswordRequestSchema()
user_reset_password_schema = UserSettingsPasswordResetSchema()
user_forgot_password_schema = UserForgotPasswordResetSchema()

class UserPasswordResetSettings(Resource):
    @fresh_jwt_required
    def post(self):
        try:
            data = user_reset_password_schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        user = UserModel.find_by_uuid(get_jwt_identity())

        # Compare the encrypted password in the database to the data passed in from the user input
        # If passwords match, return an access token and a refresh token to the user
        if check_encrypted_password(data['old_password'], user.password):
            password = encrypt_password(data['new_password'])
            user.password = password
            try:
                user.save_to_db()
            except:
                return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400
        else:
            return {"message": "The old password you supplied does not match our records. Please try again."}, 400

        return {"message": "Password update successful!"}, 200


class UserForgotPasswordUpdate(Resource):
    """
    POST
    After a user has recieved their password reset link via email, they click a link.
    That link brings them to a /reset_password page on the front end.
    They confirm their new password, then fire a request to this resource where we:
    check that they pass us. If it is right, we update their password in the database.
    """

    def post(self, token):
        try:
            data = user_forgot_password_schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        try:
            decoded_token = decode_token(token)
        except:
            return {"message": "This reset token is invalid."}, 400

        # if the time (now) is less than the time of expiry
        # the token is still valid
        # else, the token is invalid and they must request a new one
        now = time()
        expiry = decoded_token['exp']

        if expiry < now:
            return {"message": "This link has expired. Please request a new password reset"}, 400

        revoke_token(decoded_token['jti'])

        user = UserModel.find_by_uuid(decoded_token['identity'])

        if user:
            password = encrypt_password(data['password'])
            user.password = password
            try:
                user.save_to_db()
            except:
                return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

            return {"message": "Password reset successful!"}, 200
        else:
            return {"message": "This is not a valid request."}, 400

        return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400


class UserForgotPasswordRequest(Resource):
    """
    # POST
    The user requests a password reset for an email
    If that email belongs to a user, we send a reset email
    with a JWT that expires in a day. If clicked, they are taken to a link
    Where they would post new password to UserForgotPasswordUpdate (above)
    """

    def post(self):
        try:
            data = user_forgot_password_request_schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        user = UserModel.find_by_email(data['email'])

        if user:
            try:
                reset_token = create_access_token(
                    identity=user.uuid, fresh=True, expires_delta=timedelta(hours=24))
                
                Thread(target=send_password_reset_email,
                        args=(user.email, reset_token)).start()
            except:
                return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500
        else:
            return {"message": "There is no account associated with that email"}, 400

        return {"message": "A password reset email is on its way!"}, 200
