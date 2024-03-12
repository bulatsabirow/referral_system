import os.path
from functools import lru_cache

from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    JWT_SECRET: str = "SECRET"
    RESET_PASSWORD_TOKEN_SECRET: str = "SECRET"
    VERIFICATION_TOKEN_SECRET: str = "SECRET"

    class Config:
        env_file = os.path.join("..", ".env")
        env_file_encoding = "utf-8"


auth_settings = AuthSettings()
