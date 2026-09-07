def set_auth_cookies(response, refresh):
    """Attaches access and refresh token as HttpOnly cookies."""
    response.set_cookie(
        'access_token',
        str(refresh.access_token),
        httponly=True,
        secure=False,
        samesite='Lax',
    )
    response.set_cookie(
        'refresh_token',
        str(refresh),
        httponly=True,
        secure=False,
        samesite='Lax',
    )