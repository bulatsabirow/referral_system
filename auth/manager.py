import uuid
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, IntegerIDMixin, schemas, models, exceptions
from sqlalchemy import exists, select
from starlette import status

from .config import AuthSettings
from .db import get_user_db
from .models import User
from referral_program.models import ReferralCode


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = get_auth_settings().RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = get_auth_settings().VERIFICATION_TOKEN_SECRET

    async def validate_referral_code(self, referral_code: str) -> None:
        check_referral_code_existence = await self.user_db.check_referral_code_existence(referral_code)
        if not check_referral_code_existence.scalar():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code does not exist")

        check_referral_code_was_used = await self.user_db.check_referral_code_was_used(referral_code)
        if check_referral_code_was_used.scalar():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referral code was already used")
        
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

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )

        referral_code = user_dict.pop("referral_code", None)
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)

        if referral_code:
            await self.validate_referral_code(referral_code)
            referral_code_model = await self.user_db.get_referral_code(referral_code)
            user_dict["referrer_id"] = referral_code_model.referrer_id

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
