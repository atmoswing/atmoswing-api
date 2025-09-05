from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_dir: str = "./data"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")
