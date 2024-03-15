import secrets
from typing import Optional
import redis.asyncio

from fastapi_users import BaseUserManager, models, exceptions
from fastapi_users.authentication import RedisStrategy


class RefreshRedisStrategy(RedisStrategy):
    # TODO write f"{self.key_prefix}{token}" as function
    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[models.UP, models.ID]
    ) -> Optional[models.UP]:
        print("before token=", token)
        if token is None:
            return None
        print("token=", f"{self.key_prefix}{token}")
        user_id = await self.redis.hget(f"{self.key_prefix}{token}", "user_id")
        if user_id is None:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            print(f"{parsed_id=}")
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID):
            return

    async def write_token(self, user: models.UP) -> str:
        token = secrets.token_urlsafe(48)
        await self.redis.hset(f"{self.key_prefix}{token}", mapping={"user_id": str(user.id)})
        await self.redis.expire(f"{self.key_prefix}{token}", self.lifetime_seconds)
        return token

    async def destroy_token(self, token: str, user: models.UP) -> None:
        await self.redis.expire(f"{self.key_prefix}{token}", 0)
