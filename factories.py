from typing import Optional

import aioredis
from faker import Faker
from pydantic import EmailStr, BaseModel, Field
from pytest_redis import factories as redis_factories

from core.config import settings

fake = Faker()


class TestUserWithoutReferralCode(BaseModel):
    email: EmailStr = Field(default_factory=fake.email)
    password: str = Field(default_factory=fake.password)


class TestUser(TestUserWithoutReferralCode):
    referral_code: Optional[str] = Field(default=None)
