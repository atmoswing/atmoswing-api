from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_dir: str = "./data"
    debug: bool = False
    # File receiving the errors (everything in debug mode); None logs to the terminal only
    log_file: str | None = None
    # Requests allowed per client (IP address), all routes together
    rate_limit: str = "600/minute"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """
    FastAPI dependency providing the settings. Tests override it through
    app.dependency_overrides[get_settings].
    """
    return Settings()
