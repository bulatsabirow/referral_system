import contextlib
from datetime import datetime
from typing import TypedDict, Union

from fastapi import FastAPI


class DateTimeBetweenKwargs(TypedDict):
    start_date: Union[datetime, str]
    end_date: Union[datetime, str]


class TokenCookies(TypedDict):
    access_token: str
    refresh_token: str


def async_partial(f, *args):
    async def f2(*args2):
        return await f(*args, *args2)

    return f2


@contextlib.contextmanager
def dependencies_overrider(app: FastAPI, dependencies):
    app.dependency_overrides.update(dependencies)
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
