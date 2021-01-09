from extensions import db
from models.user import ProviderModel


class SpecialtyModel(db.Model):
    __tablename__ = 'specialties'
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    name = db.Column(db.String, unique=True)

    # list of user models
    users = db.relationship('ProviderModel', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    @classmethod
    def find_by_id(cls, id: int):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_all(cls):
        return cls.query.filter().order_by(SpecialtyModel.name)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
