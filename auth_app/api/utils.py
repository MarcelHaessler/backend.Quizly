def set_access_cookie(response, access_token):
    """Attaches the access token as an HttpOnly cookie."""
    response.set_cookie(
        'access_token',
        str(access_token),
        httponly=True,
        secure=False,
        samesite='Lax',
    )


def set_auth_cookies(response, refresh):
    """Attaches access and refresh token as HttpOnly cookies."""
    set_access_cookie(response, refresh.access_token)
    response.set_cookie(
        'refresh_token',
        str(refresh),
        httponly=True,
        secure=False,
        samesite='Lax',
    )


def delete_auth_cookies(response):
    """Removes both auth cookies from the client."""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


def build_user_payload(user):
    """Returns the public user fields used in the login response."""
    return {'id': user.id, 'username': user.username, 'email': user.email}
