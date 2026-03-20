"""Search strategies for memory retrieval.

Implements strategy pattern for flexible search algorithms.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..embeddings.base import EmbeddingBase
from ..graphs.base import GraphStoreBase
from ..llms.base import LLMBase
from ..reranker.base import RerankerBase
from ..utils import get_logger
from ..vector_stores.base import VectorStoreBase

logger = get_logger(__name__)


class SearchStrategy(ABC):
    """Abstract base for search strategies."""
    
    @abstractmethod
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Execute search and return results."""
        pass


class VectorSearchStrategy(SearchStrategy):
    """Pure vector similarity search."""
    
    def __init__(
        self,
        embedding: EmbeddingBase,
        vector_store: VectorStoreBase
    ):
        self.embedding = embedding
        self.vector_store = vector_store
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using vector similarity only."""
        query_vector = self.embedding.embed(query)
        
        results = self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            filters={"user_id": user_id}
        )
        
        logger.debug(f"Vector search found {len(results)} results")
        return results


class GraphSearchStrategy(SearchStrategy):
    """Pure graph traversal search."""
    
    def __init__(
        self,
        llm: LLMBase,
        graph_store: GraphStoreBase,
        vector_store: VectorStoreBase
    ):
        self.llm = llm
        self.graph_store = graph_store
        self.vector_store = vector_store
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using graph traversal."""
        # Extract entities from query
        entities = self.llm.extract_entities(query)
        entity_names = [e.get("entity") for e in entities if e.get("entity")]
        
        if not entity_names:
            return []
        
        # Expand graph
        expanded = self.graph_store.bfs_expand(
            entities=entity_names,
            depth=2,
            user_id=user_id
        )
        
        # Get centrality scores
        scored_entities = []
        for entity in expanded:
            centrality = self.graph_store.get_node_centrality(entity)
            scored_entities.append((entity, centrality))
        
        # Sort by centrality
        scored_entities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top entities as results (simplified)
        results = [
            {
                "id": entity,
                "content": entity,
                "score": score,
                "user_id": user_id,
                "metadata": {"type": "graph_entity"}
            }
            for entity, score in scored_entities[:limit]
        ]
        
        logger.debug(f"Graph search found {len(results)} results")
        return results


class HybridSearchStrategy(SearchStrategy):
    """Hybrid search combining multiple strategies."""
    
    def __init__(
        self,
        strategies: List[SearchStrategy],
        weights: List[float],
        reranker: RerankerBase = None
    ):
        """
        Initialize hybrid search.
        
        Args:
            strategies: List of search strategies to combine
            weights: Weight for each strategy (should sum to 1.0)
            reranker: Optional reranker for final results
        """
        assert len(strategies) == len(weights), "Strategies and weights must match"
        assert abs(sum(weights) - 1.0) < 1e-6, "Weights should sum to 1.0"
        
        self.strategies = strategies
        self.weights = weights
        self.reranker = reranker
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search with weighted combination.
        
        Combines results from multiple strategies and optionally reranks.
        """
        # Collect results from all strategies
        all_results = {}  # memory_id -> result
        
        for strategy, weight in zip(self.strategies, self.weights):
            results = strategy.search(query, user_id, limit * 2)
            
            for result in results:
                memory_id = result.get("id")
                
                if memory_id not in all_results:
                    all_results[memory_id] = result.copy()
                    all_results[memory_id]["score"] = 0.0
                
                # Add weighted score
                all_results[memory_id]["score"] += result.get("score", 0.0) * weight
        
        # Convert to list
        combined_results = list(all_results.values())
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Optional reranking
        if self.reranker and combined_results:
            logger.debug("Applying reranking")
            combined_results = self.reranker.rerank(
                query=query,
                candidates=combined_results,
                top_k=limit
            )
        else:
            combined_results = combined_results[:limit]
        
        logger.info(f"Hybrid search found {len(combined_results)} results")
        return combined_results
