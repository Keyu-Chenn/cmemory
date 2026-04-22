"""Base memory engine interface for framework comparison."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class EngineStats:
    """Statistics collected during engine operations."""

    # Token consumption
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # API calls
    add_calls: int = 0
    search_calls: int = 0
    update_calls: int = 0

    # Time tracking
    add_time_seconds: float = 0.0
    search_time_seconds: float = 0.0
    total_time_seconds: float = 0.0

    # Memory stats
    memory_count: int = 0
    storage_size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
                "total": self.total_tokens,
            },
            "api_calls": {
                "add": self.add_calls,
                "search": self.search_calls,
                "update": self.update_calls,
            },
            "time_seconds": {
                "add": self.add_time_seconds,
                "search": self.search_time_seconds,
                "total": self.total_time_seconds,
            },
            "memory": {
                "count": self.memory_count,
                "storage_bytes": self.storage_size_bytes,
            },
        }


class BaseMemoryEngine(ABC):
    """
    Abstract base class for memory engines.

    Provides a unified interface for different memory frameworks
    (Mem0, Zep, Letta/MemGPT, etc.) to enable fair comparison.
    """

    engine_name: str = "base"

    def __init__(self, user_id: str = "default", **kwargs) -> None:
        self.user_id = user_id
        self.config = kwargs
        self.stats = EngineStats()

    @abstractmethod
    def add(
        self,
        content: str,
        *,
        role: str = "user",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a single memory entry.

        Args:
            content: The text content to remember.
            role: Speaker role (user/assistant/system).
            timestamp: When this occurred.
            metadata: Additional metadata.

        Returns:
            Memory ID of the added entry.
        """
        pass

    @abstractmethod
    def add_batch(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        timestamps: Optional[Sequence[datetime]] = None,
    ) -> List[str]:
        """
        Add multiple messages in batch.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            timestamps: Optional timestamps for each message.

        Returns:
            List of memory IDs.
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories.

        Args:
            query: Search query text.
            limit: Maximum results to return.
            filters: Optional filters (e.g., time range, role).

        Returns:
            List of search results with 'content', 'score', 'metadata'.
        """
        pass

    @abstractmethod
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: The memory identifier.

        Returns:
            Memory dict or None if not found.
        """
        pass

    @abstractmethod
    def update(
        self,
        memory_id: str,
        *,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing memory.

        Args:
            memory_id: The memory to update.
            content: New content (optional).
            metadata: New/updated metadata (optional).

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: The memory to delete.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all memories for this user."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Persist memory state to storage."""
        pass

    @abstractmethod
    def load(self) -> bool:
        """
        Load persisted memory state.

        Returns:
            True if loaded successfully, False if no saved state.
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get collected statistics."""
        return self.stats.to_dict()

    def reset_stats(self) -> None:
        """Reset all statistics to zero."""
        self.stats = EngineStats()

    def _record_add_stats(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        time_seconds: float = 0.0,
    ) -> None:
        """Helper to record add operation stats."""
        self.stats.add_calls += 1
        self.stats.prompt_tokens += prompt_tokens
        self.stats.completion_tokens += completion_tokens
        self.stats.total_tokens += prompt_tokens + completion_tokens
        self.stats.add_time_seconds += time_seconds
        self.stats.total_time_seconds += time_seconds

    def _record_search_stats(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        time_seconds: float = 0.0,
    ) -> None:
        """Helper to record search operation stats."""
        self.stats.search_calls += 1
        self.stats.prompt_tokens += prompt_tokens
        self.stats.completion_tokens += completion_tokens
        self.stats.total_tokens += prompt_tokens + completion_tokens
        self.stats.search_time_seconds += time_seconds
        self.stats.total_time_seconds += time_seconds