from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.router.common import ErrorModel

from auth.db import get_user_db, SQLAlchemyUserDatabase
from auth.fastapi_users import get_current_user
from auth.schema import UserRead
from core.enums import ErrorDetails
from referral_program.db import get_referral_program_repository, ReferralProgramRepository
from referral_program.models import ReferralCode
from referral_program.schema import ReferralCodeCreate, ReferralCodeRead, GetReferralCodeQueryParams

router = APIRouter(prefix="/referral_code", tags=["referral_code"])


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
    repository: Annotated[ReferralProgramRepository, Depends(get_referral_program_repository)],
    current_user=Depends(get_current_user),
):
    if await repository.check_whether_active_referral_code_exists(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorDetails.ACTIVE_REFERRAL_CODE_ALREADY_EXISTS
        )

    referral_code = ReferralCode(
        referrer_id=current_user.id,
        expired_at=referral_code_create.expired_at.replace(tzinfo=None),
    )

    await repository.create_referral_code(referral_code)

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
    id: int,
    repository: Annotated[ReferralProgramRepository, Depends(get_referral_program_repository)],
    current_user=Depends(get_current_user),
):
    if not await repository.check_whether_referral_code_exists_by_id(user_id=current_user.id, id=id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorDetails.REFERRAL_CODE_NOT_FOUND)

    await repository.delete_referral_code_by_id(user_id=current_user.id, id=id)


@router.get("/", response_model=ReferralCodeRead)
async def get_referral_code_by_email(
    repository: Annotated[ReferralProgramRepository, Depends(get_referral_program_repository)],
    query_params: Annotated[GetReferralCodeQueryParams, Depends(GetReferralCodeQueryParams)],
):
    referral_code = await repository.fetch_referral_code_by_email(query_params.email)

    if not referral_code or await repository.check_whether_referral_code_was_used(referral_code):
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
async def get_referrals_by_referrer_id(id: int, user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)]):
    is_user_existing = await user_db.check_whether_user_exists(id)

    if not is_user_existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorDetails.USER_NOT_FOUND)

    referrals = await user_db.fetch_referrals(id)

    return referrals.all()
