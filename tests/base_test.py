"""
BaseTest class

This class should be the parent class to each non-unit test.
It allows for instantiation of database dhynamically
and makes sure that it is a new, blank database each time.
"""

from unittest import TestCase
from extensions import db
from config import TestingConfig
from app import app

class BaseTest(TestCase):

	@classmethod
	def setUpClass(cls):
		with app.app_context():
			db.init_app(app)

	def setUp(self):
		with app.app_context():
			db.create_all()

		self.app = app.test_client
		self.app_context = app.app_context
	
	def tearDown(self):
		with app.app_context():
			db.session.remove()
			db.drop_all()
