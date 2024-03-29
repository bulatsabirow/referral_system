from typing import Optional

from fastapi_users import BaseUserManager, models, exceptions
from fastapi_users.authentication import RedisStrategy, JWTStrategy

from auth.config import auth_settings
from core.redis import redis
from core.utils import generate_random_string


class RefreshRedisStrategy(RedisStrategy):
    REFRESH_TOKEN_LENGTH: int = auth_settings.JWT_REFRESH_TOKEN_LENGTH

    def get_hset_name(self, token) -> str:
        return f"{self.key_prefix}{token}"

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[models.UP, models.ID]
    ) -> Optional[models.UP]:
        if token is None:
            return None
        user_id = await self.redis.hget(self.get_hset_name(token), "user_id")
        if user_id is None:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID):
            return

    async def write_token(self, user: models.UP) -> str:
        token = generate_random_string(length=self.REFRESH_TOKEN_LENGTH)
        await self.redis.hset(self.get_hset_name(token), mapping={"user_id": str(user.id)})
        await self.redis.expire(self.get_hset_name(token), self.lifetime_seconds)
        return token

    async def destroy_token(self, token: str, user: models.UP) -> None:
        await self.redis.expire(self.get_hset_name(token), 0)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=auth_settings.JWT_SECRET,
        lifetime_seconds=auth_settings.JWT_ACCESS_TOKEN_LIFETIME_SECONDS,
    )


def get_refresh_redis_strategy() -> RedisStrategy:
    return RefreshRedisStrategy(
        key_prefix="", redis=redis, lifetime_seconds=auth_settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS
    )
