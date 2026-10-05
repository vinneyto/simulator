from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_PATH = Path.home() / ".simulator" / "simulator.sqlite3"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_DATABASE_PATH}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIMULATOR_", extra="ignore")
    database_url: str = DEFAULT_DATABASE_URL
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    library_directory: Path = Path.home() / ".simulator" / "library"
    dev_user_id: str = Field(default="dev-user", min_length=1, max_length=128)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
