from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CustomJWTAuthentication(JWTAuthentication):
    """ Custom JWT authentication that checks if a user is blocked """

    def authenticate(self, request):
        """ Override authentication to check if the user is blocked """
        user_auth_tuple = super().authenticate(request)

        if user_auth_tuple is None:
            return None  # No authentication provided, continue as normal

        user, token = user_auth_tuple

        if user.is_blocked:
            raise AuthenticationFailed("Your account has been blocked. Please contact support.")

        return user, token 
