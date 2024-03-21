import asyncio
from datetime import datetime
from typing import AsyncGenerator
from typing import Union, TypedDict

import aioredis
import pytest
from faker import Faker
from fastapi_users.schemas import BaseUser
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from auth.config import auth_settings
from auth.db import SQLAlchemyUserDatabase
from auth.manager import get_user_manager
from auth.models import User
from auth.schema import UserCreate
from auth.strategy import get_jwt_strategy, get_refresh_redis_strategy, RefreshRedisStrategy
from core.config import settings
from core.db import get_async_session
from core.models import Base
from factories import TestUser, TestUserWithoutReferralCode
from main import app
from referral_program.db import ReferralProgramRepository
from referral_program.models import ReferralCode
from tests_utils import TokenCookies, async_partial, DateTimeBetweenKwargs, dependencies_overrider


TEST_REDIS_URL = settings.REDIS_URL.replace(str(settings.REDIS_DB), str(settings.TEST_REDIS_DB))
test_redis = aioredis.from_url(TEST_REDIS_URL)


def get_test_refresh_redis_strategy():
    return RefreshRedisStrategy(
        key_prefix="", redis=test_redis, lifetime_seconds=auth_settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS
    )


strategy = get_jwt_strategy()
refresh_strategy = get_test_refresh_redis_strategy()

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
test_session = async_sessionmaker(expire_on_commit=False, autocommit=False, autoflush=False, bind=test_engine)
fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def clear_redis():
    await test_redis.flushdb()


async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def get_test_async_session():
    async with test_session() as session:
        try:
            await create_tables()
            yield session
        finally:
            await drop_tables()


@pytest.fixture
async def get_test_user_db(get_test_async_session):
    return SQLAlchemyUserDatabase(get_test_async_session, User)


@pytest.fixture
async def auth_client(user: BaseUser, get_test_async_session) -> AsyncGenerator[AsyncClient, None]:
    overridden_dependencies = {
        get_async_session: lambda: get_test_async_session,
        get_refresh_redis_strategy: get_test_refresh_redis_strategy,
    }

    with dependencies_overrider(app, overridden_dependencies) as test_app:
        async with AsyncClient(
            app=test_app,
            base_url="http://test",
            cookies=TokenCookies(
                access_token=await strategy.write_token(user), refresh_token=await refresh_strategy.write_token(user)
            ),
        ) as client:
            yield client


@pytest.fixture
async def user(get_test_user_db):
    user_manager = await anext(get_user_manager(get_test_user_db))
    created_user = await user_manager.create(UserCreate(**TestUser().model_dump()))
    return created_user


@pytest.fixture
async def get_referral_user(get_test_user_db):
    return async_partial(create_user, get_test_user_db)


async def create_user(get_test_user_db, referral_code=None):
    user_manager = await anext(get_user_manager(get_test_user_db))
    created_user = await user_manager.create(
        UserCreate(**TestUserWithoutReferralCode().model_dump(), referral_code=referral_code)
    )
    return created_user


@pytest.fixture
async def get_test_referral_program_repository(get_test_async_session):
    yield ReferralProgramRepository(get_test_async_session)


@pytest.fixture
async def referral_code(request, get_test_referral_program_repository: ReferralProgramRepository, user: BaseUser):
    kwargs = getattr(request, "param", None) or DateTimeBetweenKwargs(start_date="+1d", end_date="+10d")

    referral_code: ReferralCode = ReferralCode(referrer_id=user.id, expired_at=fake.date_time_between(**kwargs))
    await get_test_referral_program_repository.create_referral_code(referral_code)
    return referral_code
