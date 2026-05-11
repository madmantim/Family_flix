from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    tmdb_api_key: str
    tmdb_access_token: str
    omdb_api_key: str = ""
    database_url: str = "sqlite:///./family_flix.db"
    # Comma-separated list of allowed CORS origins. Default permits all (useful
    # for local dev). In production, set CORS_ORIGINS to your deployed domain(s).
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
