from datetime import datetime

from extensions import db
from geoalchemy2 import Geometry
from models.address import AddressModel
from models.procedural_wait_time import ProceduralWaitTimeModel
from sqlalchemy import asc, func, text


class UserModel(db.Model):
    """
    The parent user model. All attributes shared between users are included here.

    Methods:
    save_to_db,
    delete_from_db,
    find_by_email,
    find_by_id,
    find_by_uuid,
    get_users_within_radius,
    """
    __tablename__ = 'users'

    id = db.Column(
        db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(
        db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    uuid = db.Column(db.String, unique=True, nullable=False)
    registered_on = db.Column(
        db.DateTime, default=datetime.utcnow(), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    is_initial_setup_complete = db.Column(
        db.Boolean, default=False, nullable=False)
    is_verified_professional = db.Column(
        db.Boolean, default=False, nullable=False)
    last_active = db.Column(
        db.DateTime, default=datetime.utcnow(), nullable=False)
    profile_picture_link = db.Column(db.String)

    # user_type: 0, 1, 2, 3
    # 0 -> they are a PUBLIC PROVIDER (FREE)
    # 1 -> they are a PUBLIC PROVIDER (PAID)
    # 2 -> they are a PRIVATE PROVIDER (PAID)
    # 3 -> they are an ADMIN (FREE)
    user_type = db.Column(db.Integer)

    # One to One relationships
    provider = db.relationship("ProviderModel", backref="users", uselist=False)
    admin = db.relationship("AdminModel", backref="users", uselist=False)

    def __init__(self,
                 name: str,
                 email: str,
                 password: str,
                 uuid: str,
                 registered_on=None,
                 is_confirmed: bool = None,
                 is_initial_setup_complete: bool = None,
                 is_verified_professional: bool = None,
                 last_active=None,
                 user_type: int = None,
                 profile_picture_link: str = None) -> object:
        """
        Require a name, email and password to init.
        UUID, registered_on, is_confirmed, is_verified_professional, last_active recieve defaults on init
        """
        self.name = name
        self.email = email
        self.password = password
        self.uuid = uuid
        self.registered_on = registered_on
        self.is_confirmed = is_confirmed
        self.is_initial_setup_complete = is_initial_setup_complete
        self.is_verified_professional = is_verified_professional
        self.last_active = last_active
        self.user_type = user_type
        self.profile_picture_link = profile_picture_link

    def update(self, update_dict: dict):
        """
        Updates attributes of the user model object.

        Takes in a dict of serialized user data.
        Returns the updated user model object.
        """
        for key, value in update_dict.items():
            if key != "addresses":
                setattr(self, key, value)

        return self

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_email(cls, email: str) -> object:
        """
        Returns a user object for a unique email
        """
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, id: int) -> object:
        """
        Returns a user object for a given user id (internal)
        """
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_uuid(cls, uuid: str) -> object:
        """
        Returns a user object for a given user uuid (external)
        """
        return cls.query.filter_by(uuid=uuid).first()

    @classmethod
    def find_by_list_of_emails(cls, emails: list) -> list:
        """
        Returns a user object for each match in the list of emails provided
        """
        return cls.query.filter(UserModel.email.in_(emails)).all()

    @classmethod
    def find_all_providers(cls, admin_id):
        """
        Returns a list of user objects for each Provider that a user is related to
        """

        matching_providers = db.engine.\
            execute('SELECT DISTINCT ON (users.id) * FROM users JOIN providers_to_admins ON users.id=providers_to_admins.provider_id WHERE providers_to_admins.admin_id={}'.
                    format(admin_id))

        return matching_providers

    @classmethod
    def find_all_admins(cls, provider_id):
        """
        Returns a list of user objects for each admin that a user is related to
        """

        matching_admins = db.engine.\
            execute('SELECT DISTINCT ON (users.id) * FROM users JOIN providers_to_admins ON users.id=providers_to_admins.admin_id WHERE providers_to_admins.provider_id={}'.
                    format(provider_id))

        return matching_admins


    def get_users_within_radius(
            self,
            searcher_id: int,
            specialty_id: int,
            radius: int,
            page: int,
            sort: str,
            u_geo: str = None,
            name: str = None,
            language_ids: list = None,
            designation_ids: list = None,
            is_wheelchair_accessible: bool = None,
            is_accepting_new_patients: bool = None) -> list:
        """
        Return all users of a certain specialty within a given radius (in meters) of this city.
        Sorting by the distance of a sphere is less accurate than a spheroid, but faster
        order by distance from lat long, before paginate       
        """
        # import down here to avoid circular imports?
        from models.language import LanguageModel
        from models.designation import DesignationModel


        # query to get addresses within distance (in meters)
        # and return only one result per user
        # addresses_query = db.session.\
        #     query(AddressModel).\
        #     filter(func.ST_Distance_Sphere(AddressModel.geo, u_geo) < radius).\
        #     distinct(AddressModel.user_id).\
        #     subquery()

        address_qualified_users = db.session.execute("""SELECT DISTINCT addresses.user_id 
                                                     FROM addresses WHERE ST_DWithin(addresses.geo, '{}', {});""".\
                                                        format(u_geo, radius))

        # these should be strings for raw sql query
        user_ids_matching = [str(row[0]) for row in address_qualified_users]
            

        # # im currently suspecting that its these joins that are messing this up massively
        # # cause the same person shouldnt be showing up twice for having two addresses
        # # based on the distinct on user_id above
        # # UNLESS its the joins that are royally messing things up
        # matching_users = db.session.\
        #     query(UserModel).\
        #     join(ProviderModel).\
        #     join(AddressModel).\
        #     filter(
        #         # regular search
        #         ProviderModel.specialty_id == specialty_id,
        #         UserModel.user_type == 0,
        #         UserModel.is_verified_professional == True,
        #         UserModel.id.in_(user_ids_matching)
        #     )

        
        if sort == "dist":
            matching_user_ids = db.session.execute("""SELECT DISTINCT ON (users.id) users.id AS users_id
                                        FROM users
                                        JOIN addresses ON users.id = addresses.user_id
                                        LEFT OUTER JOIN providers ON users.id = providers.user_id
                                        WHERE 
                                        providers.specialty_id = {}
                                            AND users.user_type = 0
                                            AND users.id IN ({})
                                        GROUP BY users.id, providers.user_id, addresses.id
                                        ORDER BY users.id, ST_Distance(addresses.geo, '{}');""".\
                                            format(specialty_id, ', '.join(user_ids_matching), u_geo))
        elif sort == "wait":
            matching_user_ids = db.session.execute("""SELECT users.id 
                                          FROM users 
                                          JOIN providers ON users.id = providers.user_id 
                                          WHERE providers.specialty_id = {} 
	                                      AND users.user_type = 0
                                          AND users.id IN ({}) 
                                          GROUP BY users.id, providers.user_id
                                          ORDER BY providers.consultation_wait;
                                          """.format(specialty_id, ', '.join(user_ids_matching)))


        # ints for orm query,
        # str for sort
        int_user_ids = []
        str_user_ids = []

        for count, row in enumerate(matching_user_ids):
            int_user_ids.append(row[0])
            str_user_ids.append("WHEN users.id = {} THEN {}".format(str(row[0]), str(count + 1)))
            # another possible way is
            # ORDER BY  id=1 DESC, id=3 DESC, id=2 DESC, id=4 DESC
            # str_user_ids.append("users.id = {} DESC,".format(str(row[0])))

        if str_user_ids:
            matching_users = db.session.query(UserModel).\
                                        join(ProviderModel).\
                                        filter(UserModel.id.in_(int_user_ids)).\
                                        order_by(text(""" CASE {} ELSE 0 END""".format(' '.join(str_user_ids))))
        else:
            matching_users = db.session.query(UserModel).\
                                        join(ProviderModel).\
                                        filter(UserModel.id.in_(int_user_ids))
        
        if name:
            # ilike for case insensitive matching on psql
            matching_users = matching_users.filter(
                UserModel.name.ilike('%{}%'.format(name)))

        if language_ids:
            matching_users = matching_users.filter(
                ProviderModel.languages.any(LanguageModel.id.in_(language_ids)))

        if designation_ids:
            matching_users = matching_users.filter(
                ProviderModel.designations.any(DesignationModel.id.in_(designation_ids)))

        if is_wheelchair_accessible:
            matching_users = matching_users.filter(ProviderModel.addresses.any(
                AddressModel.is_wheelchair_accessible == True))

        if is_accepting_new_patients:
            matching_users = matching_users.filter(ProviderModel.addresses.any(
                AddressModel.is_accepting_new_patients == True))

        matching_users = matching_users.paginate(page, 6, False)

        return matching_users


# An association table (many-to-many) for
# mapping care providers to the designations they have.
provider_to_designation_association_table = db.Table('providers_to_designations',
                                                     db.Column('provider_id', db.Integer, db.ForeignKey(
                                                         'providers.user_id')),
                                                     db.Column('designation_id', db.Integer, db.ForeignKey(
                                                         'designations.id')),
                                                     )

# An association table (many-to-many) for
# mapping care providers to the languages they speak.
provider_to_language_association_table = db.Table('providers_to_languages',
                                                  db.Column('provider_id', db.Integer, db.ForeignKey(
                                                      'providers.user_id')),
                                                  db.Column('language_id', db.Integer, db.ForeignKey(
                                                      'languages.id')),
                                                  )


def append_to_association_table(self, child_model_obj, parent_model_obj_with_attribute):
    parent_model_obj_with_attribute.append(child_model_obj)
    db.session.commit()


class ProviderModel(db.Model):
    """
    A child to UserModel, filled with attributes of care providers.

    Methods:
    save_to_db,
    delete_from_db
    """
    __tablename__ = 'providers'

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)

    # # ONE OF specialty_id or provider_type_id will be null
    provider_type_id = db.Column(
        db.Integer, db.ForeignKey('provider_types.id'))
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'))

    subspecialty_or_special_interests = db.Column(db.String)
    services_provided = db.Column(db.String)
    services_not_provided = db.Column(db.String)
    education_and_qualifications = db.Column(db.String)
    research_interests = db.Column(db.String)
    consultation_wait = db.Column(db.Float)
    referral_instructions = db.Column(db.String)
    # Love, TN

    # addresses is one to many
    # ie,
    # < ProviderModel 1 >.addresses --> [< AddressModel 1 >, < AddressModel 2 >] - (Serialize) ->
    # [
    #   {
    #       address: '200 University Ave W, ...',
    #       latitude: 78.32134,
    #       longitude: -34.42993,
    #       phone: '1233454433',
    #       fax: '12345678910',
    #       is_wheelchair_accessible: True,
    #       is_accepting_new_patients: True,
    #       start_hour: (08:15),
    #       end_hour: (16:15),
    #   },
    #   {...},
    #   ...
    # ]

    addresses = db.relationship(
        "AddressModel", back_populates='user', cascade="all, delete, delete-orphan")

    procedural_wait_times = db.relationship(
        "ProceduralWaitTimeModel", back_populates='user', cascade="all, delete, delete-orphan")

    # provider_type, specialty are many to one
    # ie,
    # < ProviderModel 1 >.specialty --> <Specialty 1>
    # < ProviderModel 2 >.specialty --> <Specialty 1> - (Serialize) ->
    # {
    #    id: 1,
    #    name: 'Adolescent Medicine',
    # }
    specialty = db.relationship('SpecialtyModel')
    provider_type = db.relationship('ProviderTypeModel')

    # designations, languages, admins are many to many
    # ie,
    # < ProviderModel 2 >.languages <--> provider_to_language_association_table <-->  <Languages 1>.id
    # Finding the languages of a provider would return:
    # [
    #   {
    #       id: 1,
    #       name: 'English',
    #   },
    #   {
    #       id: 2,
    #       name: 'French',
    #   },
    #  ...
    # ]
    designations = db.relationship('DesignationModel', secondary=provider_to_designation_association_table,
                                   backref=db.backref('providers', lazy='dynamic'), lazy='dynamic')

    languages = db.relationship('LanguageModel', secondary=provider_to_language_association_table,
                                backref=db.backref('providers', lazy='dynamic'), lazy='dynamic')

    # backpopulates the provider column on ProviderToAdminAssociation,
    # Is backpopulated by the provider column on ProviderToAdminAssociation
    admins = db.relationship(
        "ProviderToAdminAssociation", back_populates="provider")

    def __init__(self,
                 user_id,
                 provider_type_id=None,
                 specialty_id=None,
                 subspecialty_or_special_interests=None,
                 services_provided=None,
                 services_not_provided=None,
                 education_and_qualifications=None,
                 research_interests=None,
                 consultation_wait=None,
                 procedural_wait=None):
        self.user_id = user_id
        self.provider_type_id = provider_type_id
        self.specialty_id = specialty_id
        self.subspecialty_or_special_interests = subspecialty_or_special_interests
        self.services_provided = services_provided
        self.services_not_provided = services_not_provided
        self.education_and_qualifications = education_and_qualifications
        self.research_interests = research_interests
        self.consultation_wait = consultation_wait

    def update(self, provider_data: dict):
        """
        Updates attributes of the provider model object.

        Takes in a dict of serialized provider data.
        Returns the updated provider model object.
        """
        # import down here to avoid circular imports
        from models.designation import DesignationModel
        from models.language import LanguageModel
        from models.specialty import SpecialtyModel

        for key, value in provider_data.items():
            if key not in {"specialty", "languages", "designations", "addresses", "procedural_wait_times"}:
                setattr(self, key, value)

        if "specialty" in provider_data:
            specialty = provider_data["specialty"]
            specialty_id = specialty['id']

            self.specialty_id = specialty_id

        if "languages" in provider_data:
            languages = provider_data["languages"]

            existing_languages = self.languages

            # delete all existing languages because we are uploading a new list
            for language in existing_languages:
                # row will be deleted from the association table automatically
                self.languages.remove(language)

            for item in languages:
                language_obj = LanguageModel.find_by_id(item['id'])

                provider_model_obj_with_languages = self.languages

                append_to_association_table(self, child_model_obj=language_obj,
                                            parent_model_obj_with_attribute=provider_model_obj_with_languages)

        if "designations" in provider_data:
            designations = provider_data["designations"]

            existing_designations = self.designations

            # delete all existing designations because we are uploading a new list
            for designation in existing_designations:
                # row will be deleted from the association table automatically
                self.designations.remove(designation)

            for item in designations:

                designation_obj = DesignationModel.find_by_id(item['id'])

                provider_model_obj_with_designations = self.designations

                append_to_association_table(self, child_model_obj=designation_obj,
                                            parent_model_obj_with_attribute=provider_model_obj_with_designations)

        if "addresses" in provider_data:
            addresses = provider_data["addresses"]

            if addresses:
                address_model_list = []
                for place in addresses:
                    address_model = AddressModel(
                        address=place["address"],
                        latitude=place["latitude"],
                        longitude=place["longitude"],
                        geo=place["geo"],
                    )

                    if "start_hour" in place:
                        start_hour = place["start_hour"]
                        start_hour_dt = datetime.strptime(
                            start_hour, '%H:%M').time()
                        address_model.start_hour = start_hour_dt

                    if "end_hour" in place:
                        end_hour = place["end_hour"]
                        end_hour_dt = datetime.strptime(
                            end_hour, '%H:%M').time()
                        address_model.end_hour = end_hour_dt

                    if "is_wheelchair_accessible" in place:
                        is_wheelchair_accessible = place["is_wheelchair_accessible"]
                    else:
                        is_wheelchair_accessible = False

                    address_model.is_wheelchair_accessible = is_wheelchair_accessible

                    if "is_accepting_new_patients" in place:
                        is_accepting_new_patients = place["is_accepting_new_patients"]
                    else:
                        is_accepting_new_patients = False

                    address_model.is_accepting_new_patients = is_accepting_new_patients

                    if "fax" in place:
                        address_model.fax = place["fax"]

                    if "phone" in place:
                        address_model.phone = place["phone"]

                    address_model_list.append(address_model)

                # delete all previous addresses
                del self.addresses

                # add addresses from this request
                self.addresses = address_model_list

        if "procedural_wait_times" in provider_data:
            procedural_wait_times = provider_data["procedural_wait_times"]

            if procedural_wait_times:
                procedural_wait_times_model_list = []

                for procedural_wait_time in procedural_wait_times:
                    procedural_wait_time_model = ProceduralWaitTimeModel(
                        procedure=procedural_wait_time["procedure"],
                        wait_time=procedural_wait_time["wait_time"],
                    )

                    procedural_wait_times_model_list.append(
                        procedural_wait_time_model)

                # delete all previous procedural_wait_times
                del self.procedural_wait_times

                # add procedural_wait_times from this request
                self.procedural_wait_times = procedural_wait_times_model_list
                
            else:
                # if procedural_wait_times list is empty
                del self.procedural_wait_times

                self.procedural_wait_times = []

        return self

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, user_id: int) -> object:
        """
        Returns a ProviderModel object for a given user id (internal)
        """
        return cls.query.filter_by(user_id=user_id).first()


class AdminModel(db.Model):
    """
    A child to UserModel, filled with attributes of office administrators.

    Methods:
    save_to_db,
    delete_from_db
    """
    __tablename__ = 'admins'
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)

    # backpopulates the admin column on ProviderToAdminAssociation,
    # Is backpopulated by the admin column on ProviderToAdminAssociation
    providers = db.relationship(
        "ProviderToAdminAssociation", back_populates="admin")

    def __init__(self, user_id):
        self.user_id = user_id

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, user_id: int) -> object:
        """
        Returns an AdminModel object for a given user id (internal)
        """
        return cls.query.filter_by(user_id=user_id).first()


class ProviderToAdminAssociation(db.Model):
    """
    An association object model (many-to-many association WITH extra data)
    for mapping care providers to their administrators.

    Methods:
    save_to_db,
    delete_from_db
    """
    __tablename__ = 'providers_to_admins'
    provider_id = db.Column(db.Integer, db.ForeignKey(
        'providers.user_id'), primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey(
        'admins.user_id'), primary_key=True)
    is_relationship_confirmed_by_provider = db.Column(
        db.Boolean, nullable=False, default=False)

    # backpopulates the admins column on ProviderModel,
    # is backpopulated by the admins column on ProviderModel
    provider = db.relationship("ProviderModel", back_populates="admins")

    # backpopulates the providers column on AdminModel,
    # is backpopulated by the providers column on AdminModel
    admin = db.relationship("AdminModel", back_populates="providers")

    def __init__(self,
                 provider_id=None,
                 admin_id=None,
                 is_relationship_confirmed_by_provider=None):
        self.provider_id = provider_id
        self.admin_id = admin_id
        self.is_relationship_confirmed_by_provider = is_relationship_confirmed_by_provider

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def findRelationshipBasedOnAdminAndProvider(self, provider_id, admin_id):
        association = ProviderToAdminAssociation.query.filter(
            ProviderToAdminAssociation.provider_id == provider_id,
            ProviderToAdminAssociation.admin_id == admin_id,
        ).first()

        return association
