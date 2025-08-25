from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from HTTP-only cookies
    """
    
    def authenticate(self, request):
        # First try the standard header authentication
        header_auth = super().authenticate(request)
        if header_auth:
            return header_auth
            
        # Then try cookie authentication
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        return (user, validated_token)

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        try:
            return AccessToken(raw_token)
        except TokenError as e:
            raise InvalidToken({
                'detail': 'Given token not valid',
                'messages': [str(e)],
            })