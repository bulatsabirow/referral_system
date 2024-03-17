from fastapi import status
from fastapi_users import models
from fastapi_users.authentication import (
    AuthenticationBackend,
    JWTStrategy,
    Strategy,
    RedisStrategy,
)
from fastapi_users.authentication.strategy import StrategyDestroyNotSupportedError
from fastapi_users.authentication.transport import TransportLogoutNotSupportedError
from fastapi_users.types import DependencyCallable
from starlette.responses import Response

from auth.config import auth_settings
from auth.strategy import RefreshRedisStrategy, get_jwt_strategy, get_refresh_redis_strategy
from auth.transport import RefreshCookieTransport, refresh_cookie_transport
from core.redis import redis


class AuthenticationRefreshJWTBackend(AuthenticationBackend):
    def __init__(self, get_refresh_strategy: DependencyCallable[Strategy[models.UP, models.ID]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_refresh_strategy = get_refresh_strategy

    async def login(self, strategy: Strategy[models.UP, models.ID], user: models.UP) -> Response:
        token = await strategy.write_token(user)
        refresh_strategy = self.get_refresh_strategy()
        refresh_token = await refresh_strategy.write_token(user)
        return await self.transport.get_login_response(token=token, refresh_token=refresh_token)

    async def logout(
        self, strategy: Strategy[models.UP, models.ID], user: models.UP, token: str, refresh_token: str
    ) -> Response:
        refresh_strategy = self.get_refresh_strategy()
        await refresh_strategy.destroy_token(refresh_token, user)
        try:
            await strategy.destroy_token(token, user)
        except StrategyDestroyNotSupportedError:
            pass

        try:
            response = await self.transport.get_logout_response()
        except TransportLogoutNotSupportedError:
            response = Response(status_code=status.HTTP_204_NO_CONTENT)

        return response


auth_backend = AuthenticationRefreshJWTBackend(
    name="jwt",
    transport=refresh_cookie_transport,
    get_strategy=get_jwt_strategy,
    get_refresh_strategy=get_refresh_redis_strategy,
)
