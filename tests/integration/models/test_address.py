from datetime import datetime

from models.address import AddressModel
from tests.base_test import BaseTest


class AddressModelTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            address = "200 University Ave W, Waterloo, ON N2L 3G1"
            latitude = 43.4717512
            longitude = -80.5459129
            geo = "POINT({} {})".format(longitude, latitude)
            phone = "123456789"
            fax = "123456789"
            is_wheelchair_accessible = True
            is_accepting_new_patients = True
            start_hour = datetime.strptime(
                "08:00", '%H:%M').time()
            end_hour = datetime.strptime(
                "08:00", '%H:%M').time()

            address = AddressModel(address=address,
                                   latitude=latitude,
                                   longitude=longitude,
                                   geo=geo,
                                   phone=phone,
                                   fax=fax,
                                   is_wheelchair_accessible=is_wheelchair_accessible,
                                   is_accepting_new_patients=is_accepting_new_patients,
                                   start_hour=start_hour,
                                   end_hour=end_hour)

            self.assertIsNone(AddressModel.find_by_id(
                1), "Found a user with address '1' before save_to_db")

            address.save_to_db()

            self.assertIsNotNone(AddressModel.find_by_id(
                1), "Did not find a address with id '1' after save_to_db")
