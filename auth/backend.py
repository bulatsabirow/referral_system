from aioredis import Redis
from fastapi import Depends, status
from fastapi_users import models
from fastapi_users.authentication import (
    AuthenticationBackend,
    JWTStrategy,
    CookieTransport,
    Strategy,
    BearerTransport,
    RedisStrategy,
)
from fastapi_users.authentication.strategy import StrategyDestroyNotSupportedError
from fastapi_users.authentication.transport import TransportLogoutNotSupportedError
from fastapi_users.types import DependencyCallable
from starlette.responses import Response

from auth.config import auth_settings
from auth.strategy import RefreshRedisStrategy
from auth.transport import RefreshCookieTransport
from core.redis import get_redis

refresh_cookie_transport = RefreshCookieTransport(
    access_token_cookie_name="access_token",
    refresh_token_cookie_name="refresh_token",
    access_token_cookie_max_age=auth_settings.JWT_ACCESS_TOKEN_LIFETIME_SECONDS,
    refresh_token_cookie_max_age=auth_settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS,
)


def get_refresh_cookie_transport() -> RefreshCookieTransport:
    return refresh_cookie_transport


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=auth_settings.JWT_SECRET, lifetime_seconds=auth_settings.JWT_ACCESS_TOKEN_LIFETIME_SECONDS
    )


def get_refresh_redis_strategy() -> RedisStrategy:
    return RefreshRedisStrategy(
        key_prefix="", redis=get_redis(), lifetime_seconds=auth_settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS
    )


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
    transport=refresh_cookie_transport,
    get_strategy=get_jwt_strategy,
    get_refresh_strategy=get_refresh_redis_strategy,
)
