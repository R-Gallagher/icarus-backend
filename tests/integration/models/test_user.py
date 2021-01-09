from models.user import UserModel
from uuid import uuid4
from tests.base_test import BaseTest

class UserModelTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            name = 'Testing Tester'
            email = 'test@icarusmed.com'
            password = '123'
            uuid = str(uuid4())

            user = UserModel(name=name, email=email, password=password, uuid=uuid)

            self.assertIsNone(UserModel.find_by_email(email), "Found a user with email 'test@icarusmed.com' before save_to_db")
            self.assertIsNone(UserModel.find_by_id(1), "Found a user with id '1' before save_to_db")
            self.assertIsNone(UserModel.find_by_uuid(uuid), "Found a user with uuid {} before save_to_db".format(uuid))

            user.save_to_db()

            self.assertIsNotNone(UserModel.find_by_email(email), "Did not find a user with email 'test@icarusmed.com' after save_to_db")
            self.assertIsNotNone(UserModel.find_by_id(1), "Did not find a user with id '1' after save_to_db")
            self.assertIsNotNone(UserModel.find_by_uuid(uuid), "Did not find a user with uuid {} after save_to_db".format(uuid))