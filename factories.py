from typing import Optional

from faker import Faker
from pydantic import EmailStr, BaseModel, Field

fake = Faker()


class TestUserWithoutReferralCode(BaseModel):
    email: EmailStr = Field(default_factory=fake.email)
    password: str = Field(default_factory=fake.password)


class TestUser(TestUserWithoutReferralCode):
    referral_code: Optional[str] = Field(default=None)
