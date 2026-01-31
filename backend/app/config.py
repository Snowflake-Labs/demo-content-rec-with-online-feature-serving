# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Snowflake Connection
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_warehouse: str = "CONTENT_REC_WH"
    snowflake_database: str = "CONTENT_REC_DEMO"
    snowflake_schema: str = "FEATURES"
    snowflake_role: str = "PUBLIC"

    # Authentication (PAT recommended, password as fallback)
    snowflake_token: str = ""  # PAT (Programmatic Access Token)
    snowflake_password: str = ""  # Password (legacy)

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
