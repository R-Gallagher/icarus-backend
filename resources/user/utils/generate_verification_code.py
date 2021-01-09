from secrets import randbits
from extensions import redis_store    

def generate_verification_code(user_uuid: str):
    """
    Takes in a users uuid
    Generates a cryptographically secure 24 bit code for user verification and adds that
    code to a redis store.
    Returns the verification code
    """

    # randbits is used to generate the verification code
    # because it is cryptographically secure, where random() is not
    # 24 bits will generate a 8 or 9 digit number
    # randbits returns bits, so we must cast to a str
    verification_code = str(randbits(24))
    
    try:
        # encode on the way in, redis auto encodes and it can get annoying
        redis_store.set(user_uuid, verification_code.encode('utf-8'), 86400)
    except:
        return {"message": "An error occurred. Please try again later."}

    return verification_code