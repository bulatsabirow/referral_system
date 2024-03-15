import secrets
from typing import Optional

from fastapi_users import BaseUserManager, models, exceptions
from fastapi_users.authentication import RedisStrategy


class RefreshRedisStrategy(RedisStrategy):
    def get_hset_name(self, token) -> str:
        return f"{self.key_prefix}{token}"

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[models.UP, models.ID]
    ) -> Optional[models.UP]:
        print("before token=", token)
        if token is None:
            return None
        print("token=", f"{self.key_prefix}{token}")
        user_id = await self.redis.hget(self.get_hset_name(token), "user_id")
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
        await self.redis.hset(self.get_hset_name(token), mapping={"user_id": str(user.id)})
        await self.redis.expire(self.get_hset_name(token), self.lifetime_seconds)
        return token

    async def destroy_token(self, token: str, user: models.UP) -> None:
        print("destroyed token =", token)
        await self.redis.expire(self.get_hset_name(token), 0)
