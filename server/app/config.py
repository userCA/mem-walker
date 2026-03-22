from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "Mnemosyne Memory System"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Memory defaults
    default_page_size: int = 20
    max_page_size: int = 100

    # Backend defaults
    default_backend_host: str = "localhost"
    default_backend_port: int = 19530

    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
