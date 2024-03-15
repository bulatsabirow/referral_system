from typing import Optional

from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, IntegerIDMixin, schemas, models, exceptions
from starlette import status

from core.enums import ErrorDetails
from .config import auth_settings
from .db import get_user_db
from .models import User


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = auth_settings.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = auth_settings.VERIFICATION_TOKEN_SECRET

    async def validate_referral_code(self, referral_code: str) -> None:
        check_referral_code_existence = await self.user_db.check_referral_code_existence(referral_code)
        if not check_referral_code_existence.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorDetails.REFERRAL_CODE_DOESNT_EXISTS
            )

        check_referral_code_was_used = await self.user_db.check_referral_code_was_used(referral_code)
        if check_referral_code_was_used.scalar():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorDetails.REFERRAL_CODE_ALREADY_USED)

    async def create(
        self,
        user_create: schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = user_create.create_update_dict() if safe else user_create.create_update_dict_superuser()

        referral_code = user_dict.pop("referral_code", None)
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)

        if referral_code:
            await self.validate_referral_code(referral_code)
            referral_code_model = await self.user_db.get_referral_code(referral_code)
            user_dict["referrer_id"] = referral_code_model.id

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
