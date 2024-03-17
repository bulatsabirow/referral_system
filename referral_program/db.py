from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from auth.models import User
from core.db import get_async_session
from referral_program.models import ReferralCode


class ReferralProgramRepository:
    def __init__(self, session):
        self.session: AsyncSession = session

    async def check_whether_active_referral_code_exists(self, user_id: int):
        query = (
            select(ReferralCode)
            .join(User, ReferralCode.id == User.referrer_id, isouter=True)
            .where(ReferralCode.referrer_id == user_id, ReferralCode.expired_at >= datetime.utcnow(), User.id == None)
        )
        query_result = await self.session.execute(exists(query).select())

        return query_result.scalar()

    async def create_referral_code(self, referral_code):
        self.session.add(referral_code)

        await self.session.commit()

    async def check_whether_referral_code_exists_by_id(self, user_id: int, id: int):
        query = exists(ReferralCode).where(ReferralCode.referrer_id == user_id, ReferralCode.id == id).select()

        return await self.session.scalar(query)

    async def delete_referral_code_by_id(self, user_id: int, id: int):
        query = delete(ReferralCode).where(ReferralCode.referrer_id == user_id, ReferralCode.id == id)

        await self.session.execute(query)
        await self.session.commit()

    async def fetch_referral_code_by_email(self, email) -> Optional[ReferralCode]:
        query = (
            select(ReferralCode)
            .join(ReferralCode.referrer)
            .options(contains_eager(ReferralCode.referrer))
            .where(User.email == email, ReferralCode.expired_at >= datetime.utcnow())
            .order_by(ReferralCode.created_at.desc())
            .limit(1)
        )

        return await self.session.scalar(query)

    async def check_whether_referral_code_was_used(self, referral_code: ReferralCode) -> bool:
        return await self.session.scalar(select(User).where(User.referrer_id == referral_code.id).exists().select())


def get_referral_program_repository(session: Annotated[AsyncSession, Depends(get_async_session)]):
    return ReferralProgramRepository(session)
