from typing import Optional

from fastapi_users import schemas
from fastapi_users.schemas import CreateUpdateDictModel, PYDANTIC_V2
from pydantic import ConfigDict, Field, EmailStr


class UserRead(CreateUpdateDictModel):
    """Base User model."""

    id: int
    email: EmailStr

    if PYDANTIC_V2:  # pragma: no cover
        model_config = ConfigDict(from_attributes=True)  # type: ignore
    else:  # pragma: no cover

        class Config:
            orm_mode = True


class UserCreate(CreateUpdateDictModel):
    email: EmailStr
    password: str
    referral_code: Optional[str] = Field(max_length=16, default=None)


class UserUpdate(schemas.BaseUserUpdate):
    pass
