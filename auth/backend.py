from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, CookieTransport, Strategy, BearerTransport
from fastapi_users.types import DependencyCallable
from starlette.responses import Response

from auth.config import auth_settings
from auth.transport import RefreshCookieTransport


refresh_bearer_transport = RefreshCookieTransport(
    access_token_cookie_name="access_token",
    refresh_token_cookie_name="refresh_token",
    access_token_cookie_max_age=auth_settings.JWT_ACCESS_TOKEN_MAX_AGE,
    refresh_token_cookie_max_age=auth_settings.JWT_REFRESH_TOKEN_MAX_AGE,
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=auth_settings.JWT_SECRET, lifetime_seconds=auth_settings.JWT_ACCESS_TOKEN_MAX_AGE)


def get_refresh_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=auth_settings.JWT_SECRET, lifetime_seconds=auth_settings.JWT_REFRESH_TOKEN_MAX_AGE)


class AuthenticationRefreshJWTBackend(AuthenticationBackend):
    def __init__(self, get_refresh_strategy: DependencyCallable[Strategy[models.UP, models.ID]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_refresh_strategy = get_refresh_strategy

    async def login(self, strategy: Strategy[models.UP, models.ID], user: models.UP) -> Response:
        token = await strategy.write_token(user)
        refresh_strategy = self.get_refresh_strategy()
        refresh_token = await refresh_strategy.write_token(user)
        return await self.transport.get_login_response(token=token, refresh_token=refresh_token)


auth_backend = AuthenticationRefreshJWTBackend(
    name="jwt",
    transport=refresh_bearer_transport,
    get_strategy=get_jwt_strategy,
    get_refresh_strategy=get_refresh_jwt_strategy,
)
