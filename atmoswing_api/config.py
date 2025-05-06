from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_dir: str = "./data"
    keep_days: int = 30

    model_config = SettingsConfigDict(env_file=".env")
