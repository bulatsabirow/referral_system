from urllib import response

import pytest
from httpx import Response
from httpx import AsyncClient
from starlette import status


class TestReferralCode:
    async def test_create_referral_code(self, auth_client):
        response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})

        assert response.status_code == status.HTTP_201_CREATED

    async def test_create_referral_code_twice(self, auth_client):
        first_response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})
        second_response: Response = await auth_client.post("/referral_code", follow_redirects=True, json={})

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
