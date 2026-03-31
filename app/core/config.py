import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "Luminnal Job Engine"
    app_version: str = "0.1.0"

    database_url: str | None = os.getenv("DATABASE_URL")

    ai_provider: str = os.getenv("AI_PROVIDER", "none")
    ai_model: str = os.getenv("AI_MODEL", "none")


settings = Settings()