from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core.models import Base


class ReferralCode(Base):
    __tablename__ = 'referral_code'
    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    code: Mapped[str] = mapped_column(String(length=16))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    expired_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    referrer = relationship("User", back_populates="referral_codes")
