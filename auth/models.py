from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core.models import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    referral_codes = relationship("ReferralCode", back_populates="referrer")


class ReferralUser(Base):
    __tablename__ = "referral_user"
    __table_args__ = (
        CheckConstraint("referral_code_id != referral_id", name="check_referral_and_referrer_and_not_the_same_person"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    referral_code_id: Mapped[int] = mapped_column(ForeignKey("referral_code.id"), unique=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
