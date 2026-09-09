from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegistrationSerializer
from .utils import (
    build_login_payload,
    delete_auth_cookies,
    set_access_cookie,
    set_auth_cookies,
)

LOGOUT_DETAIL = (
    'Log-Out successfully! All Tokens will be deleted. '
    'Refresh token is now invalid.'
)
INVALID_CREDENTIALS = {'detail': 'Invalid credentials.'}
INVALID_REFRESH = {'detail': 'Refresh token invalid or missing.'}


class RegistrationView(APIView):
    """Creates a new user account from username, email and password."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Creates the account or reports what was wrong with the input."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {'detail': 'User created successfully!'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Validates credentials and returns JWT cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Sets both auth cookies; wrong credentials give a generic 401."""
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password'),
        )
        if user is None:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
        response = Response(build_login_payload(user))
        set_auth_cookies(response, RefreshToken.for_user(user))
        return response


class LogoutView(APIView):
    """Blacklists the refresh token and clears the auth cookies."""

    def post(self, request):
        """Blacklists the refresh token so it cannot be used again."""
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(INVALID_REFRESH, status=status.HTTP_401_UNAUTHORIZED)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(INVALID_REFRESH, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({'detail': LOGOUT_DETAIL})
        delete_auth_cookies(response)
        return response


class TokenRefreshView(APIView):
    """Issues a new access token from the refresh token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Issues a new access token; a missing cookie is refused."""
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(INVALID_REFRESH, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response(INVALID_REFRESH, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({'detail': 'Token refreshed'})
        set_access_cookie(response, refresh.access_token)
        return response
