from os import environ
from resources.designation import DesignationList
from resources.specialty import SpecialtyList
from resources.language import LanguageList
from resources.user.user_auth import (TokenRefresh, UserCsrf, UserLogin,
                                      UserLogout)
from resources.user.user_is import (UserIsAuthenticated, UserIsLoggedInAs)
from resources.user.user_password import (UserForgotPasswordRequest,
                                          UserForgotPasswordUpdate,
                                          UserPasswordResetSettings)
from resources.user.user_profile import (AdminManagedProfile,
                                         UserProfile, UserProfilePicture,
                                         UserType, UserAcceptAdminRequest,
                                         UserRejectAdminRequest,
                                         UserAcceptAdminRelationship, 
                                         UserDeleteAdminRelationship)
from resources.user.user_register import (RegistrationConfirmation,
                                          RegistrationConfirmationResend,
                                          UserRegister)
from resources.user.user_search import UserSearch

def add_resources(app, api):

    api.add_resource(UserCsrf, '/csrf')

    api.add_resource(UserIsAuthenticated, '/verifyAuth')

    api.add_resource(UserIsLoggedInAs, '/loggedInAs')

    api.add_resource(UserRegister, '/register')

    api.add_resource(RegistrationConfirmation,
                     '/confirm/<string:confirmation_code>')

    api.add_resource(RegistrationConfirmationResend, '/confirm/resend')

    api.add_resource(UserLogin, '/login')

    api.add_resource(UserLogout, '/logout')

    api.add_resource(TokenRefresh, '/refresh')

    api.add_resource(UserProfile, '/users/<string:user_uuid>/profile')

    api.add_resource(AdminManagedProfile, '/users/<string:user_uuid>/profile/admin')

    api.add_resource(UserType, '/users/<string:user_uuid>/user_type')

    api.add_resource(UserProfilePicture,
                     '/users/<string:user_uuid>/profile_pic')

    api.add_resource(UserPasswordResetSettings,
                     '/users/settings/password_reset')

    api.add_resource(UserForgotPasswordUpdate,
                     '/users/forgot_password/update/<string:token>')

    api.add_resource(UserForgotPasswordRequest,
                     '/users/forgot_password/request')

    api.add_resource(UserAcceptAdminRequest,
                     '/users/accept_admin_request/<string:accept_token>/<string:admin_uuid>')

    api.add_resource(UserRejectAdminRequest,
                     '/users/reject_admin_request/<string:accept_token>/<string:admin_uuid>')

    api.add_resource(UserAcceptAdminRelationship, '/users/accept_admin_relationship/<string:admin_uuid>')

    api.add_resource(UserDeleteAdminRelationship, '/users/delete_admin_relationship/<string:admin_uuid>')

    api.add_resource(
        UserSearch, '/users/<int:specialty_id>&<int:radius>&<int:page>&<string:sort_by>')

    api.add_resource(DesignationList, '/designations')

    api.add_resource(SpecialtyList, '/specialties')

    api.add_resource(LanguageList, '/languages')

    return api
