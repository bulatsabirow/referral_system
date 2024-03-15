from fastapi import FastAPI

from auth import fastapi_users, auth_backend
from auth.schema import UserRead, UserCreate
from referral_program.views import router

app = FastAPI(title="Stakewolle")

app.include_router(router)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"])
