import asyncio
from typing import AsyncGenerator, Annotated

import pytest
from fastapi_users.schemas import BaseUser
from httpx import AsyncClient
from pytest_asyncio import is_async_test
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from auth.db import SQLAlchemyUserDatabase
from auth.manager import UserManager, get_user_manager
from auth.models import User
from auth.schema import UserCreate
from auth.strategy import get_jwt_strategy, get_refresh_redis_strategy
from core.db import get_async_session
from core.models import Base
from main import app

strategy = get_jwt_strategy()
refresh_strategy = get_refresh_redis_strategy()

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
test_session = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def create_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def get_test_async_session():
    async with test_session() as session:
        await create_database()
        yield session
        await delete_database()


@pytest.fixture
async def get_test_user_db(get_test_async_session):
    return SQLAlchemyUserDatabase(get_test_async_session, User)


@pytest.fixture
async def auth_client(user, get_test_async_session) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_async_session] = lambda: get_test_async_session

    async with AsyncClient(
        app=app,
        base_url="http://test",
        cookies={
            "access_token": await strategy.write_token(user),
            "refresh_token": await refresh_strategy.write_token(user),
        },
    ) as client:
        yield client


@pytest.fixture
async def user(get_test_user_db):
    user_manager = await anext(get_user_manager(get_test_user_db))
    created_user = await user_manager.create(UserCreate(email="t@t.com", password="t"))
    return created_user


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)
