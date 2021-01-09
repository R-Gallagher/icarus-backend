from datetime import datetime
from json import dumps
from threading import Thread
from time import time
from uuid import uuid4
from os import environ

import boto3
from blacklist import revoke_token
from flask import after_this_request, jsonify, request
from flask_jwt_extended import (decode_token, fresh_jwt_required,
                                get_jwt_identity, unset_jwt_cookies)
from flask_restful import Resource
from marshmallow import ValidationError
from models.address import AddressModel
from models.designation import DesignationModel
from models.language import LanguageModel
from models.procedural_wait_time import ProceduralWaitTimeModel
from models.user import (AdminModel, ProviderModel, ProviderToAdminAssociation,
                         UserModel)
from resources.strings import GENERIC_ERROR_HAS_OCCURRED, PROFILE_UPDATED_SUCCESSFULLY
from resources.user.utils.send_users_emails import \
    send_admin_confirmation_email_to_providers
from schemas.user.user_profile import (AdminModelSchema, ImageSchema,
                                       ProviderAdminModelSchema,
                                       ProviderModelSchema, UserModelSchema)

# instantiate marshmallow schema
user_model_schema = UserModelSchema()
many_users_schema = UserModelSchema(many=True)
provider_model_schema = ProviderModelSchema()
admin_model_schema = AdminModelSchema()
provider_admin_model_schema = ProviderAdminModelSchema(many=True)
image_schema = ImageSchema()


class UserType(Resource):
    """
    GET, PUT

    GET: Returns the user type of an authenticated user based on input uuid
    PUT: Updates user type if json user_type is 0, 1, or 2 (based on their jti)
    """

    @fresh_jwt_required
    def get(self, user_uuid: str):
        user = UserModel.find_by_uuid(user_uuid)

        if user is None:
            return {"message": "User Not Found"}, 404

        return {"user_type": user.user_type}, 200

    @fresh_jwt_required
    def put(self, user_uuid: str):
        try:
            user_json = request.get_json()
            user_data = user_model_schema.load(user_json)
        except ValidationError as err:
            return err.messages, 400

        if user_data["user_type"] is None:
            return {"message": "No user type supplied"}, 400

        user_types = [0, 1, 2, 3]

        if user_data["user_type"] not in user_types:
            return {"message": "Invalid user type"}, 400

        user = UserModel.find_by_uuid(get_jwt_identity())

        # user types that belong to healthcare providers (refer to UserModel)
        health_provider_types = [0, 1, 2]

        if user_data["user_type"] in health_provider_types:
            # user has selected a health care provider account type
            provider = ProviderModel.find_by_id(user_id=user.id)

            if provider is None:
                # user has not been added as an admin yet
                # instantiate a new AdminModel and save them to it
                provider = ProviderModel(user.id)
                user.provider = provider
                try:
                    user.save_to_db()
                except:
                    return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

        else:
            # User has selected an administrative assistant account type
            admin = AdminModel.find_by_id(user_id=user.id)

            if admin is None:
                # user has not been added as an admin yet
                # instantiate a new AdminModel and save them to it
                admin = AdminModel(user_id=user.id)
                user.admin = admin
                user.is_initial_setup_complete = True

                try:
                    user.save_to_db()
                except:
                    return (
                        {
                            "message": GENERIC_ERROR_HAS_OCCURRED
                        },
                        500,
                    )

        try:
            user.update(update_dict=user_data).save_to_db()
        except:
            return (
                {
                    "message": GENERIC_ERROR_HAS_OCCURRED
                },
                500,
            )

        return (
            {"message": PROFILE_UPDATED_SUCCESSFULLY,
                "user_type": user.user_type},
            201,
        )


class UserProfile(Resource):
    """
    GET, PUT

    GET: takes in user_uuid and returns a user profile as defined in the UserModel class.
    PUT: updates UserModel for the user_uuid supplied.
    """

    @fresh_jwt_required
    def get(self, user_uuid: str):

        user = UserModel.find_by_uuid(user_uuid)

        if not user:
            return {"message": "User Not Found"}, 404

        return user_model_schema.dump(user), 200

    @fresh_jwt_required
    def put(self, user_uuid: str):
        try:
            user_json = request.get_json()
            user_data = user_model_schema.load(user_json)
        except ValidationError as err:
            return err.messages, 400

        user = UserModel.find_by_uuid(user_uuid)

        requestor = UserModel.find_by_uuid(get_jwt_identity())

        # is the uuid they've passed in match their profile uuid?
        if user.uuid != requestor.uuid:
            # if it hasnt, their jwt identity must match one of the
            # administrator jwts for the passed in user_uuid

            # first, check if the requestor is actually an admin user type
            if requestor.user_type != 3:
                return {"message": "You must have an administrator account type to edit someone elses profile"}, 401

            admin = requestor

            provider_to_admin = ProviderToAdminAssociation()

            can_they_edit = provider_to_admin.findRelationshipBasedOnAdminAndProvider(
                provider_id=user.id, admin_id=admin.id)

            if not can_they_edit:
                return {"message": "You do not have permission to edit this profile."}, 401

            if not can_they_edit.is_relationship_confirmed_by_provider:
                return {"message": "You must be verified by the provider before you can edit their account."}, 401

        provider = ProviderModel.find_by_id(user_id=user.id)

        # this is shitty but the update by dict is killing us with error messages right now
        if "provider" in user_data:
            provider_data = user_data["provider"]

            provider = provider.update(provider_data=provider_data)

            if not user.is_initial_setup_complete:
                # if addresses is an empty list, setup has not been completed!
                if provider.addresses:
                    user.is_initial_setup_complete = True

            try:
                user.provider = provider
                user.save_to_db()
            except:
                return {"message": GENERIC_ERROR_HAS_OCCURRED, "profile": user_model_schema.dump(user)}, 500

        return {"message": PROFILE_UPDATED_SUCCESSFULLY, "profile": user_model_schema.dump(user)}, 201


class UserProfilePicture(Resource):
    """
    POST
    Used to upload a users profile image file.
    Use a JWT to retrieve user info and then save that image to an aws s3 bucket.
    """

    @fresh_jwt_required
    def post(self, user_uuid: str):
        data = image_schema.load(request.files)  # {"image": FileStorage}
        image = data["image"]
        bucket = environ.get("S3_BUCKET")

        user = UserModel.find_by_uuid(user_uuid)

        requestor = UserModel.find_by_uuid(get_jwt_identity())

        # is the uuid they've passed in match their profile uuid?
        if user.uuid != requestor.uuid:
            # if it hasnt, their jwt identity must match one of the
            # administrator jwts for the passed in user_uuid

            # first, check if the requestor is actually an admin user type
            if requestor.user_type != 3:
                return {"message": "You must have an administrator account type to edit someone elses profile"}, 401

            admin = requestor

            provider_to_admin = ProviderToAdminAssociation()

            can_they_edit = provider_to_admin.findRelationshipBasedOnAdminAndProvider(
                provider_id=user.id, admin_id=admin.id)

            if not can_they_edit:
                return {"message": "You do not have permission to edit this profile."}, 401

            if not can_they_edit.is_relationship_confirmed_by_provider:
                return {"message": "You must be verified by the provider before you can edit their account."}, 401

        filename = "{}-profile-picture.jpg".format(str(uuid4()))

        # upload file to s3 bucket
        s3 = boto3.resource("s3")
        s3.meta.client.upload_fileobj(image, bucket, filename)

        # save link to db
        link = "https://{}.s3.amazonaws.com/{}".format(bucket, filename)
        # need to delete old photo eventually

        try:
            user.profile_picture_link = link
            user.save_to_db()
        except:
            return (
                {
                    "message": GENERIC_ERROR_HAS_OCCURRED,
                    "profile_picture_link": user.profile_picture_link,
                },
                500,
            )

        return (
            {
                "message": PROFILE_UPDATED_SUCCESSFULLY,
                "profile_picture_link": link,
            },
            201,
        )


class AdminManagedProfile(Resource):
    """
    GET, PUT

    IF user type of requestor is admin (3)
    GET: Return a list of all providers that are related to the currently authenticated administrator
    PUT: Invites a provider to be managed by the currently authenticated administrator.
         The administrator must provide the email address(es) of the provider they are requesting.
         Emails will be sent to matching provider emails with acceptance JWTs.
         If the email addresses provided do NOT match anyone in the DB, return the not matching list.

    IF user type of requestor is provider (3)
    GET: Return a list of all admins that are related to the currently authenticated user
    PUT: TO DO - Invite admin to be an administrator for authenticated providers account
    """

    @fresh_jwt_required
    def get(self, user_uuid: str):

        user = UserModel.find_by_uuid(user_uuid)

        if not user:
            return {"message": "User Not Found"}, 404

        # if signed in as admin
        if user.user_type == 3:
            # get a list of all providers that are related to the current admin
            providers_list = user.find_all_providers(admin_id=user.id)

            return {"managed_providers": provider_admin_model_schema.dump(providers_list)}, 200

        else:
            # get a list of all admins that are related to the current provider
            admins_list = user.find_all_admins(provider_id=user.id)

            return {"managed_providers": provider_admin_model_schema.dump(admins_list)}, 200

    @fresh_jwt_required
    def put(self, user_uuid: str):
        try:
            user_json = request.get_json()
            user_data = admin_model_schema.load(user_json)
        except ValidationError as err:
            return err.messages, 400

        admin = UserModel.find_by_uuid(get_jwt_identity())

        if not admin.user_type == 3:
            return {"message": "Only administrator account types can access this \
                                functionality for now."}, 400

        validated_user_data = admin_model_schema.dump(user_data)

        # because we need to validate the input using marshmallow,
        # the data comes in like:
        # [
        #   {
        #       "email": "email1@example.com"
        #   },
        #   {
        #       "email": "email2@example.com"
        #   }
        # ]
        # therefore we must pull all of these emails into a list of JUST emails,
        # not a list of dicts
        # Why was this decision made?
        #   Because we can choose to either de/serialize things in a weird way with marshmallow,
        #   and then get our nice list of emails out of the box
        #   OR we could choose to do the standard de/serialization with marshmallow,
        #   and create the list once the data is validated. This seemed like the least bad
        #   choice to me

        recieved_email_list = []
        emails = validated_user_data["providers"]

        for email in emails:
            recieved_email_list.append(email["email"])

        # out of the list of emails, we need to figure out which ones are in our database as users
        # find which emails from the emails list exist in our db
        matching_users = UserModel.find_by_list_of_emails(
            emails=recieved_email_list)

        # generate a list of JUST emails that matched (as strings for comparison)
        matching_user_email_strings = [
            matched.email for matched in matching_users]
        
        # generate a list of emails that werent matched
        # ie, they came in from user provider list, but we couldnt match the email to a db record
        not_matching_emails = list(
            set(recieved_email_list) - set(matching_user_email_strings))

        # get a list of all providers that are related to the current admin
        db_providers_list = admin.find_all_providers(admin_id=admin.id)

        # START ERROR HANDLING
        
        # FOR NON-MATCHING PROVIDERS (Provider doesn't exist) OR Admins
        # For now,
        # Return an error if ANY emails dont match

        # Eventually,
        # Explain that they must be a user of the site before they can be
        # added as a managed provider
        # Send them an invite link. Allow success for any matching (instead of failing the whole list)

        if not_matching_emails:
            return {"message": "You have requested to be the administrative assistant \
                                of the following people even though they are not registered \
                                as providers on Icarus: {}. Please try again once these providers \
                                have registered.".format(", ".join(not_matching_emails)),
                    "managed_providers": provider_admin_model_schema.dump(db_providers_list)}, 400


        # generate a list of any admins who are trying to be clever and add another admin
        illegally_requested_admins = []
        for user in matching_users:
            if user.user_type == 3:
                illegally_requested_admins.append(user.email)

        if illegally_requested_admins:
            return {"message": "You have requested to be the administrative assistant \
                                of the following people even though they are registered as \
                                administrator account types: {}. You cannot be the administrator \
                                of an administrator account.".format(", ".join(illegally_requested_admins)),
                                "managed_providers": provider_admin_model_schema.dump(db_providers_list)}, 400


        # generate a list of any providers that aren't verified
        unverified_matching_users = []
        for user in matching_users:
            if not user.is_verified_professional:
                unverified_matching_users.append(user.email)

        if unverified_matching_users:
            return {"message": "You have requested to be the administrative assistant \
                                of the following people even though they are not verified \
                                as providers on Icarus: {}. Please try again once these providers \
                                are verified.".format(", ".join(unverified_matching_users)),
                                "managed_providers": provider_admin_model_schema.dump(db_providers_list)}, 400


        # END ERROR HANDLING

        # FOR MATCHING PROVIDERS
        # Add them to the association table,
        # Send each provider that matches a confirmation link

        # add each matching provider to the association table
        for matched_provider in matching_users:
            map_association = ProviderToAdminAssociation(
                provider_id=matched_provider.id,
                admin_id=admin.id,
                is_relationship_confirmed_by_provider=False,
            )

            map_association.save_to_db()

        # if matching users have made it this far, they are matching providers
        # ie, we know they are providers
        matching_providers = matching_users
        
        # this needs to update after association table has been changed
        db_providers_list = admin.find_all_providers(admin_id=admin.id)

        # send an admin invitation to each provider
        if matching_providers:
            try:
                Thread(
                    target=send_admin_confirmation_email_to_providers,
                    kwargs=dict(providers=matching_providers, admin=admin),
                ).start()
            except:
                return {"message": GENERIC_ERROR_HAS_OCCURRED}, 500

        return (
            {
                "message": PROFILE_UPDATED_SUCCESSFULLY,
                "received_providers": dumps(recieved_email_list),
                "matching_providers": many_users_schema.dump(matching_providers),
                "not_matching_emails": not_matching_emails,
                "managed_providers": provider_admin_model_schema.dump(db_providers_list)
            },
            201,
        )


class UserAcceptAdminRequest(Resource):
    """
    POST
    After a user has recieved an admin request reset link via email, they click a link.
    That link brings them to a /user/accept_admin_request/{jwt} page on the front end.
    They confirm, then fire a request to this resource where we:
    check the jwt they pass us. If it is right, we update their many to many to show verified.
    """

    def post(self, accept_token, admin_uuid):
        try:
            decoded_token = decode_token(accept_token)
        except:
            return {"message": "This token is invalid."}, 400

        provider = UserModel.find_by_uuid(decoded_token["identity"])
        admin = UserModel.find_by_uuid(admin_uuid)

        provider_id = provider.id
        admin_id = admin.id

        AssociationObject = ProviderToAdminAssociation()

        relationship = AssociationObject.\
            findRelationshipBasedOnAdminAndProvider(
                provider_id=provider_id, admin_id=admin_id)

        relationship.is_relationship_confirmed_by_provider = True
        admin.is_verified_professional = True

        try:
            relationship.save_to_db()
            admin.save_to_db()
        except:
            # get a list of all admins that are related to the current provider
            admins_list = provider.find_all_admins(provider_id=provider.id)
            
            return {"message": GENERIC_ERROR_HAS_OCCURRED, 
                    "managed_providers": provider_admin_model_schema.dump(admins_list)}, 400

        return {"message": PROFILE_UPDATED_SUCCESSFULLY}, 201


class UserRejectAdminRequest(Resource):
    """
    POST
    After a user has recieved an admin request reset link via email, they click a link.
    That link brings them to a /user/accept_admin_request/{jwt} page on the front end.
    They reject, then fire a request to this resource where we:
    invalidate the jwt passed to us and destroy the relationship between the admin
    and the provider in the database,
    """

    def post(self, accept_token, admin_uuid):
        try:
            decoded_token = decode_token(accept_token)
        except:
            return {"message": "This token is invalid."}, 400

        jti = decoded_token["jti"]

        if jti:
            revoke_token(jti)

        admin = UserModel.find_by_uuid(admin_uuid)
        provider = UserModel.find_by_uuid(decoded_token["identity"])

        provider_id = provider.id
        admin_id = admin.id

        AssociationObject = ProviderToAdminAssociation()

        relationship = AssociationObject.\
            findRelationshipBasedOnAdminAndProvider(
                provider_id=provider_id, admin_id=admin_id)

        try:
            relationship.delete_from_db()
        except:
            # get a list of all admins that are related to the current provider
            admins_list = provider.find_all_admins(provider_id=provider.id)
            
            return {"message": GENERIC_ERROR_HAS_OCCURRED, 
                    "managed_providers": provider_admin_model_schema.dump(admins_list)}, 400

        return {"message": "Request has been rejected succcessfully!"}, 201


class UserAcceptAdminRelationship(Resource):
    """
    POST
    After a user (provider) has recieved an admin request.
    They have not acted on the request using the email link.
    The user should be able to accept the relationship with that admin.
    """
    @fresh_jwt_required
    def post(self, admin_uuid):

        admin = UserModel.find_by_uuid(admin_uuid)
        provider = UserModel.find_by_uuid(get_jwt_identity())

        provider_id = provider.id
        admin_id = admin.id

        AssociationObject = ProviderToAdminAssociation()

        relationship = AssociationObject.\
            findRelationshipBasedOnAdminAndProvider(
                provider_id=provider_id, admin_id=admin_id)

        relationship.is_relationship_confirmed_by_provider = True
        admin.is_verified_professional = True

        try:
            relationship.save_to_db()
            admin.save_to_db()
        except:
            # get a list of all admins that are related to the current provider
            admins_list = provider.find_all_admins(provider_id=provider.id)
            
            return {"message": GENERIC_ERROR_HAS_OCCURRED, 
                    "managed_providers": provider_admin_model_schema.dump(admins_list)}, 400

        # get a list of all admins that are related to the current provider
        admins_list = provider.find_all_admins(provider_id=provider.id)

        return {"message": PROFILE_UPDATED_SUCCESSFULLY, 
                "managed_providers": provider_admin_model_schema.dump(admins_list)}, 201


class UserDeleteAdminRelationship(Resource):
    """
    POST
    After a user (provider) has recieved an admin request.
    They have already accepted it.
    The user should be able to delete the relationship with that admin.
    """
    @fresh_jwt_required
    def post(self, admin_uuid):

        admin = UserModel.find_by_uuid(admin_uuid)
        provider = UserModel.find_by_uuid(get_jwt_identity())

        provider_id = provider.id
        admin_id = admin.id

        AssociationObject = ProviderToAdminAssociation()

        relationship = AssociationObject.\
            findRelationshipBasedOnAdminAndProvider(
                provider_id=provider_id, admin_id=admin_id)

        try:
            relationship.delete_from_db()
        except:
            # get a list of all admins that are related to the current provider
            admins_list = provider.find_all_admins(provider_id=provider.id)

            return {"message": GENERIC_ERROR_HAS_OCCURRED, 
                    "managed_providers": provider_admin_model_schema.dump(admins_list)}, 400

        # get a list of all admins that are related to the current provider
        admins_list = provider.find_all_admins(provider_id=provider.id)

        return {"message": PROFILE_UPDATED_SUCCESSFULLY, 
                "managed_providers": provider_admin_model_schema.dump(admins_list)}, 201