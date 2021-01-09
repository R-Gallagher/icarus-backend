from blacklist import revoke_token
from config import BaseConfig
from extensions import redis_store
from flask_jwt_extended import create_access_token, decode_token
from extensions import redis_store
from tests.base_test import BaseTest
from uuid import uuid4

class UserTest(BaseTest):
    def test_revoke_token(self):
        with self.app() as client:
            with self.app_context():
                
                access_token = create_access_token(identity='123-456-789', fresh=True)

                decoded_token = decode_token(access_token)

                jti = decoded_token["jti"]

                # token shouldnt be in the blacklist before calling revoke_toke 
                blacklisted_token = redis_store.get(jti)
                self.assertIsNone(blacklisted_token)

                revoke_token(jti)
                
                # token should be in the blacklist now 
                blacklisted_token = redis_store.get(jti)
                self.assertIsNotNone(blacklisted_token)


