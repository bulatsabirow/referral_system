from typing import Callable
from urllib.parse import quote

import pytest
from fastapi_users.schemas import BaseUser
from httpx import Response
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from conftest import DateTimeBetweenKwargs
from referral_program.models import ReferralCode


class TestReferralCode:
    async def test_create_referral_code(self, auth_client: AsyncClient, get_test_async_session: AsyncSession):
        response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})

        assert response.status_code == status.HTTP_201_CREATED
        assert await get_test_async_session.scalar(func.count(ReferralCode.id)) == 1

    async def test_create_referral_code_twice(self, auth_client: AsyncClient):
        first_response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})
        second_response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_referral_code(self, auth_client: AsyncClient, referral_code: ReferralCode):
        response: Response = await auth_client.delete(f"/referral_code/{referral_code.id}", follow_redirects=True)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_non_existing_referral_code(self, auth_client: AsyncClient, referral_code: ReferralCode):
        first_response: Response = await auth_client.delete(f"/referral_code/{referral_code.id}", follow_redirects=True)
        second_response: Response = await auth_client.delete(
            f"/referral_code/{referral_code.id}", follow_redirects=True
        )

        assert second_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_referral_code_by_email(self, auth_client: AsyncClient, referral_code: ReferralCode):
        print(f"{referral_code.referrer=}")
        response: Response = await auth_client.get(
            "/referral_code", params={"email": quote(referral_code.referrer.email)}, follow_redirects=True
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["referral_code"] == referral_code.code
        assert response.json()["id"] == referral_code.id

    @pytest.mark.parametrize("referral_code", [DateTimeBetweenKwargs(start_date="-10d", end_date="-1d")], indirect=True)
    async def test_get_invalid_referral_code_by_email(self, auth_client: AsyncClient, referral_code: ReferralCode):
        response: Response = await auth_client.get(
            "/referral_code", params={"email": quote(referral_code.referrer.email)}, follow_redirects=True
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["referral_code"] is None
        assert response.json()["id"] is None

    async def test_get_referrals_by_referrer_id(
        self, auth_client: AsyncClient, get_referral_user: Callable, referral_code: ReferralCode
    ):
        user: BaseUser = await get_referral_user(referral_code.code)
        response: Response = await auth_client.get(f"/referral_code/referrals/{referral_code.referrer.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["id"] == user.id
        assert response.json()[0]["email"] == user.email

    async def test_get_referrals_non_existing_user(self, auth_client: AsyncClient, referral_code: ReferralCode):
        response: Response = await auth_client.get(f"/referral_code/referrals/{referral_code.referrer.id + 1}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
