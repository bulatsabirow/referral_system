from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.router.common import ErrorModel
from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from auth.models import User
from auth.fastapi_users import fastapi_users
from auth.schema import UserRead
from core.db import get_async_session
from core.enums import ErrorDetails
from referral_program.models import ReferralCode
from referral_program.schema import ReferralCodeCreate, ReferralCodeRead, GetReferralCodeQueryParams

router = APIRouter(prefix="/referral_code", tags=["referral_code"])
get_current_user = fastapi_users.current_user()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorDetails.ACTIVE_REFERRAL_CODE_ALREADY_EXISTS: {
                            "summary": ErrorDetails.ACTIVE_REFERRAL_CODE_ALREADY_EXISTS,
                            "value": {"detail": ErrorDetails.ACTIVE_REFERRAL_CODE_ALREADY_EXISTS},
                        },
                    }
                }
            },
        }
    },
)
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorDetails.ACTIVE_REFERRAL_CODE_ALREADY_EXISTS
        )

    referral_code = ReferralCode(
        referrer_id=current_user.id,
        expired_at=referral_code_create.expired_at.replace(tzinfo=None),
    )

    session.add(referral_code)

    await session.commit()

    return referral_code


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorDetails.REFERRAL_CODE_NOT_FOUND: {
                            "summary": ErrorDetails.REFERRAL_CODE_NOT_FOUND,
                            "value": {"detail": ErrorDetails.REFERRAL_CODE_NOT_FOUND},
                        },
                    }
                }
            },
        },
    },
)
async def delete_referral_code(
    id: int, session: AsyncSession = Depends(get_async_session), current_user=Depends(get_current_user)
):
    if not await session.scalar(
        exists(ReferralCode).where(ReferralCode.referrer_id == current_user.id, ReferralCode.id == id).select()
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorDetails.REFERRAL_CODE_NOT_FOUND)

    query = delete(ReferralCode).where(ReferralCode.referrer_id == current_user.id, ReferralCode.id == id)

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
        .order_by(ReferralCode.created_at.desc())
        .limit(1)
    )

    referral_code = await session.scalar(query)

    if not referral_code or await session.scalar(
        select(User).where(User.referrer_id == referral_code.id).exists().select()
    ):
        return ReferralCodeRead()

    return ReferralCodeRead(referral_code=referral_code.code, id=referral_code.id)


@router.get(
    "/referrals/{id}",
    dependencies=[Depends(get_current_user)],
    response_model=list[UserRead],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorDetails.USER_NOT_FOUND: {
                            "summary": ErrorDetails.USER_NOT_FOUND,
                            "value": {"detail": ErrorDetails.USER_NOT_FOUND},
                        },
                    }
                }
            },
        },
    },
)
async def get_referrals_by_referrer_id(id: int, session: AsyncSession = Depends(get_async_session)):
    is_user_existing = await session.scalar(exists(select(User).where(User.id == id)).select())

    if not is_user_existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorDetails.USER_NOT_FOUND)

    query = (
        select(User)
        .where(User.referrer_id.in_(select(ReferralCode.id).where(ReferralCode.referrer_id == id)))
        .order_by(User.id)
    )
    referrals = await session.scalars(query)

    return referrals.all()
