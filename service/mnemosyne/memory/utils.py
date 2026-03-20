"""Utility functions for memory module."""

import time
from typing import Any, Dict


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


def format_memory_result(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format memory result for user consumption.
    
    Args:
        memory: Raw memory data
        
    Returns:
        Formatted memory dictionary
    """
    return {
        "id": memory.get("id"),
        "content": memory.get("content"),
        "score": round(memory.get("score", 0.0), 4),
        "metadata": memory.get("metadata", {}),
        "created_at": memory.get("created_at"),
        "user_id": memory.get("user_id")
    }
