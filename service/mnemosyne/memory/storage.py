"""Memory storage coordination layer.

Implements Writer/Reader/Lifecycle components following facade pattern.
"""

import hashlib
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from ..embeddings.base import EmbeddingBase
from ..exceptions import MemoryError
from ..graphs.base import GraphStoreBase
from ..llms.base import LLMBase
from ..utils import get_logger
from ..vector_stores.base import VectorStoreBase
from .bm25_calculator import BM25Calculator

logger = get_logger(__name__)


def _reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Fuse multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        results_list: List of result lists, each sorted by score (descending)
        k: RRF parameter (default 60, higher = more weight to lower ranks)

    Returns:
        Fused and re-ranked list of results
    """
    scores = {}
    item_data = {}

    for results in results_list:
        for rank, item in enumerate(results):
            item_id = item.get("id")
            if not item_id:
                continue

            # Accumulate RRF score
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)

            # Keep item data from first occurrence
            if item_id not in item_data:
                item_data[item_id] = item

    # Sort by fused score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Build result list preserving item data with fused score
    fused = []
    for item_id in sorted_ids:
        item = item_data[item_id].copy()
        item["fused_score"] = scores[item_id]
        fused.append(item)

    return fused


class _MemoryWriter:
    """Internal writer component - handles memory creation."""

    # Semantic similarity thresholds for conflict detection
    SEMANTIC_DUPLICATE_THRESHOLD = 0.99  # Above this = exact duplicate
    SEMANTIC_SAFE_THRESHOLD = 0.70       # Below this = no conflict risk
    SEMANTIC_GRAY_ZONE_MIN = 0.70        # Gray zone lower bound
    SEMANTIC_GRAY_ZONE_MAX = 0.99        # Gray zone upper bound

    # Conflict resolution strategies
    STRATEGY_NEWER_WINS = "newer_wins"   # New memory overwrites/conflicts old
    STRATEGY_KEEP_BOTH = "keep_both"     # Keep both, mark as conflict
    STRATEGY_SKIP = "skip"               # Skip inserting if conflict

    def __init__(
        self,
        embedding: EmbeddingBase,
        vector_store: VectorStoreBase,
        graph_store: GraphStoreBase,
        llm: LLMBase,
        conflict_strategy: str = STRATEGY_NEWER_WINS,
        bm25_calculator: Optional[BM25Calculator] = None
    ):
        self.embedding = embedding
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.llm = llm
        self.conflict_strategy = conflict_strategy
        self.bm25_calculator = bm25_calculator or BM25Calculator()
        self._graph_lock = threading.Lock()
    
    def add(
        self,
        messages: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        infer: bool = True
    ) -> str:
        """
        Add a single memory.
        
        Args:
            messages: Content to remember
            user_id: User ID
            metadata: Optional metadata
            infer: Whether to extract facts using LLM
            
        Returns:
            Memory ID
        """
        try:
            memory_id = str(uuid.uuid4())
            
            # --- Phase 1: Pre-inference Deduplication (Fast) ---
            # 1.1 Hash Deduplication
            content_hash = hashlib.md5(messages.strip().encode('utf-8')).hexdigest()
            
            existing = self.vector_store.list(
                filters={"user_id": user_id, "content_hash": content_hash},
                limit=1
            )
            if existing:
                logger.info(f"Duplicate memory found (hash) for user {user_id}, skipping insert.")
                return existing[0]["id"]

            # 1.2 Semantic Deduplication
            # When infer=True, we do semantic dedup AFTER extraction on the extracted content
            # When infer=False, we do semantic dedup on the raw message
            embedding_vector = None
            similar_memories = []
            _top_match_score = 0.0

            if not infer:
                # For non-infer mode, check dedup on raw message (before LLM cost)
                logger.debug("Generating embedding for deduplication check")
                embedding_vector = self.embedding.embed(messages)

                try:
                    similar_memories = self.vector_store.search(
                        query_vector=embedding_vector,
                        limit=1,
                        filters={"user_id": user_id}
                    )

                    if similar_memories:
                        top_match = similar_memories[0]
                        # Threshold 0.99 indicates nearly identical content
                        if top_match.get("score", 0.0) > 0.99:
                            logger.info(f"Semantic duplicate found (score: {top_match['score']:.4f}) for user {user_id}, skipping insert.")
                            return top_match["id"]
                except Exception as e:
                    logger.warning(f"Semantic deduplication check failed: {e}")

            # Store similar_memories for potential conflict detection
            _similar_memories_for_conflict = similar_memories if similar_memories else []
            _top_match_score = similar_memories[0].get("score", 0.0) if similar_memories else 0.0

            # --- Phase 2: Fact Extraction (Slow / Costly) ---
            # Extract facts if requested
            content = messages
            if infer:
                logger.debug(f"Extracting facts for user {user_id}")
                facts = self.llm.extract_facts(messages, user_id)

                if facts:
                    # Use first fact as content, or original message
                    content = facts[0].get("fact", messages) if facts else messages
                else:
                    content = messages

                # Always embed the final content for storage (even if same as original)
                embedding_vector = self.embedding.embed(content)

                # If content changed after extraction, check semantic dedup on extracted content
                if content != messages:
                    try:
                        similar_after_extraction = self.vector_store.search(
                            query_vector=embedding_vector,
                            limit=1,
                            filters={"user_id": user_id}
                        )

                        if similar_after_extraction:
                            top_match = similar_after_extraction[0]
                            if top_match.get("score", 0.0) > 0.99:
                                logger.info(f"Semantic duplicate found after extraction (score: {top_match['score']:.4f}) for user {user_id}, skipping insert.")
                                return top_match["id"]
                    except Exception as e:
                        logger.warning(f"Semantic dedup check after extraction failed: {e}")

            # --- Phase 2.5: Conflict Detection (LLM-based) ---
            # Check for conflicts in the "gray zone" where semantic similarity is ambiguous
            if (_top_match_score >= self.SEMANTIC_GRAY_ZONE_MIN and
                _top_match_score <= self.SEMANTIC_GRAY_ZONE_MAX and
                _similar_memories_for_conflict):
                logger.debug(f"Gray zone detected (score: {_top_match_score:.4f}), running conflict detection")

                # Get top candidates for conflict checking
                candidates_for_conflict = _similar_memories_for_conflict[:5]
                existing_contents = [m.get("content", "") for m in candidates_for_conflict]

                # Use LLM to detect semantic conflicts
                try:
                    conflict_result = self.llm.detect_conflicts(content, existing_contents)

                    if conflict_result and conflict_result.get("has_conflict"):
                        conflicting_fact = conflict_result.get("conflicting_fact", "unknown")
                        conflict_reason = conflict_result.get("reason", "semantic contradiction")

                        logger.info(f"Conflict detected: '{content}' vs '{conflicting_fact}' - {conflict_reason}")

                        # Apply conflict resolution strategy
                        if self.conflict_strategy == self.STRATEGY_SKIP:
                            # Skip: don't insert conflicting memory
                            logger.info(f"Conflict strategy SKIP: not inserting conflicting memory for user {user_id}")
                            return candidates_for_conflict[0]["id"]
                        elif self.conflict_strategy == self.STRATEGY_KEEP_BOTH:
                            # Keep both: insert with conflict metadata
                            logger.info(f"Conflict strategy KEEP_BOTH: inserting with conflict metadata")
                            if metadata is None:
                                metadata = {}
                            metadata["has_conflict"] = True
                            metadata["conflict_with"] = conflicting_fact
                            metadata["conflict_reason"] = conflict_reason
                        elif self.conflict_strategy == self.STRATEGY_NEWER_WINS:
                            # Newer wins: insert normally, let newer info take precedence
                            # Add conflict metadata for transparency
                            logger.info(f"Conflict strategy NEWER_WINS: inserting newer memory")
                            if metadata is None:
                                metadata = {}
                            metadata["has_conflict"] = True
                            metadata["conflict_with"] = conflicting_fact
                            metadata["conflict_reason"] = conflict_reason
                            metadata["conflict_resolved"] = "newer_wins"
                        # Default: newer_wins
                except NotImplementedError:
                    # LLM doesn't support conflict detection, skip
                    logger.debug("LLM does not support detect_conflicts, skipping")
                except Exception as e:
                    logger.warning(f"Conflict detection failed: {e}, continuing with insert")

            # --- Phase 3: Persistence ---
            # Prepare payload
            if metadata is None:
                metadata = {}
            metadata["content_hash"] = content_hash
            metadata["timestamp"] = int(time.time())  # Add timestamp to metadata
            # Set default confidence if not provided
            if "confidence" not in metadata:
                metadata["confidence"] = 0.8
            
            payload = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata,
                "original_message": messages
            }

            # Compute BM25 vector
            content_terms = content.lower().split()
            bm25_vector = self.bm25_calculator.add_document(content_terms)

            # Insert into vector store
            logger.debug(f"Inserting into vector store: {memory_id}")
            self.vector_store.insert(
                vectors=[embedding_vector],
                payloads=[payload],
                ids=[memory_id],
                bm25_vectors=[bm25_vector]
            )
            
            # Defer entity extraction and graph building to background
            if infer:
                self._defer_entity_extraction(content, user_id)

            logger.info(f"Added memory {memory_id} for user {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise MemoryError(f"Failed to add memory: {e}")
    
    def _defer_entity_extraction(self, content: str, user_id: str) -> None:
        """Extract entities and build graph in a background thread."""
        graph_store = self.graph_store
        llm = self.llm
        graph_lock = self._graph_lock

        def _run():
            try:
                entities = llm.extract_entities(content)
                for entity_data in entities:
                    entity_name = entity_data.get("entity")
                    entity_type = entity_data.get("type", "UNKNOWN")
                    if not entity_name:
                        continue

                    with graph_lock:
                        graph_store.add_node(
                            entity=entity_name,
                            properties={"type": entity_type},
                            user_id=user_id
                        )
                        for rel in entity_data.get("relations", []):
                            target = rel.get("target")
                            if target:
                                graph_store.add_node(
                                    entity=target, properties={}, user_id=user_id
                                )
                                graph_store.add_relationship(
                                    source=entity_name,
                                    target=target,
                                    relation_type=rel.get("type", "RELATED_TO")
                                )
            except Exception as e:
                logger.warning(f"Background entity extraction failed: {e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def add_batch(
        self,
        messages: List[str],
        user_id: str
    ) -> List[str]:
        """
        Add multiple memories in batch.
        
        Args:
            messages: List of content to remember
            user_id: User ID
            
        Returns:
            List of memory IDs
        """
        try:
            logger.info(f"Adding {len(messages)} memories in batch")
            
            # Generate embeddings in batch
            embeddings = self.embedding.embed_batch(messages)
            
            # Generate memory IDs
            memory_ids = [str(uuid.uuid4()) for _ in range(len(messages))]
            
            # Prepare payloads
            payloads = [
                {
                    "user_id": user_id,
                    "content": msg,
                    "metadata": {},
                    "original_message": msg
                }
                for msg in messages
            ]
            
            # Batch insert into vector store
            self.vector_store.insert(
                vectors=embeddings,
                payloads=payloads,
                ids=memory_ids
            )
            
            logger.info(f"Batch added {len(memory_ids)} memories")
            return memory_ids
            
        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            raise MemoryError(f"Batch add failed: {e}")


class _MemoryReader:
    """Internal reader component - handles memory retrieval."""

    def __init__(
        self,
        embedding: EmbeddingBase,
        vector_store: VectorStoreBase,
        graph_store: GraphStoreBase,
        llm: LLMBase,
        bm25_calculator: Optional[BM25Calculator] = None
    ):
        self.embedding = embedding
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.llm = llm
        self.bm25_calculator = bm25_calculator or BM25Calculator()
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        use_graph: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search memories using parallel hybrid approach (vector + BM25 + optional graph).

        Args:
            query: Search query
            user_id: User ID
            limit: Maximum results
            use_graph: Whether to use graph expansion

        Returns:
            List of memories with scores
        """
        try:
            import concurrent.futures

            query_vector = None
            expanded_entities = []
            vector_results = []
            bm25_results = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Task 1: Generate Embedding
                logger.debug("Generating query embedding (async)")
                future_embed = executor.submit(self.embedding.embed, query)

                # Task 2: Entity Extraction (if enabled)
                future_entities = None
                if use_graph:
                    logger.debug("Extracting entities from query (async)")
                    future_entities = executor.submit(self.llm.extract_entities, query)

                # Task 3: BM25 Search (if available)
                future_bm25 = None
                if hasattr(self.vector_store, 'bm25_search'):
                    logger.debug("Running BM25 search (async)")
                    # Compute query vector using stored IDF
                    query_bm25_vector = self.bm25_calculator.compute_query_vector(query)
                    future_bm25 = executor.submit(
                        self.vector_store.bm25_search,
                        query_vector=query_bm25_vector,  # Pass precomputed vector
                        limit=limit * 2,
                        filters={"user_id": user_id}
                    )

                # Wait for embedding (fast)
                query_vector = future_embed.result()

                # Vector search immediately when embedding is ready
                logger.debug(f"Searching vector store for user {user_id}")
                search_limit = int(limit * 2.0)
                vector_results = self.vector_store.search(
                    query_vector=query_vector,
                    limit=search_limit,
                    filters={"user_id": user_id}
                )

                # Wait for BM25 results
                if future_bm25:
                    try:
                        bm25_results = future_bm25.result()
                    except Exception as e:
                        logger.warning(f"BM25 search failed, continuing without it: {e}")
                        bm25_results = []

                # Wait for entities (slow)
                if future_entities:
                    try:
                        entities = future_entities.result()
                        if entities:
                            entity_names = [e.get("entity") for e in entities if e.get("entity")]
                            if entity_names:
                                logger.debug(f"Expanding graph from entities: {entity_names}")
                                expanded_entities = self.graph_store.bfs_expand(
                                    entities=entity_names,
                                    depth=2,
                                    user_id=user_id
                                )
                    except Exception as e:
                        logger.warning(f"Graph expansion failed, continuing with vector results: {e}")

            # RRF Fusion: combine vector and BM25 results
            if bm25_results:
                logger.debug(f"Fusing {len(vector_results)} vector + {len(bm25_results)} BM25 results")
                fused_results = _reciprocal_rank_fusion([vector_results, bm25_results], k=60)
            else:
                fused_results = vector_results

            # Combine and score results
            results = []
            seen_content = set()

            for result in fused_results:
                content = result.get("content", "")

                # Simple deduplication by content hash (using MD5 for determinism)
                content_hash = hashlib.md5(content.strip().encode('utf-8')).hexdigest()
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                # Base score from vector similarity or fused score
                score = result.get("score", result.get("fused_score", 0.0))

                # Boost score if content mentions expanded entities
                if expanded_entities:
                    for entity in expanded_entities:
                        if entity.lower() in content.lower():
                            score += 0.1

                metadata = result.get("metadata", {})
                results.append({
                    "id": result.get("id"),
                    "content": content,
                    "score": min(score, 1.0),
                    "metadata": metadata,
                    "timestamp": metadata.get("timestamp"),  # Extract timestamp from metadata
                    "user_id": result.get("user_id"),
                    "created_at": result.get("created_at")
                })

            # Sort by combined score
            results.sort(key=lambda x: x["score"], reverse=True)

            logger.info(f"Found {len(results[:limit])} memories for query")
            return results[:limit]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise MemoryError(f"Search failed: {e}")
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        try:
            result = self.vector_store.get(memory_id)
            return result
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    def get_all(
        self, user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        try:
            results = self.vector_store.list(
                filters={"user_id": user_id},
                limit=limit,
                offset=offset
            )
            
            logger.info(f"Retrieved {len(results)} memories for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []


class _MemoryLifecycle:
    """Internal lifecycle component - handles memory management."""

    def __init__(
        self,
        vector_store: VectorStoreBase,
        graph_store: GraphStoreBase,
        decay_config: Optional[Any] = None,
        embedding: Optional[EmbeddingBase] = None
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedding = embedding
        self.decay_config = decay_config or {
            "strategy": "hybrid",
            "half_life_days": 30.0,
            "min_confidence": 0.1,
            "access_boost": 0.05
        }

    def _update_memory_payload(self, memory_id: str, memory: Dict[str, Any]) -> bool:
        """
        Update memory payload in a backend-compatible way.

        For SQLite, payload-only update usually succeeds.
        For Milvus-like backends that require full upsert (vector + payload),
        retry with re-embedded content if payload-only update fails.
        """
        updated = self.vector_store.update(vector_id=memory_id, payload=memory)
        if updated:
            return True

        if self.embedding is None:
            return False

        content = memory.get("content")
        if not content:
            return False

        try:
            vector = self.embedding.embed(content)
            return self.vector_store.update(
                vector_id=memory_id,
                vector=vector,
                payload=memory
            )
        except Exception as e:
            logger.error(f"Failed to re-embed memory {memory_id} for update: {e}")
            return False

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            # Delete from vector store
            deleted = self.vector_store.delete(memory_id)

            if deleted:
                logger.info(f"Deleted memory {memory_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def update(
        self,
        memory_id: str,
        new_content: str,
        embedding: EmbeddingBase
    ) -> bool:
        """Update a memory's content."""
        try:
            # Get existing memory
            existing = self.vector_store.get(memory_id)
            if not existing:
                return False

            # Generate new embedding
            new_embedding = embedding.embed(new_content)

            # Update payload
            payload = existing.copy()
            payload["content"] = new_content

            # Update in vector store
            updated = self.vector_store.update(
                vector_id=memory_id,
                vector=new_embedding,
                payload=payload
            )

            if updated:
                logger.info(f"Updated memory {memory_id}")

            return updated

        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False

    def apply_decay(self, user_id: str) -> Dict[str, Any]:
        """
        Apply confidence decay to all memories for a user.

        Returns:
            Dict with statistics about the decay operation
        """
        from .utils import (
            calculate_time_decayed_confidence,
            calculate_access_decayed_confidence,
            calculate_hybrid_confidence
        )

        try:
            decayed_count = 0
            forgotten_count = 0
            total_checked = 0
            strategy = self.decay_config.get("strategy", "hybrid")
            half_life = self.decay_config.get("half_life_days", 30.0)
            min_conf = self.decay_config.get("min_confidence", 0.1)
            access_boost = self.decay_config.get("access_boost", 0.05)
            batch_size = 500
            offset = 0

            while True:
                batch = self.vector_store.list(
                    filters={"user_id": user_id},
                    limit=batch_size,
                    offset=offset
                )
                if not batch:
                    break
                total_checked += len(batch)
                offset += len(batch)

                for memory in batch:
                    memory_id = memory.get("id")
                    metadata = memory.get("metadata", {})

                    current_conf = metadata.get("confidence", 0.8)
                    created_at = metadata.get("timestamp", int(time.time()))
                    access_count = metadata.get("access_count", 0)
                    last_accessed = metadata.get("last_accessed_at")

                    if strategy == "time_decay":
                        new_conf = calculate_time_decayed_confidence(
                            current_conf, created_at, half_life, min_conf
                        )
                    elif strategy == "access_decay":
                        new_conf = calculate_access_decayed_confidence(
                            current_conf, access_count, last_accessed,
                            access_boost, half_life, min_conf
                        )
                    else:
                        new_conf = calculate_hybrid_confidence(
                            current_conf, created_at, access_count,
                            last_accessed, half_life, min_conf, access_boost
                        )

                    if new_conf != current_conf:
                        metadata["confidence"] = round(new_conf, 4)
                        metadata["decayed_at"] = int(time.time())
                        if self._update_memory_payload(memory_id, memory):
                            decayed_count += 1

                    if new_conf <= min_conf:
                        metadata["status"] = "archived"
                        metadata["forgotten_at"] = int(time.time())
                        metadata["forget_reason"] = "confidence_below_threshold"
                        if self._update_memory_payload(memory_id, memory):
                            forgotten_count += 1
                            logger.info(f"Memory {memory_id} forgotten ({new_conf:.4f})")

            logger.info(
                f"Decay applied to {decayed_count} memories, "
                f"forgotten {forgotten_count} memories for user {user_id}"
            )

            return {
                "decayed_count": decayed_count,
                "forgotten_count": forgotten_count,
                "strategy": strategy,
                "total_checked": total_checked
            }

        except Exception as e:
            logger.error(f"Failed to apply decay: {e}")
            raise MemoryError(f"Decay operation failed: {e}")

    def cleanup_forgotten(self, user_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Permanently delete memories that have been forgotten for a long time.

        Args:
            user_id: User ID
            dry_run: If True, only count without deleting

        Returns:
            Dict with cleanup statistics
        """
        try:
            current_time = int(time.time())
            cleanup_threshold_days = 7
            cleanup_threshold = cleanup_threshold_days * 24 * 3600
            cleaned_count = 0
            batch_size = 500
            offset = 0

            while True:
                batch = self.vector_store.list(
                    filters={"user_id": user_id},
                    limit=batch_size,
                    offset=offset
                )
                if not batch:
                    break
                offset += len(batch)

                for memory in batch:
                    metadata = memory.get("metadata", {})
                    forgotten_at = metadata.get("forgotten_at")
                    if not forgotten_at:
                        continue
                    if (current_time - forgotten_at) <= cleanup_threshold:
                        continue

                    memory_id = memory.get("id")
                    if not dry_run:
                        self.vector_store.delete(memory_id)
                    cleaned_count += 1

            logger.info(
                f"Cleaned up {cleaned_count} forgotten memories for user {user_id}"
            )

            return {
                "cleaned_count": cleaned_count,
                "dry_run": dry_run,
                "threshold_days": cleanup_threshold_days
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise MemoryError(f"Cleanup operation failed: {e}")

    def boost_confidence(self, memory_id: str, boost: float = 0.05) -> bool:
        """
        Boost confidence of a memory (e.g., when accessed).

        Args:
            memory_id: Memory ID
            boost: Amount to boost confidence by

        Returns:
            True if updated successfully
        """
        try:
            memory = self.vector_store.get(memory_id)
            if not memory:
                return False

            metadata = memory.get("metadata", {})
            current_conf = metadata.get("confidence", 0.8)

            # Boost confidence (cap at 1.0)
            new_conf = min(1.0, current_conf + boost)
            metadata["confidence"] = round(new_conf, 4)
            metadata["access_count"] = metadata.get("access_count", 0) + 1
            metadata["last_accessed_at"] = int(time.time())

            updated = self._update_memory_payload(memory_id, memory)
            if not updated:
                return False

            logger.debug(f"Boosted confidence of memory {memory_id} to {new_conf:.4f}")
            return True

        except Exception as e:
            logger.error(f"Failed to boost confidence for {memory_id}: {e}")
            return False
