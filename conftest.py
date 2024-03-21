import asyncio
from datetime import datetime
from typing import AsyncGenerator
from typing import Union, TypedDict

import pytest
from faker import Faker
from fastapi_users.schemas import BaseUser
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from auth.db import SQLAlchemyUserDatabase
from auth.manager import get_user_manager
from auth.models import User
from auth.schema import UserCreate
from auth.strategy import get_jwt_strategy, get_refresh_redis_strategy
from core.db import get_async_session
from core.models import Base
from factories import TestUser, TestUserWithoutReferralCode
from main import app
from referral_program.db import ReferralProgramRepository
from referral_program.models import ReferralCode

strategy = get_jwt_strategy()
refresh_strategy = get_refresh_redis_strategy()

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
test_session = async_sessionmaker(expire_on_commit=False, autocommit=False, autoflush=False, bind=test_engine)
# TODO use testing Redis connection
fake = Faker()


class DateTimeBetweenKwargs(TypedDict):
    start_date: Union[datetime, str]
    end_date: Union[datetime, str]


def async_partial(f, *args):
    async def f2(*args2):
        return await f(*args, *args2)

    return f2


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
    # TODO use context manager for dependency overriding
    app.dependency_overrides[get_async_session] = lambda: get_test_async_session

    async with AsyncClient(
        app=app,
        base_url="http://test",
        # TODO use TypedDict type
        cookies={
            "access_token": await strategy.write_token(user),
            "refresh_token": await refresh_strategy.write_token(user),
        },
    ) as client:
        yield client

    app.dependency_overrides.clear()


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
