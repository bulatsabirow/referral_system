import base64
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from auth import fastapi_users, User
from auth.schema import UserRead
from core.db import get_async_session
from referral_program.models import ReferralCode
from referral_program.schema import ReferralCodeCreate, ReferralCodeRead, GetReferralCodeQueryParams

router = APIRouter(prefix="/referral_code", tags=["referral_code"])
get_current_user = fastapi_users.current_user()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_referral_code(
    referral_code_create: ReferralCodeCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    query = (
        select(ReferralCode)
        .join(User, ReferralCode.id == User.referrer_id, isouter=True)
        .where(
            ReferralCode.referrer_id == current_user.id, ReferralCode.expired_at >= datetime.utcnow(), User.id == None
        )
    )
    result = await session.execute(exists(query).select())
    if result.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active referral code already exists")

    referral_code = ReferralCode(
        referrer_id=current_user.id,
        expired_at=referral_code_create.expired_at.replace(tzinfo=None),
    )

    session.add(referral_code)

    await session.commit()

    return referral_code


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_referral_code(
    session: AsyncSession = Depends(get_async_session), current_user=Depends(get_current_user)
):
    query = delete(ReferralCode).where(
        ReferralCode.referrer_id == current_user.id, ReferralCode.expired_at >= datetime.utcnow()
    )

    await session.execute(query)
    await session.commit()


@router.get("/", response_model=ReferralCodeRead)
async def get_referral_code_by_email(
    query_params: GetReferralCodeQueryParams = Depends(GetReferralCodeQueryParams),
    session: AsyncSession = Depends(get_async_session),
):
    email = query_params.email
    query = (
        select(ReferralCode)
        .join(ReferralCode.referrer)
        .options(contains_eager(ReferralCode.referrer))
        .where(User.email == email, ReferralCode.expired_at >= datetime.utcnow())
    )

    referral_code = await session.scalar(query)

    if not referral_code or await session.scalar(
        select(User).where(User.referrer_id == referral_code.id).exists().select()
    ):
        return ReferralCodeRead(referral_code=None)

    print("referral_code", referral_code, referral_code.code)
    return ReferralCodeRead(referral_code=referral_code.code)


@router.get("/referrals/{id}", dependencies=[Depends(get_current_user)], response_model=list[UserRead])
async def get_referrals_by_referrer_id(id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.referrer_id.in_(select(ReferralCode.id).where(ReferralCode.referrer_id == id)))
    referrals = await session.scalars(query)

    return referrals.all()
