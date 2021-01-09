from marshmallow import Schema, fields

class SpecialtySchema(Schema):
    class Meta:

        # # things we might want to return, but dont want to input into the db
        # dump_only = ("id",)

        # includes foreign key relationships
        include_fk = True
    
    name = fields.Str(required=True)
    id = fields.Int()
