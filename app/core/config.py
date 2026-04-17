import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    REDIS_URL: str

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if os.environ.get("VERCEL") and url.startswith("sqlite:///"):
            # Vercel filesystem is read-only, use /tmp for SQLite
            url = "sqlite:////tmp/traffic.db"
        return url

    class Config:
        env_file = ".env"

settings = Settings()
