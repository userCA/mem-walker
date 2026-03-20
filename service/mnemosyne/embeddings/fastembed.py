"""FastEmbed embedding implementation."""

import os
from typing import List, Literal, Optional, Union

from ..exceptions import EmbeddingError
from ..utils import get_logger
from .base import EmbeddingBase
from .configs import FastEmbedConfig

logger = get_logger(__name__)

try:
    from fastembed import TextEmbedding
except ImportError:
    raise ImportError(
        "FastEmbed is not installed. Please install it using `pip install fastembed`"
    )


class FastEmbedEmbedding(EmbeddingBase):
    """
    FastEmbed embedding implementation.
    
    Uses FastEmbed with ONNX runtime for fast, efficient embeddings.
    """
    
    def __init__(self, config: Optional[FastEmbedConfig] = None):
        """
        Initialize FastEmbed embedding.
        
        Args:
            config: Configuration for FastEmbed embedding
        """
        if config is None:
            config = FastEmbedConfig()
        
        self.config = config
        cache_dir = config.cache_dir or os.getenv("FASTEMBED_CACHE_PATH")
        self.config.cache_dir = cache_dir

        local_files_only_env = os.getenv("FASTEMBED_LOCAL_FILES_ONLY")
        local_files_only = config.local_files_only or (local_files_only_env or "").lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }
        
        try:
            self.model = TextEmbedding(
                model_name=config.model,
                cache_dir=cache_dir,
                threads=config.threads,
                local_files_only=local_files_only,
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize FastEmbed model: {e}")
        
        logger.info(f"Initialized FastEmbed embedding with model: {config.model}")
    
    def embed(
        self,
        text: Union[str, List[str]],
        memory_action: Optional[Literal["add", "search", "update"]] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text or list of texts
            memory_action: Optional action type (not used for FastEmbed)
            
        Returns:
            Single embedding or list of embeddings
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        # Clean text
        texts = [t.replace("\n", " ") for t in texts]
        
        try:
            embeddings = list(self.model.embed(texts))
            embeddings = [emb.tolist() for emb in embeddings]
            
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
            batch = [t.replace("\n", " ") for t in batch]
            
            try:
                batch_embeddings = list(self.model.embed(batch))
                batch_embeddings = [emb.tolist() for emb in batch_embeddings]
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
