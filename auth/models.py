from typing import Optional

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core.models import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("referral_code.id"), default=None)

    referral_codes = relationship("ReferralCode", back_populates="referrer",
                                  primaryjoin="User.id == ReferralCode.referrer_id")

