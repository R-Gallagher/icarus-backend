from marshmallow import Schema, fields

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user


class UserSettingsPasswordResetSchema(Schema):
    """
    Schema for user password resets from their profile settings

    Used to serialize data recieved from settings password resets:
    old_password, new_password
    """
    class Meta:
        load_only = ("old_password", "new_password",)

    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True)


class UserForgotPasswordRequestSchema(Schema):
    """
    Schema for user password resets when they have forgotten it

    Used to serialize data recieved from forgotten password resets:
    password
    """
    email = fields.Str(required=True)


class UserForgotPasswordResetSchema(Schema):
    """
    Schema for user password resets when they have forgotten it

    Used to serialize data recieved from forgotten password resets:
    password
    """
    class Meta:
        load_only = ("password",)

    password = fields.Str(required=True)
