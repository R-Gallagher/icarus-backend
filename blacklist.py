from config import BaseConfig
from extensions import redis_store

def revoke_token(jti):
    redis_store.set(jti, 'true', BaseConfig.JWT_ACCESS_TOKEN_EXPIRES * 1.2)