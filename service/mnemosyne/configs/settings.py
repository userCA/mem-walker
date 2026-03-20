"""Global configuration settings for Mnemosyne."""

from dotenv import load_dotenv
load_dotenv()

from dataclasses import dataclass, field
from typing import Optional

from ..embeddings.configs import OpenAIEmbeddingConfig
from ..graphs.configs import Neo4jConfig
from ..llms.configs import OpenAILLMConfig
from ..reranker.configs import RerankerConfig
from ..vector_stores.configs import MilvusConfig
from .local_storage import LocalStorageConfig, StorageBackendConfig


@dataclass
class LocalSLMConfig:
    """Configuration for local small language model."""
    model_path: str = "qwen2.5-0.5b-instruct"
    base_url: str = "http://localhost:8000/v1"
    api_key: str = "EMPTY"
    n_gpu_layers: int = -1  # -1 = use all GPU layers, 0 = CPU only
    n_ctx: int = 2048  # Context window size


@dataclass
class SimpleLocalLLMConfig:
    """Configuration for simple local LLM."""
    model_name: str = ""
    base_url: str = ""


@dataclass
class GlobalSettings:
    """Global settings for Mnemosyne memory system."""

    # Component configurations
    embedding_config: OpenAIEmbeddingConfig = field(default_factory=OpenAIEmbeddingConfig)
    vector_store_config: MilvusConfig = field(default_factory=MilvusConfig)
    graph_store_config: Neo4jConfig = field(default_factory=Neo4jConfig)
    llm_config: OpenAILLMConfig = field(default_factory=OpenAILLMConfig)
    local_slm_config: LocalSLMConfig = field(default_factory=LocalSLMConfig)
    simple_local_llm_config: SimpleLocalLLMConfig = field(default_factory=SimpleLocalLLMConfig)
    reranker_config: RerankerConfig = field(default_factory=RerankerConfig)

    # Local storage configuration (SQLite + FAISS)
    local_storage_config: LocalStorageConfig = field(default_factory=LocalStorageConfig)
    storage_backend_config: StorageBackendConfig = field(default_factory=StorageBackendConfig)

    # Memory system settings
    default_user_id: str = "default"
    enable_fact_extraction: bool = True
    enable_graph_memory: bool = True
    enable_reranking: bool = True
    enable_local_slm: bool = False

    # Performance settings
    batch_size: int = 32
    max_workers: int = 4

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "GlobalSettings":
        """Load settings from environment variables."""
        import os

        settings = cls()

        # Load API keys from env
        if openai_key := os.getenv("OPENAI_API_KEY"):
            settings.embedding_config.api_key = openai_key
            settings.llm_config.api_key = openai_key

        # Load Milvus config from env
        if milvus_host := os.getenv("MILVUS_HOST"):
            settings.vector_store_config.host = milvus_host
        if milvus_port := os.getenv("MILVUS_PORT"):
            settings.vector_store_config.port = int(milvus_port)

        # Load Neo4j config from env
        if neo4j_uri := os.getenv("NEO4J_URI"):
            settings.graph_store_config.uri = neo4j_uri
        if neo4j_password := os.getenv("NEO4J_PASSWORD"):
            settings.graph_store_config.password = neo4j_password

        # Load Local SLM config from env
        if slm_model := os.getenv("LOCAL_SLM_MODEL"):
            settings.local_slm_config.model_path = slm_model
        if slm_base_url := os.getenv("LOCAL_SLM_BASE_URL"):
            settings.local_slm_config.base_url = slm_base_url
        if slm_api_key := os.getenv("LOCAL_SLM_API_KEY"):
            settings.local_slm_config.api_key = slm_api_key
        if enable_slm := os.getenv("ENABLE_LOCAL_SLM"):
            settings.enable_local_slm = enable_slm.lower() == "true"

        # Load Simple Local LLM config from env
        if local_llm_model := os.getenv("LOCAL_LLM_MODEL"):
            settings.simple_local_llm_config.model_name = local_llm_model
        if local_llm_base_url := os.getenv("LOCAL_LLM_BASE_URL"):
            settings.simple_local_llm_config.base_url = local_llm_base_url

        # Load Local Storage config from env
        if local_enabled := os.getenv("LOCAL_STORAGE_ENABLED"):
            settings.local_storage_config.enabled = local_enabled.lower() == "true"
        if local_db_path := os.getenv("LOCAL_STORAGE_DB_PATH"):
            settings.local_storage_config.db_path = local_db_path
        if local_index_dir := os.getenv("LOCAL_STORAGE_VECTOR_INDEX_DIR"):
            settings.local_storage_config.vector_index_dir = local_index_dir
        if storage_backend := os.getenv("STORAGE_BACKEND"):
            settings.storage_backend_config.backend = storage_backend

        return settings
