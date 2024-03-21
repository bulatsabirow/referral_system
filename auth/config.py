import os.path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    JWT_SECRET: str = "SECRET"
    RESET_PASSWORD_TOKEN_SECRET: str = "SECRET"
    VERIFICATION_TOKEN_SECRET: str = "SECRET"
    JWT_ACCESS_TOKEN_LIFETIME_SECONDS: int = 300
    JWT_REFRESH_TOKEN_LIFETIME_SECONDS: int = 2629746
    JWT_REFRESH_TOKEN_LENGTH: int = 64

    model_config = SettingsConfigDict(env_file=os.path.join(".env"), env_file_encoding="utf-8", extra="ignore")


auth_settings = AuthSettings()
