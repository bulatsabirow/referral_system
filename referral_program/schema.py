from datetime import datetime, timedelta
from typing import Optional

from fastapi import Query
from pydantic import BaseModel, Field, field_validator, EmailStr


class ReferralCodeCreate(BaseModel):
    expired_at: datetime = Field(default_factory=lambda: (datetime.utcnow() + timedelta(days=7)).replace(tzinfo=None))

    @field_validator("expired_at")
    @classmethod
    def expiration_date_must_not_be_already_expired(cls, v):
        if v.replace(tzinfo=None) <= datetime.utcnow():
            raise ValueError("Expiration date must not be already expired")
        return v


class ReferralCodeRead(BaseModel):
    id: Optional[int] = None
    referral_code: Optional[str] = Field(max_length=16, default=None)


class GetReferralCodeQueryParams(BaseModel):
    email: EmailStr = Field(Query(description="email address", example="user@example.com"))
