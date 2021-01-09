from marshmallow import Schema, fields

# In Meta classes below
# dump_only: things we might want to return, but dont want to input into the db
# load_only: things we don't want to return to user

class AddressModelSchema(Schema):
    """
    Schema for UserModel

    Used to deserialize all user facing fields in a UserModel object.
    """
    class Meta:
        dump_only = ("id", "user_id")
        load_only = ("id", "user_id", "geo")
    
    address = fields.Str()
    latitude = fields.Float()
    longitude = fields.Float()
    geo = fields.Str()
    phone = fields.Str()
    fax = fields.Str()
    is_wheelchair_accessible = fields.Boolean()
    is_accepting_new_patients = fields.Boolean()
    start_hour = fields.Str()
    end_hour = fields.Str()