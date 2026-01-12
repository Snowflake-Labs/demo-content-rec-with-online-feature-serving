from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Snowflake Connection
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_warehouse: str = "CONTENT_REC_WH"
    snowflake_database: str = "CONTENT_REC_DEMO"
    snowflake_schema: str = "FEATURES"
    snowflake_role: str = "PUBLIC"

    # Application Settings
    use_mock: bool = True  # Use mock data instead of Snowflake
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
