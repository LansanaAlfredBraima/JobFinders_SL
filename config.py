import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env") if os.path.exists(os.path.join(os.path.dirname(__file__), ".env")) else None,
        extra="ignore"
    )

settings = Settings()
