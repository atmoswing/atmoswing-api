from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_dir: str = "./data"

    model_config = SettingsConfigDict(env_file=".env")
