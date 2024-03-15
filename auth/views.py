from typing import Annotated

from aioredis import Redis
from fastapi import APIRouter, Cookie, Depends, status, HTTPException
from fastapi_users import BaseUserManager
from fastapi_users.authentication import RedisStrategy, JWTStrategy

from auth import fastapi_users, get_user_manager
from auth.backend import (
    get_refresh_redis_strategy,
    refresh_cookie_transport,
    get_refresh_cookie_transport,
    get_jwt_strategy,
)
from auth.transport import RefreshCookieTransport

router = APIRouter(prefix="/auth", tags=["auth"])
get_current_user = fastapi_users.current_user()


@router.get("/refresh")
async def refresh_jwt(
    refresh_strategy: Annotated[RedisStrategy, Depends(get_refresh_redis_strategy)],
    strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
    refresh_token: Annotated[str, Cookie()],
    user_manager: Annotated[BaseUserManager, Depends(get_user_manager)],
    transport: Annotated[RefreshCookieTransport, Depends(get_refresh_cookie_transport)],
):
    user = await refresh_strategy.read_token(refresh_token, user_manager)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token." "Please, try to login again."
        )

    token = await strategy.write_token(user)
    new_refresh_token = await refresh_strategy.write_token(user)
    return await transport.get_login_response(token, new_refresh_token)
