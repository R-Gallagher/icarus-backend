from extensions import db
from geoalchemy2 import Geometry


class AddressModel(db.Model):
    """
    For relationships between users (one) and their office addresses (many)

    Methods:
    save_to_db
    delete_from_db
    """
    __tablename__ = 'addresses'

    id = db.Column(
        db.Integer, nullable=False, unique=True,
        primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('providers.user_id'))
    user = db.relationship("ProviderModel", back_populates="addresses")

    address = db.Column(db.String)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    geo = db.Column(Geometry(geometry_type="POINT")) # this should get SRID = 4326 added to it
    phone = db.Column(db.String)
    fax = db.Column(db.String)
    is_wheelchair_accessible = db.Column(db.Boolean)
    is_accepting_new_patients = db.Column(db.Boolean)
    start_hour = db.Column(db.Time)
    end_hour = db.Column(db.Time)

    def __init__(self,
                 address: str,
                 latitude: float,
                 longitude: float,
                 geo,
                 phone: str = None,
                 fax: str = None,
                 is_wheelchair_accessible: bool = None,
                 is_accepting_new_patients: bool = None,
                 start_hour=None,
                 end_hour=None):
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.geo = geo
        self.phone = phone
        self.fax = fax
        self.is_wheelchair_accessible = is_wheelchair_accessible
        self.is_accepting_new_patients = is_accepting_new_patients
        self.start_hour = start_hour
        self.end_hour = end_hour

    @classmethod
    def find_by_id(cls, id: int):
        return cls.query.filter_by(id=id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
