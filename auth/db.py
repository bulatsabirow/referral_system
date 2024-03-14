from datetime import datetime

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase as SQLAlchemyBaseUserDatabase
from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from core.db import get_async_session
from referral_program.models import ReferralCode


class ReferralCodeMixin:
    async def check_referral_code_existence(self, code):
        exists_query = exists(select(ReferralCode).where(ReferralCode.code == code))
        return await self.session.execute(select(exists_query))

    async def check_referral_code_was_used(self, code):
        check_used_query = exists(select(ReferralCode).join(User,
                                                            and_(ReferralCode.referrer_id == User.referrer_id,
                                                                 ReferralCode.code == code)))
        return await self.session.execute(select(check_used_query))

    async def get_referral_code(self, code: str):
        select_referral_code_query = select(ReferralCode).where(ReferralCode.code == code)
        referral_code = await self.session.scalar(select_referral_code_query)

        return referral_code


class SQLAlchemyUserDatabase(ReferralCodeMixin, SQLAlchemyBaseUserDatabase):
    pass


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
