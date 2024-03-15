from fastapi import FastAPI

from auth.backend import auth_backend
from auth.fastapi_users import fastapi_users
from auth.schema import UserRead, UserCreate
from core.redis import redis
from referral_program.views import router

app = FastAPI(title="Referral system")


@app.on_event("shutdown")
async def shutdown_event():
    await redis.close()


app.include_router(router)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"])
