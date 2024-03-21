import pytest
from fastapi import status
from fastapi_users.schemas import BaseUser
from httpx import AsyncClient, Response
from sqlalchemy import select

from auth.models import User
from conftest import DateTimeBetweenKwargs
from core.enums import ErrorDetails
from factories import TestUser
from referral_program.models import ReferralCode
from referral_program.services import generate_referral_code


class TestAuth:
    async def test_register_with_referral_code(
        self, auth_client: AsyncClient, get_test_async_session, referral_code: ReferralCode
    ):
        response = await auth_client.post(
            "/auth/register", json=TestUser(referral_code=referral_code.code).model_dump()
        )
        registered_user_id: int = response.json()["id"]

        assert response.status_code == status.HTTP_201_CREATED
        assert referral_code.referrer.id == await get_test_async_session.scalar(
            select(User.referrer_id).where(User.id == registered_user_id)
        )

    @pytest.mark.parametrize("referral_code", [DateTimeBetweenKwargs(start_date="-10d", end_date="-1d")], indirect=True)
    async def test_register_with_expired_referral_code(self, auth_client: AsyncClient, referral_code: ReferralCode):
        response = await auth_client.post(
            "/auth/register", json=TestUser(referral_code=referral_code.code).model_dump()
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == ErrorDetails.EXPIRED_REFERRAL_CODE

    async def test_register_with_used_referral_code(
        self, auth_client: AsyncClient, get_test_async_session, referral_code: ReferralCode
    ):
        first_response = await auth_client.post(
            "/auth/register", json=TestUser(referral_code=referral_code.code).model_dump()
        )
        second_response = await auth_client.post(
            "/auth/register", json=TestUser(referral_code=referral_code.code).model_dump()
        )

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert second_response.json()["detail"] == ErrorDetails.REFERRAL_CODE_ALREADY_USED

    async def test_register_with_non_existing_referral_code(self, auth_client: AsyncClient, get_test_async_session):
        response = await auth_client.post(
            "/auth/register", json=TestUser(referral_code=generate_referral_code()).model_dump()
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == ErrorDetails.REFERRAL_CODE_DOESNT_EXIST

    async def test_logout(self, auth_client: AsyncClient):
        response = await auth_client.post("/auth/logout")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.cookies.get("access_token") is None
        assert response.cookies.get("refresh_token") is None

    async def test_refresh_token(self, auth_client: AsyncClient, user: BaseUser):
        auth_client.cookies.pop("access_token", None)
        old_refresh_token = auth_client.cookies.get("refresh_token")
        response: Response = await auth_client.post("/auth/refresh")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.cookies.get("access_token") is not None
        assert response.cookies.get("refresh_token") != old_refresh_token
