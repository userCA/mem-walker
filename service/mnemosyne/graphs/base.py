"""Base abstract class for graph stores."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class GraphStoreBase(ABC):
    """
    Abstract base class for graph stores.
    
    All graph store implementations should inherit from this class.
    """
    
    @abstractmethod
    def add_node(
        self,
        entity: str,
        properties: Dict[str, Any],
        user_id: str,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Add an entity node to the graph.
        
        Args:
            entity: Entity name
            properties: Node properties/attributes
            user_id: User ID for multi-tenancy
            embedding: Optional embedding vector for the entity
            
        Returns:
            Node ID
        """
        pass
    
    @abstractmethod
    def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a relationship between two entities.
        
        Args:
            source: Source entity name
            target: Target entity name
            relation_type: Type of relationship (e.g., LIKES, WORKS_AT)
            properties: Optional relationship properties
            
        Returns:
            True if relationship added successfully
        """
        pass
    
    @abstractmethod
    def bfs_expand(
        self,
        entities: List[str],
        depth: int = 2,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Breadth-first search expansion from entities.
        
        Args:
            entities: Starting entity names
            depth: Maximum depth to traverse
            user_id: Optional user ID filter
            
        Returns:
            List of expanded entity names
        """
        pass
    
    @abstractmethod
    def get_node_centrality(self, entity: str) -> float:
        """
        Calculate centrality score for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            Centrality score (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    def get_neighbors(
        self,
        entity: str,
        relation_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get neighboring entities.
        
        Args:
            entity: Source entity name
            relation_types: Optional filter for relationship types
            
        Returns:
            List of neighbor entities with relationships
        """
        pass
    
    @abstractmethod
    def delete_node(self, entity: str) -> bool:
        """
        Delete a node and its relationships.
        
        Args:
            entity: Entity name to delete
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def query(self, cypher_query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a custom query (e.g., Cypher for Neo4j).
        
        Args:
            cypher_query: Query string
            params: Optional query parameters
            
        Returns:
            Query results
        """
        pass
