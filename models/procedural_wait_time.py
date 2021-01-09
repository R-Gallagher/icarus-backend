from extensions import db


class ProceduralWaitTimeModel(db.Model):
    """
    For relationships between users (one) and their office addresses (many)

    Methods:
    save_to_db
    delete_from_db
    """
    __tablename__ = 'procedural_wait_times'

    id = db.Column(
        db.Integer, nullable=False, unique=True,
        primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('providers.user_id'))
    user = db.relationship(
        "ProviderModel", back_populates="procedural_wait_times")

    procedure = db.Column(db.String)
    wait_time = db.Column(db.Float)

    def __init__(self,
                 procedure: str,
                 wait_time: int):
        self.procedure = procedure
        self.wait_time = wait_time

    @classmethod
    def find_by_id(cls, id: int):
        return cls.query.filter_by(id=id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
