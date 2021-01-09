from marshmallow import Schema, fields

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user

class UserRegisterSchema(Schema):
    """
    Schema for user registration

    Used to serialize data recieved on registration:
    name, email, password
    """
    class Meta:
        load_only = ("password",)

    name = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)