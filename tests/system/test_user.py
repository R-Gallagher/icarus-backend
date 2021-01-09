from models.user import UserModel
from tests.base_test import BaseTest
import json


class UserTest(BaseTest):
    def test_register_user(self):
        with self.app() as client:
            with self.app_context():
                request = client.post(
                    '/register',
                    data=json.dumps({'name': 'Ryan Gallagher',
                                     'email': 'ryan@icarusmed.com',
                                     'password': '123'}),
                    content_type='application/json')
                user = UserModel.find_by_email('ryan@icarusmed.com')
                self.assertEqual(request.status_code, 201)
                self.assertIsNotNone(
                    UserModel.find_by_email('ryan@icarusmed.com'))
                self.assertDictEqual(
                    {"message": "Account created successfully, a confirmation email is on its way!",
                        "u": user.uuid, "first_login": True},
                    json.loads(request.data))

    def test_user_reject_admin_request(self): 
        """
        not quite sure how to test something this complex
        """
        pass