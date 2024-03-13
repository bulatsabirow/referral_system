import uuid
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

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
