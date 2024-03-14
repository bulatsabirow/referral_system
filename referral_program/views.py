import base64
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from auth import fastapi_users, User
from core.db import get_async_session
from referral_program.models import ReferralCode
from referral_program.schema import ReferralCodeCreate

router = APIRouter(prefix="/referral_code", tags=["referral_code"])
get_current_user = fastapi_users.current_user()


@router.post("/")
async def create_referral_code(referral_code_create: ReferralCodeCreate,
                               session: AsyncSession = Depends(get_async_session),
                               current_user=Depends(get_current_user)):
    print(type(current_user))
    # TODO consider another one condition
    query = select(ReferralCode).where(ReferralCode.referrer_id == current_user.id,
                                       ReferralCode.expired_at >= datetime.utcnow())
    result = await session.execute(exists(query).select())
    if result.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active referral code already exists")

    referral_code = ReferralCode(referrer_id=current_user.id,
                                 expired_at=referral_code_create.expired_at.replace(tzinfo=None),
                                 )

    session.add(referral_code)

    await session.commit()

    return referral_code


@router.get("/")
async def get_referral_code_by_email(email: str,
                                     session: AsyncSession = Depends(get_async_session)):
    encoded_email = email
    email: str = base64.urlsafe_b64decode(encoded_email).decode('utf-8')
    query = (select(ReferralCode).join(ReferralCode.referrer).options(contains_eager(ReferralCode.referrer)).
             where(User.email == email, ReferralCode.expired_at >= datetime.utcnow()))

    referral_code = await session.scalar(query)

    return {"referral_code": getattr(referral_code, "code", None)}
