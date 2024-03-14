from typing import Optional

from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[int]):
    pass


class UserCreate(schemas.BaseUserCreate):
    referral_code: Optional[str] = Field(max_length=16, default=None)


class UserUpdate(schemas.BaseUserUpdate):
    pass