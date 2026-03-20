"""HuggingFace embedding implementation."""

import logging
import os
from typing import List, Literal, Optional, Union

from ..exceptions import EmbeddingError
from ..utils import get_logger
from .base import EmbeddingBase
from .configs import HuggingFaceEmbeddingConfig

logger = get_logger(__name__)

# Suppress verbose logs from transformers libraries
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)


class HuggingFaceEmbedding(EmbeddingBase):
    """
    HuggingFace embedding implementation.
    
    Supports two modes:
    1. Local mode: Uses sentence-transformers library
    2. Remote mode: Uses HuggingFace TEI (Text Embeddings Inference) endpoint
    """
    
    def __init__(self, config: Optional[HuggingFaceEmbeddingConfig] = None):
        """
        Initialize HuggingFace embedding.
        
        Args:
            config: Configuration for HuggingFace embedding
        """
        if config is None:
            config = HuggingFaceEmbeddingConfig()
        
        self.config = config
        self.use_remote = config.huggingface_base_url is not None
        hf_home = os.getenv("HF_HOME")
        cache_dir = (
            config.cache_dir
            or os.getenv("HUGGINGFACE_HUB_CACHE")
            or (os.path.join(hf_home, "hub") if hf_home else None)
        )
        self.config.cache_dir = cache_dir

        local_files_only_env = os.getenv("HF_HUB_OFFLINE") or os.getenv("TRANSFORMERS_OFFLINE")
        local_files_only = config.local_files_only or (local_files_only_env or "").lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }
        
        try:
            if self.use_remote:
                # Remote mode: Use OpenAI-compatible client for TEI
                from openai import OpenAI
                self.client = OpenAI(base_url=config.huggingface_base_url)
                logger.info(f"Initialized HuggingFace TEI client with URL: {config.huggingface_base_url}")
            else:
                # Local mode: Use sentence-transformers
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError:
                    raise ImportError(
                        "sentence-transformers is not installed. "
                        "Please install it using `pip install sentence-transformers`"
                    )
                
                self.model = SentenceTransformer(
                    config.model,
                    cache_folder=cache_dir,
                    local_files_only=local_files_only,
                    **config.model_kwargs
                )
                
                # Update dimension from model if not specified
                if config.dimension == 384:  # default value
                    self.config.dimension = self.model.get_sentence_embedding_dimension()
                
                logger.info(f"Initialized HuggingFace local model: {config.model}")
                
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize HuggingFace embedding: {e}")
    
    def embed(
        self,
        text: Union[str, List[str]],
        memory_action: Optional[Literal["add", "search", "update"]] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text or list of texts
            memory_action: Optional action type (not used for HuggingFace)
            
        Returns:
            Single embedding or list of embeddings
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        try:
            if self.use_remote:
                # Remote mode: Use TEI endpoint
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.config.model,
                    **self.config.model_kwargs
                )
                embeddings = [item.embedding for item in response.data]
            else:
                # Local mode: Use sentence-transformers
                embeddings = self.model.encode(
                    texts,
                    convert_to_numpy=True
                ).tolist()
                
                # Ensure embeddings is always a list of lists
                if is_single and isinstance(embeddings[0], (int, float)):
                    embeddings = [embeddings]
            
            logger.debug(f"Generated embeddings for {len(texts)} text(s)")
            
            return embeddings[0] if is_single else embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise EmbeddingError(f"Embedding generation failed: {e}")
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                if self.use_remote:
                    # Remote mode: Use TEI endpoint
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.config.model,
                        **self.config.model_kwargs
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                else:
                    # Local mode: Use sentence-transformers
                    batch_embeddings = self.model.encode(
                        batch,
                        convert_to_numpy=True,
                        batch_size=batch_size
                    ).tolist()
                
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Processed batch {i // batch_size + 1}, size: {len(batch)}")
                
            except Exception as e:
                logger.error(f"Failed to process batch {i // batch_size + 1}: {e}")
                raise EmbeddingError(f"Batch embedding failed: {e}")
        
        logger.info(f"Generated {len(all_embeddings)} embeddings in batches")
        return all_embeddings
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.config.dimension
