from datetime import datetime
from typing import Union, TypedDict, Callable

import pytest
from faker import Faker
from fastapi_users.schemas import BaseUser

from conftest import fake
from referral_program.db import ReferralProgramRepository
from referral_program.models import ReferralCode
from referral_program.schema import ReferralCodeCreate


class DateTimeBetweenKwargs(TypedDict):
    start_date: Union[datetime, str]
    end_date: Union[datetime, str]


@pytest.fixture
async def get_test_referral_program_repository(get_test_async_session):
    yield ReferralProgramRepository(get_test_async_session)


@pytest.fixture
async def referral_code(request, get_test_referral_program_repository: ReferralProgramRepository, user: BaseUser):
    kwargs = getattr(request, "param", None) or DateTimeBetweenKwargs(start_date="+1d", end_date="+10d")

    referral_code: ReferralCode = ReferralCode(referrer_id=user.id, expired_at=fake.date_time_between(**kwargs))
    await get_test_referral_program_repository.create_referral_code(referral_code)
    return referral_code
