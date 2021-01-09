from marshmallow import Schema, fields, post_load
from werkzeug.datastructures import FileStorage
from schemas.address import AddressModelSchema
from schemas.procedural_wait_time import ProceduralWaitTimeModelSchema
from schemas.designation import DesignationSchema
from schemas.language import LangaugeSchema
from schemas.specialty import SpecialtySchema

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user


class ProviderModelSchema(Schema):
    """
    Schema for ProviderModel

    Used to deserialize all user facing fields in a ProviderModel object:
    user_type, subspecialty_or_special_interests, services_provided, 
    services_not_provided, education_and_qualifications, research_interests,
    consultation_wait
    """
    class Meta: 
        load_only = ("user_id",)

    addresses = fields.Nested(AddressModelSchema, many=True)
    procedural_wait_times = fields.Nested(ProceduralWaitTimeModelSchema, many=True)
    
    designations = fields.Nested(DesignationSchema, many=True)
    languages = fields.Nested(LangaugeSchema, many=True)

    # provider_type_id = fields.Integer()
    specialty = fields.Nested(SpecialtySchema)
    subspecialty_or_special_interests = fields.Str()
    services_provided = fields.Str()
    services_not_provided = fields.Str()
    education_and_qualifications = fields.Str()
    research_interests = fields.Str()
    consultation_wait = fields.Float(allow_none=True)
    referral_instructions = fields.Str()

class UserModelSchema(Schema):
    """
    Schema for UserModel

    Used to deserialize all user facing fields in a UserModel object.
    """
    class Meta:
        dump_only = ("id",)
        load_only = ("id", "password", "is_confirmed",
                        "registered_on", "last_active")
	
    name = fields.Str()
    email = fields.Str()
    uuid = fields.Str()
    user_type = fields.Int()
    profile_picture_link = fields.Str()
    is_initial_setup_complete = fields.Boolean()
    is_verified_professional = fields.Boolean()
    is_confirmed = fields.Boolean()
    provider = fields.Nested(ProviderModelSchema)


class AdminModelSchema(Schema):
    """
    Schema for AdminModel

    Used to de/serialize all providers that an administrator works for.
    """

    providers = fields.Nested(UserModelSchema, many=True)


class ProviderAdminModelSchema(Schema):
    """
    Schema for AdminModel

    Used to de/serialize all providers that an administrator works for.
    """
    name = fields.Str()
    email = fields.Str()
    uuid = fields.Str()
    profile_picture_link = fields.Str()
    is_relationship_confirmed_by_provider = fields.Boolean()


class FileStorageField(fields.Field):
    """
    Custom schema field definition for images

    Used to validate data recieved from profile picture uploads
    password
    """
    default_error_messages = {
        "invalid": "Not a valid image."
    }

    def _deserialize(self, value,  *args, **kwargs) -> FileStorage:
        if value is None:
            return None

        if not isinstance(value, FileStorage):
            self.fail("Invalid")  # raises ValidationError

        return value


class ImageSchema(Schema):
    """
    Schema for Image Uploads

    Used to serialize data recieved from profile picture uploads:
    image
    """
    image = FileStorageField(required=True)