from marshmallow import Schema, fields

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user


class UserLoginSchema(Schema):
    """
    Schema for user login

    Used to serialize data recieved on login:
    email, password
    """
    class Meta:
        load_only = ("password",)

    email = fields.Str(required=True)
    password = fields.Str(required=True)

