from models.user import UserModel, ProviderModel
from schemas.user.user_profile import  ProviderModelSchema
from models.specialty import SpecialtyModel
from tests.base_test import BaseTest
from uuid import uuid4

provider_model_schema = ProviderModelSchema()

class UserTest(BaseTest):

	def test_user_register(self):
		name = 'Testing Tester'
		email = 'test@icarusmed.com'
		password = '123'
		uuid = str(uuid4())

		user = UserModel(name=name, email=email, password=password, uuid=uuid)

		self.assertEqual(user.name, name)
		self.assertEqual(user.email, email)
		self.assertEqual(user.password, password)
		self.assertEqual(user.uuid, uuid)

	def test_user_profile_update(self):
		name = 'Testing Tester'
		email = 'test@icarusmed.com'
		password = '123'
		uuid = str(uuid4())

		user = UserModel(name=name, email=email, password=password, uuid=uuid)

		provider = ProviderModel(user.id)
		user.provider = provider

		provider_input = {
			"specialty": {"id": 1, "name": "Adolescent Medicine"}
		}

		provider_data = provider_model_schema.load(provider_input)
		self.assertEqual(provider_data['specialty']['id'], 1)

		provider.update(provider_data=provider_data)

		# self.assertEqual(user.specialty, SpecialtyModel.find_by_id(1))
		self.assertEqual(provider.specialty_id, 1)

