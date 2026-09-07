from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegistrationSerializer
from .utils import (
    build_user_payload,
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
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password'),
        )
        if user is None:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        response = Response({
            'detail': 'Login successfully!',
            'user': build_user_payload(user),
        })
        set_auth_cookies(response, refresh)
        return response


class LogoutView(APIView):
    """Blacklists the refresh token and clears the auth cookies."""

    def post(self, request):
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
