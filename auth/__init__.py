from fastapi_users import FastAPIUsers

from auth.backend import auth_backend
from auth.manager import get_user_manager
from auth.models import User

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)