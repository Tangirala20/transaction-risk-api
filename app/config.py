import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./risk_api.db")
    api_key: str = os.getenv("API_KEY", "local-dev-key-change-me")

settings = Settings()
