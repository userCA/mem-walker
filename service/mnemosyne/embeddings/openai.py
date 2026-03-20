"""OpenAI embedding implementation."""

from typing import List, Literal, Optional, Union

from openai import OpenAI

from ..exceptions import EmbeddingError
from ..utils import get_logger
from .base import EmbeddingBase
from .configs import OpenAIEmbeddingConfig

logger = get_logger(__name__)


class OpenAIEmbedding(EmbeddingBase):
    """
    OpenAI embedding implementation.
    
    Uses OpenAI's text-embedding models for generating embeddings.
    """
    
    def __init__(self, config: Optional[OpenAIEmbeddingConfig] = None):
        """
        Initialize OpenAI embedding.
        
        Args:
            config: Configuration for OpenAI embedding
        """
        if config is None:
            config = OpenAIEmbeddingConfig()
        
        self.config = config
        
        try:
            self.client = OpenAI(api_key=config.api_key)
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize OpenAI client: {e}")
        
        logger.info(f"Initialized OpenAI embedding with model: {config.model}")
    
    def embed(
        self,
        text: Union[str, List[str]],
        memory_action: Optional[Literal["add", "search", "update"]] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text or list of texts
            memory_action: Optional action type (not used for OpenAI)
            
        Returns:
            Single embedding or list of embeddings
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        try:
            response = self.client.embeddings.create(
                model=self.config.model,
                input=texts,
                encoding_format=self.config.encoding_format
            )
            
            embeddings = [item.embedding for item in response.data]
            
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
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=batch,
                    encoding_format=self.config.encoding_format
                )
                
                batch_embeddings = [item.embedding for item in response.data]
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
