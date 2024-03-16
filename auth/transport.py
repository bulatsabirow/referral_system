import datetime

from fastapi_users.authentication import Transport, BearerTransport, CookieTransport
from pydantic import BaseModel
from starlette.responses import Response, JSONResponse
from fastapi import status


class RefreshCookieTransport(CookieTransport):
    def __init__(
        self,
        access_token_cookie_name: str,
        refresh_token_cookie_name: str,
        access_token_cookie_max_age: int,
        refresh_token_cookie_max_age: int,
        *args,
        **kwargs,
    ):
        kwargs["cookie_name"] = access_token_cookie_name
        kwargs["cookie_max_age"] = access_token_cookie_max_age
        super().__init__(*args, **kwargs)

        self.refresh_token_cookie_name = refresh_token_cookie_name
        self.refresh_cookie_max_age = refresh_token_cookie_max_age

    async def get_login_response(self, token: str, refresh_token: str) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        return await self._set_login_cookie(response, token, refresh_token)

    async def _set_login_cookie(self, response: Response, token: str, refresh_token: str) -> Response:
        response.set_cookie(
            self.cookie_name,
            token,
            max_age=self.cookie_max_age,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        response.set_cookie(
            self.refresh_token_cookie_name,
            refresh_token,
            max_age=self.refresh_cookie_max_age,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        return response

    def _set_logout_cookie(self, response: Response) -> Response:
        response.set_cookie(
            self.cookie_name,
            "",
            max_age=0,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        response.set_cookie(
            self.refresh_token_cookie_name,
            "",
            max_age=0,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        return response
