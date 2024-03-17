from typing import Type

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from auth.backend import AuthenticationRefreshJWTBackend
from auth.backend import auth_backend
from auth.manager import get_user_manager
from auth.models import User
from auth.views import get_auth_router

try:
    from httpx_oauth.oauth2 import BaseOAuth2

    from fastapi_users.router import get_oauth_router
    from fastapi_users.router.oauth import get_oauth_associate_router
except ModuleNotFoundError:  # pragma: no cover
    BaseOAuth2 = Type  # type: ignore


class RefreshTokenFastAPIUsers(FastAPIUsers[User, int]):
    def get_auth_router(
        self, backend: AuthenticationRefreshJWTBackend, requires_verification: bool = False
    ) -> APIRouter:
        """
        Return an auth router for a given authentication backend.

        :param backend: The authentication backend instance.
        :param requires_verification: Whether the authentication
        require the user to be verified or not. Defaults to False.
        """
        return get_auth_router(
            backend,
            self.get_user_manager,
            self.authenticator,
            requires_verification,
        )


fastapi_users = RefreshTokenFastAPIUsers(
    get_user_manager,
    [auth_backend],
)

get_current_user = fastapi_users.current_user()
