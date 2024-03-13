import secrets
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator


class ReferralCodeCreate(BaseModel):
    expired_at: datetime = Field(default_factory=lambda: (datetime.utcnow() + timedelta(days=7)).replace(tzinfo=None))

    @field_validator("expired_at")
    @classmethod
    def expiration_date_must_not_be_already_expired(cls, v):
        if v.replace(tzinfo=None) <= datetime.utcnow():
            raise ValueError("Expiration date must not be already expired")
        return v

