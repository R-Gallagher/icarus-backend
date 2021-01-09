from extensions import jwt
from flask import jsonify
from extensions import redis_store
from models.user import UserModel

def add_jwt():
    # This method will check if a token is blacklisted, and will be called automatically when blacklist is enabled
    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token['jti']
        entry = redis_store.get(jti)
        if entry is None:
            return False
        return True # Here we blacklist particular jwt_managers that have been created in the past.


    # The following callbacks are used for customizing jwt_manager response/error messages.
    # The original ones may not be in a very pretty format (opinionated)
    @jwt.expired_token_loader
    def expired_token_callback(expired_token):
        return jsonify({
            'message': 'The token has expired.',
            'error': 'token_expired',
            'status': 427
        }), 427


    @jwt.invalid_token_loader
    # we have to keep the error argument here, since it's passed in by the caller internally
    def invalid_token_callback(error): 
        return jsonify({
            'message': 'Signature verification failed.',
            'error': 'invalid_token',
            'status': 401
        }), 401


    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "description": "Request does not contain an access token.",
            'error': 'authorization_required',
            'status': 427
        }), 427


    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback():
        return jsonify({
            "description": "The token is not fresh.",
            'error': 'fresh_token_required',
            'status': 401
        }), 401


    @jwt.revoked_token_loader
    def revoked_token_callback():
        return jsonify({
            "description": "The token has been revoked.",
            'error': 'token_revoked',
            'status': 401
        }), 401
    
    return check_if_token_in_blacklist, expired_token_callback, invalid_token_callback, \
           missing_token_callback, token_not_fresh_callback, revoked_token_callback