from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, CookieTransport

from auth.config import auth_settings

SECRET = auth_settings.JWT_SECRET

cookie_transport = CookieTransport(cookie_name="stakewolle", cookie_max_age=100)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)