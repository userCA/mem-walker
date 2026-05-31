"""DuckDB graph store implementation."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import duckdb

from ..exceptions import GraphStoreError
from ..utils import get_logger
from .base import GraphStoreBase
from .configs import DuckDBConfig

logger = get_logger(__name__)


class DuckDBGraphStore(GraphStoreBase):
    """
    DuckDB graph store implementation.

    Provides graph storage and traversal using DuckDB (SQL-based).
    Ideal for development and medium-scale deployments.
    """

    def __init__(self, config: Optional[DuckDBConfig] = None):
        """
        Initialize DuckDB graph store.

        Args:
            config: Configuration for DuckDB
        """
        if config is None:
            config = DuckDBConfig()

        self.config = config
        self._tables_created = False

        try:
            self.conn = duckdb.connect(
                database=config.db_path,
                read_only=config.read_only,
                config=config.config or {},
            )
            # Note: DuckDB handles conflicts differently than SQLite
            # ON CONFLICT DO UPDATE works without disabling foreign keys
            self._create_tables()
            logger.info(f"Connected to DuckDB at {config.db_path}")
        except Exception as e:
            raise GraphStoreError(f"Failed to connect to DuckDB: {e}")

    def _create_tables(self) -> None:
        """Create graph tables if they don't exist."""
        if self._tables_created:
            return

        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS entity_id_seq;
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY DEFAULT nextval('entity_id_seq'),
                name VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                entity_type VARCHAR DEFAULT 'UNKNOWN',
                properties JSON,
                mentions INTEGER DEFAULT 1,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(name, user_id)
            );
        """)

        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS relation_id_seq;
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY DEFAULT nextval('relation_id_seq'),
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type VARCHAR NOT NULL,
                properties JSON,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(source_id, target_id, relation_type)
            );
        """)

        # Create indexes for performance
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_user_id ON entities(user_id);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);"
        )

        self._tables_created = True
        logger.debug("DuckDB graph tables created/verified")

    def add_node(
        self,
        entity: str,
        properties: Dict[str, Any],
        user_id: str,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """Add an entity node."""
        entity_type = properties.pop("type", "UNKNOWN")
        if embedding:
            properties["embedding"] = embedding

        props_json = json.dumps(properties)
        now = datetime.now()

        query = """
            INSERT INTO entities (name, user_id, entity_type, properties, mentions, created_at, updated_at)
            VALUES ($1, $2, $3, $4::JSON, 1, $5, $5)
            ON CONFLICT (name, user_id) DO UPDATE SET
                mentions = entities.mentions + 1,
                updated_at = $5,
                properties = json_merge_patch(entities.properties, $4::JSON)
            RETURNING name
        """

        try:
            result = self.conn.execute(
                query, [entity, user_id, entity_type, props_json, now]
            ).fetchone()
            if result:
                logger.debug(f"Added/updated node: {entity}")
                return result[0]
            raise GraphStoreError(f"Failed to add node: {entity}")
        except Exception as e:
            raise GraphStoreError(f"Failed to add node: {e}")

    def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a relationship between entities."""
        # Normalize relation type
        relation_type = relation_type.upper().replace(" ", "_")
        props_json = json.dumps(properties or {})

        # Get entity IDs
        now = datetime.now()
        query = """
            WITH source_id AS (
                SELECT id FROM entities WHERE name = $1
            ), target_id AS (
                SELECT id FROM entities WHERE name = $2
            )
            INSERT INTO relations (source_id, target_id, relation_type, properties, created_at, updated_at)
            SELECT s.id, t.id, $3, $4::JSON, $5, $5
            FROM source_id s, target_id t
            ON CONFLICT (source_id, target_id, relation_type) DO UPDATE SET
                updated_at = $5,
                properties = json_merge_patch(relations.properties, $4::JSON)
            RETURNING id
        """

        try:
            result = self.conn.execute(
                query, [source, target, relation_type, props_json, now]
            ).fetchone()
            if result:
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
        user_id: Optional[str] = None,
    ) -> List[str]:
        """Breadth-first search expansion."""
        if not entities:
            return []

        try:
            # Build recursive CTE for BFS
            user_filter = ""
            params: List[Any] = [entities, depth]
            param_idx = 3

            if user_id:
                user_filter = "AND e2.user_id = $3"
                params.append(user_id)

            query = f"""
                WITH RECURSIVE bfs AS (
                    -- Base case: starting entities
                    SELECT e.id, e.name, 0 as level
                    FROM entities e
                    WHERE e.name = ANY($1)

                    UNION ALL

                    -- Recursive case: expand to neighbors
                    SELECT e2.id, e2.name, bfs.level + 1
                    FROM bfs
                    JOIN relations r ON r.source_id = bfs.id
                    JOIN entities e2 ON e2.id = r.target_id
                    WHERE bfs.level < $2
                    {user_filter}
                    AND NOT EXISTS (
                        SELECT 1 FROM bfs b2 WHERE b2.id = e2.id
                    )
                )
                SELECT DISTINCT name FROM bfs WHERE level > 0
            """

            result = self.conn.execute(query, params).fetchall()
            expanded = [row[0] for row in result]
            logger.debug(f"BFS expanded {len(entities)} entities to {len(expanded)}")
            return expanded
        except Exception as e:
            logger.error(f"BFS expansion failed: {e}")
            return []

    def get_node_centrality(self, entity: str) -> float:
        """Calculate centrality score."""
        query = """
            SELECT COUNT(r.id) as degree
            FROM entities e
            LEFT JOIN relations r ON e.id = r.source_id OR e.id = r.target_id
            WHERE e.name = $1
            GROUP BY e.id
        """

        try:
            result = self.conn.execute(query, [entity]).fetchone()
            if result:
                degree = result[0] or 0
                # Normalize to 0-1 range (assuming max degree of 100)
                return min(degree / 100.0, 1.0)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate centrality: {e}")
            return 0.0

    def get_neighbors(
        self,
        entity: str,
        relation_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get neighboring entities."""
        if relation_types:
            types_str = "', '".join([r.upper().replace(" ", "_") for r in relation_types])
            query = f"""
                SELECT DISTINCT e.name, r.relation_type
                FROM entities e
                JOIN relations r ON (
                    (r.source_id = (SELECT id FROM entities WHERE name = $1) AND e.id = r.target_id)
                    OR (r.target_id = (SELECT id FROM entities WHERE name = $1) AND e.id = r.source_id)
                )
                WHERE r.relation_type IN ('{types_str}')
            """
            params = [entity]
        else:
            query = """
                SELECT DISTINCT e.name, r.relation_type
                FROM entities e
                JOIN relations r ON (
                    (r.source_id = (SELECT id FROM entities WHERE name = $1) AND e.id = r.target_id)
                    OR (r.target_id = (SELECT id FROM entities WHERE name = $1) AND e.id = r.source_id)
                )
            """
            params = [entity]

        try:
            result = self.conn.execute(query, params).fetchall()
            return [{"name": row[0], "relation": row[1]} for row in result]
        except Exception as e:
            logger.error(f"Failed to get neighbors: {e}")
            return []

    def delete_node(self, entity: str) -> bool:
        """Delete a node and its relationships."""
        query = """
            WITH deleted AS (
                DELETE FROM entities WHERE name = $1 RETURNING id
            )
            SELECT COUNT(*) FROM deleted
        """

        try:
            result = self.conn.execute(query, [entity]).fetchone()
            if result and result[0] > 0:
                logger.debug(f"Deleted node: {entity}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete node: {e}")
            return False

    def query(self, sql_query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a custom SQL query."""
        try:
            result = self.conn.execute(sql_query, params or {}).fetchall()
            # Get column names from cursor description
            columns = [desc[0] for desc in self.conn.description] if self.conn.description else []
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            raise GraphStoreError(f"Query execution failed: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed DuckDB connection")
