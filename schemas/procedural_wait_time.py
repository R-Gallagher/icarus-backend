from marshmallow import Schema, fields

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user

class ProceduralWaitTimeModelSchema(Schema):
    """
    Schema for UserModel

    Used to deserialize all user facing fields in a UserModel object.
    """
    class Meta:
        dump_only = ("id", "user_id")
        load_only = ("id", "user_id")
    
    procedure = fields.Str()
    wait_time = fields.Float()