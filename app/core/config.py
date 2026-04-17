import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart City Traffic Management System"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./traffic.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if os.environ.get("VERCEL"):
            if not url or url.startswith("sqlite:///"):
                # Vercel filesystem is read-only, use /tmp for SQLite
                return "sqlite:////tmp/traffic.db"
        return url

    class Config:
        env_file = ".env"

settings = Settings()
