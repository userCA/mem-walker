from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class AdapterConfig(BaseSettings):
    # API 配置
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM 配置
    llm_provider: str = "deepseek"  # deepseek | openai | local
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # mnemosyne 配置
    storage_backend: str = "local"
    local_db_path: str = "./data/mnemosyne.db"

    # 可观测性
    log_level: str = "INFO"
    enable_tracing: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ADAPTER_",
        extra="ignore"  # Ignore extra fields from env
    )

@lru_cache()
def get_config() -> AdapterConfig:
    return AdapterConfig()