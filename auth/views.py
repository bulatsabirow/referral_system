from typing import Annotated
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import models
from fastapi_users.authentication import Authenticator, Strategy
from fastapi_users.authentication import RedisStrategy, JWTStrategy
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.router.common import ErrorCode, ErrorModel

from auth.backend import (
    get_refresh_redis_strategy,
    get_refresh_cookie_transport,
    get_jwt_strategy,
    AuthenticationRefreshJWTBackend,
)
from auth.manager import get_user_manager
from auth.transport import RefreshCookieTransport
from core.enums import ErrorDetails


def get_auth_router(
    backend: AuthenticationRefreshJWTBackend,
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    authenticator: Authenticator,
    requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with login/logout routes for an authentication backend."""
    router = APIRouter()
    get_current_user_token = authenticator.current_user_token(active=True, verified=requires_verification)

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value": {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
        request: Request,
        credentials: OAuth2PasswordRequestForm = Depends(),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
        strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user = await user_manager.authenticate(credentials)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        response = await backend.login(strategy, user)
        await user_manager.on_after_login(user, request, response)
        return response

    logout_responses: OpenAPIResponseType = {
        **{status.HTTP_401_UNAUTHORIZED: {"description": "Missing token or inactive user."}},
        **backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post("/logout", name=f"auth:{backend.name}.logout", responses=logout_responses)
    async def logout(
        user_token: Tuple[models.UP, str] = Depends(get_current_user_token),
        refresh_token=Cookie(),
        strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user, token = user_token
        return await backend.logout(strategy, user, token, refresh_token)

    @router.post(
        "/refresh",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            ErrorDetails.INVALID_REFRESH_TOKEN: {
                                "summary": ErrorDetails.INVALID_REFRESH_TOKEN,
                                "value": {"detail": ErrorDetails.INVALID_REFRESH_TOKEN},
                            },
                        }
                    }
                },
            }
        },
    )
    async def refresh_jwt(
        refresh_strategy: Annotated[RedisStrategy, Depends(get_refresh_redis_strategy)],
        strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
        refresh_token: Annotated[str, Cookie()],
        user_manager: Annotated[BaseUserManager, Depends(get_user_manager)],
        transport: Annotated[RefreshCookieTransport, Depends(get_refresh_cookie_transport)],
    ):
        user = await refresh_strategy.read_token(refresh_token, user_manager)

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorDetails.INVALID_REFRESH_TOKEN)

        token = await strategy.write_token(user)
        await refresh_strategy.destroy_token(refresh_token, user)
        new_refresh_token = await refresh_strategy.write_token(user)
        return await transport.get_login_response(token, new_refresh_token)

    return router
