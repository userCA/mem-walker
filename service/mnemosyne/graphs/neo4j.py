"""Neo4j graph store implementation."""

from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from ..exceptions import GraphStoreError
from ..utils import get_logger
from .base import GraphStoreBase
from .configs import Neo4jConfig

logger = get_logger(__name__)


class Neo4jGraphStore(GraphStoreBase):
    """
    Neo4j graph store implementation.
    
    Provides graph storage and traversal using Neo4j.
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize Neo4j graph store.
        
        Args:
            config: Configuration for Neo4j
        """
        if config is None:
            config = Neo4jConfig()
        
        self.config = config
        
        try:
            self.driver = GraphDatabase.driver(
                config.uri,
                auth=(config.user, config.password),
                max_connection_lifetime=config.max_connection_lifetime,
                max_connection_pool_size=config.max_connection_pool_size,
                connection_acquisition_timeout=config.connection_acquisition_timeout
            )
            logger.info(f"Connected to Neo4j at {config.uri}")
        except Exception as e:
            raise GraphStoreError(f"Failed to connect to Neo4j: {e}")
    
    def add_node(
        self,
        entity: str,
        properties: Dict[str, Any],
        user_id: str,
        embedding: Optional[List[float]] = None
    ) -> str:
        """Add an entity node."""
        query = """
        MERGE (e:__Entity__ {name: $entity, user_id: $user_id})
        ON CREATE SET e += $properties, e.mentions = 1, e.created_at = timestamp()
        ON MATCH SET e.mentions = e.mentions + 1, e.updated_at = timestamp()
        RETURN e.name as name
        """
        
        params = {
            "entity": entity,
            "user_id": user_id,
            "properties": properties
        }
        
        if embedding:
            params["properties"]["embedding"] = embedding
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, **params)
                record = result.single()
                if record:
                    logger.debug(f"Added/updated node: {entity}")
                    return record["name"]
                raise GraphStoreError(f"Failed to add node: {entity}")
        except Exception as e:
            raise GraphStoreError(f"Failed to add node: {e}")
    
    def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a relationship between entities."""
        # Ensure relation type is valid (alphanumeric and underscores)
        relation_type = relation_type.upper().replace(" ", "_")
        
        query = f"""
        MATCH (s:__Entity__ {{name: $source}})
        MATCH (t:__Entity__ {{name: $target}})
        MERGE (s)-[r:{relation_type}]->(t)
        ON CREATE SET r += $properties, r.created_at = timestamp()
        ON MATCH SET r.updated_at = timestamp()
        RETURN r
        """
        
        params = {
            "source": source,
            "target": target,
            "properties": properties or {}
        }
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, **params)
                if result.single():
                    logger.debug(f"Added relationship: {source} -{relation_type}-> {target}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to add relationship: {e}")
            return False
    
    def bfs_expand(
        self,
        entities: List[str],
        depth: int = 2,
        user_id: Optional[str] = None
    ) -> List[str]:
        """Breadth-first search expansion."""
        query = """
        MATCH path = (start:__Entity__)-[*1..$depth]-(end:__Entity__)
        WHERE start.name IN $entities
        """
        
        if user_id:
            query += " AND start.user_id = $user_id AND end.user_id = $user_id"
        
        query += " RETURN DISTINCT end.name as name"
        
        params = {
            "entities": entities,
            "depth": depth
        }
        
        if user_id:
            params["user_id"] = user_id
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, **params)
                expanded = [record["name"] for record in result]
                logger.debug(f"BFS expanded {len(entities)} entities to {len(expanded)}")
                return expanded
        except Exception as e:
            logger.error(f"BFS expansion failed: {e}")
            return []
    
    def get_node_centrality(self, entity: str) -> float:
        """Calculate centrality score."""
        query = """
        MATCH (e:__Entity__ {name: $entity})
        OPTIONAL MATCH (e)-[r]-()
        WITH e, count(r) as degree
        RETURN degree
        """
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, entity=entity)
                record = result.single()
                if record:
                    degree = record["degree"] or 0
                    # Normalize to 0-1 range (assuming max degree of 100)
                    return min(degree / 100.0, 1.0)
                return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate centrality: {e}")
            return 0.0
    
    def get_neighbors(
        self,
        entity: str,
        relation_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get neighboring entities."""
        if relation_types:
            types_str = "|".join(relation_types)
            query = f"""
            MATCH (e:__Entity__ {{name: $entity}})-[r:{types_str}]-(neighbor)
            RETURN neighbor.name as name, type(r) as relation
            """
        else:
            query = """
            MATCH (e:__Entity__ {name: $entity})-[r]-(neighbor)
            RETURN neighbor.name as name, type(r) as relation
            """
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, entity=entity)
                return [
                    {"name": record["name"], "relation": record["relation"]}
                    for record in result
                ]
        except Exception as e:
            logger.error(f"Failed to get neighbors: {e}")
            return []
    
    def delete_node(self, entity: str) -> bool:
        """Delete a node and its relationships."""
        query = """
        MATCH (e:__Entity__ {name: $entity})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, entity=entity)
                record = result.single()
                if record and record["deleted"] > 0:
                    logger.debug(f"Deleted node: {entity}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete node: {e}")
            return False
    
    def query(self, cypher_query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a custom Cypher query."""
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(cypher_query, **(params or {}))
                return [record.data() for record in result]
        except Exception as e:
            raise GraphStoreError(f"Query execution failed: {e}")
    
    def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
