from datetime import datetime, timedelta
from secrets import randbits
from threading import Thread
from uuid import uuid4

from extensions import redis_store
from flask import after_this_request, request
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                fresh_jwt_required, get_jwt_identity,
                                set_access_cookies, set_refresh_cookies)
from flask_restful import Resource
from marshmallow import ValidationError
from models.user import UserModel
from schemas.user.user_register import UserRegisterSchema
from security import encrypt_password
from resources.user.utils.send_users_emails import send_confirmation_email
from resources.user.utils.generate_verification_code import generate_verification_code
from resources.strings import GENERIC_ERROR_HAS_OCCURRED, REGISTER_ERROR_EMAIL_ALREADY_IN_USE

user_register_schema = UserRegisterSchema()


class UserRegister(Resource):
    """
    POST METHOD ONLY
    Takes in an email and a password and determines if the email is already in use. 
    If the email is not in use, the POST request succeeds and a user is stores in the database.
    """

    def post(self):
        try:
            request_json = request.get_json()
            request_data = user_register_schema.load(request_json)
        except ValidationError as err:
            return err.messages, 400

        if UserModel.find_by_email(request_data['email']):
            return {"message": REGISTER_ERROR_EMAIL_ALREADY_IN_USE}, 400

        name = request_data['name']
        email = request_data['email']
        password = encrypt_password(request_data['password'])
        uuid = str(uuid4())

        user = UserModel(name=name, email=email, password=password, uuid=uuid)

        verification_code = generate_verification_code(user_uuid=user.uuid)

        try:
            Thread(target=send_confirmation_email, args=(
                user.email, verification_code)).start()
        except:
            return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

        try:
            user.save_to_db()
        except:
            return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400

        access_token = create_access_token(identity=user.uuid, fresh=True)
        refresh_token = create_refresh_token(identity=user.uuid)

        @after_this_request
        def set_response_cookies(response):
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response

        return {"message": "Account created successfully, a confirmation email is on its way!", "u": user.uuid, "first_login": True}, 201


class RegistrationConfirmation(Resource):
    """
    POST
    A user inputs the confirmation code that was sent to their email. The JWT token of the user is checked, 
    their uuid is matched to the jwt, and then the confirmation code stored in the confirmations is checked 
    for the jwt and the confirmation code. If the confirmation codes match for a user, set confirmed to True
    and sets confirmed_on to the datetime in the users table.
    """
    @fresh_jwt_required
    def post(self, confirmation_code):
        current_user = UserModel.find_by_uuid(get_jwt_identity())

        user_uuid = current_user.uuid
        stored_code = redis_store.get(user_uuid).decode('utf-8')

        if stored_code is None:
            return {"message": "This confirmation code has expired. Please request a new code."}, 400

        if confirmation_code != stored_code:
            return {"message": "Confirmation code does not match."}, 400

        if current_user:
            if not current_user.is_confirmed:

                current_user.is_confirmed = True
                current_user.confirmed_on = datetime.utcnow()
                try:
                    current_user.save_to_db()
                except:
                    return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

                return {"message": "Confirmation successful!", "is_initial_setup_complete": current_user.is_initial_setup_complete}, 200
            else:
                return {"message": "You are already confirmed."}, 400
        else:
            return {"message": "This is not a valid request."}, 400

        return {"message": GENERIC_ERROR_HAS_OCCURRED}, 400


class RegistrationConfirmationResend(Resource):
    """
    POST
    Requires a fresh jwt token
    and resends a confirmation email to that user.
    """
    @fresh_jwt_required
    def get(self):

        user = UserModel.find_by_uuid(get_jwt_identity())

        if not user:
            return {"message": "You are not logged in."}, 401

        verification_code = generate_verification_code(user_uuid=user.uuid)

        try:
            Thread(target=send_confirmation_email, args=(
                user.email, verification_code)).start()
        except:
            return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

        return {"message": "A new confirmation email is on its way!"}, 200
