from os import environ
from passlib.context import CryptContext

password_hash_rounds = int(environ["PASSWORD_HASH_ROUNDS"])

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=password_hash_rounds
)

def encrypt_password(password):
    return pwd_context.encrypt(password)


def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)
