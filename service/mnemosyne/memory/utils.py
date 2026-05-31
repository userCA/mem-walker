"""Utility functions for memory module."""

import math
import time
from typing import Any, Dict, List, Optional


def generate_timestamp() -> int:
    """Generate current Unix timestamp."""
    return int(time.time())


def calculate_recency_score(created_at: int, decay_factor: float = 0.1) -> float:
    """
    Calculate recency score for a memory.

    Args:
        created_at: Unix timestamp when memory was created
        decay_factor: How fast the score decays (0.0 = no decay, 1.0 = fast decay)

    Returns:
        Recency score between 0.0 and 1.0
    """
    current_time = generate_timestamp()
    age_days = (current_time - created_at) / (24 * 3600)

    # Exponential decay
    score = 1.0 / (1.0 + decay_factor * age_days)

    return score


def calculate_time_decayed_confidence(
    initial_confidence: float,
    created_at: int,
    half_life_days: float = 30.0,
    min_confidence: float = 0.1
) -> float:
    """
    Calculate confidence after time-based decay.

    Uses exponential decay: C(t) = C0 * (1/2)^(t/t_half)

    Args:
        initial_confidence: Starting confidence value (0.0-1.0)
        created_at: Unix timestamp when memory was created
        half_life_days: Days for confidence to reduce by half
        min_confidence: Minimum confidence floor

    Returns:
        Decayed confidence value
    """
    if half_life_days <= 0:
        return initial_confidence

    current_time = generate_timestamp()
    age_days = (current_time - created_at) / (24 * 3600)

    # Exponential decay formula
    decay_ratio = math.pow(0.5, age_days / half_life_days)
    decayed = initial_confidence * decay_ratio

    # Apply floor
    return max(decayed, min_confidence)


def calculate_access_decayed_confidence(
    current_confidence: float,
    access_count: int,
    last_accessed_at: Optional[int],
    access_boost: float = 0.05,
    half_life_days: float = 30.0,
    min_confidence: float = 0.1
) -> float:
    """
    Calculate confidence with access-based adjustments.

    Memories that are accessed more frequently decay slower.
    Each access boosts confidence slightly.

    Args:
        current_confidence: Current confidence value
        access_count: Number of times memory was accessed
        last_accessed_at: Unix timestamp of last access
        access_boost: Confidence boost per access
        half_life_days: Base half-life for decay
        min_confidence: Minimum confidence floor

    Returns:
        Adjusted confidence value
    """
    # Boost from access frequency (diminishing returns)
    access_bonus = access_boost * math.log1p(access_count)

    if last_accessed_at:
        current_time = generate_timestamp()
        days_since_access = (current_time - last_accessed_at) / (24 * 3600)

        # Extend half-life based on access recency
        # Recently accessed memories have longer half-life
        access_recency_bonus = max(0, 1.0 - days_since_access / half_life_days)
        effective_half_life = half_life_days * (1 + access_recency_bonus)

        # Recalculate decay with adjusted half-life
        decay_ratio = math.pow(0.5, days_since_access / effective_half_life)
        decayed = (current_confidence + access_bonus) * decay_ratio
    else:
        # Never accessed - apply standard decay
        decayed = current_confidence

    return max(min(decayed, 1.0), min_confidence)


def calculate_hybrid_confidence(
    initial_confidence: float,
    created_at: int,
    access_count: int = 0,
    last_accessed_at: Optional[int] = None,
    half_life_days: float = 30.0,
    min_confidence: float = 0.1,
    access_boost: float = 0.05
) -> float:
    """
    Calculate confidence using hybrid decay (time + access patterns).

    Args:
        initial_confidence: Starting confidence value
        created_at: Unix timestamp when memory was created
        access_count: Number of times memory was accessed
        last_accessed_at: Unix timestamp of last access
        half_life_days: Days for confidence to halve
        min_confidence: Minimum confidence floor
        access_boost: Confidence boost per access

    Returns:
        Decayed confidence value
    """
    # Start with time decay
    time_decayed = calculate_time_decayed_confidence(
        initial_confidence, created_at, half_life_days, min_confidence
    )

    # Apply access-based adjustments
    access_adjusted = calculate_access_decayed_confidence(
        time_decayed, access_count, last_accessed_at,
        access_boost, half_life_days, min_confidence
    )

    return access_adjusted


def should_forget_memory(
    confidence: float,
    threshold: float = 0.2,
    strategy: str = "threshold"
) -> bool:
    """
    Determine if a memory should be forgotten based on confidence.

    Args:
        confidence: Current confidence value
        threshold: Forgetting threshold
        strategy: Forgetting strategy ("threshold", "probabilistic")

    Returns:
        True if memory should be forgotten
    """
    import random

    if strategy == "threshold":
        return confidence < threshold
    elif strategy == "probabilistic":
        # Higher chance of forgetting as confidence decreases
        forget_probability = max(0, 1.0 - confidence / threshold)
        return random.random() < forget_probability

    return False


def format_memory_result(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format memory result for user consumption.

    Args:
        memory: Raw memory data

    Returns:
        Formatted memory dictionary
    """
    metadata = memory.get("metadata", {})
    return {
        "id": memory.get("id"),
        "content": memory.get("content"),
        "score": round(memory.get("score", 0.0), 4),
        "metadata": metadata,
        "timestamp": metadata.get("timestamp"),  # Extract timestamp from metadata
        "created_at": memory.get("created_at"),
        "user_id": memory.get("user_id")
    }
