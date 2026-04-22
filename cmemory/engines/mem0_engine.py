"""Mem0 memory engine adapter."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from ..core.base import BaseMemoryEngine


class Mem0Engine(BaseMemoryEngine):
    """
    Mem0 memory engine adapter.

    Wraps the mem0ai library to provide unified interface
    for memory framework comparison.
    """

    engine_name = "mem0"

    def __init__(
        self,
        user_id: str = "default",
        *,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        super().__init__(user_id=user_id, **kwargs)

        self._memory_client = None
        self._config = config or self._default_config()

        # Initialize client lazily
        self._initialized = False

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for Mem0."""
        return {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": f"mem0_{self.user_id}",
                    "embedding_model_dims": int(os.getenv("EMBEDDING_DIMS", "1536")),
                    "path": os.getenv("VECTOR_STORE_PATH", ".memory_data/qdrant"),
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": os.getenv("QA_MODEL", "gpt-4o-mini"),
                },
            },
        }

    def _ensure_initialized(self) -> None:
        """Lazily initialize the Mem0 client."""
        if self._initialized:
            return

        try:
            from mem0 import Memory

            self._memory_client = Memory.from_config(self._config)
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Mem0: {e}") from e

    def add(
        self,
        content: str,
        *,
        role: str = "user",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a single memory entry."""
        self._ensure_initialized()

        start_time = time.time()

        # Prepare metadata
        meta = metadata or {}
        if timestamp:
            meta["timestamp"] = timestamp.isoformat()
        meta["role"] = role

        # Add to Mem0
        result = self._memory_client.add(
            content,
            user_id=self.user_id,
            metadata=meta,
        )

        elapsed = time.time() - start_time
        self._record_add_stats(time_seconds=elapsed)

        # Extract memory ID from result
        if isinstance(result, dict):
            results = result.get("results", [])
            if results:
                return results[0].get("id", "unknown")
        elif isinstance(result, list) and result:
            return result[0].get("id", "unknown")

        return "unknown"

    def add_batch(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        timestamps: Optional[Sequence[datetime]] = None,
    ) -> List[str]:
        """Add multiple messages in batch."""
        ids = []
        for i, msg in enumerate(messages):
            ts = timestamps[i] if timestamps and i < len(timestamps) else None
            id_ = self.add(
                msg.get("content", ""),
                role=msg.get("role", "user"),
                timestamp=ts,
            )
            ids.append(id_)
        return ids

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories."""
        self._ensure_initialized()

        start_time = time.time()

        result = self._memory_client.search(
            query,
            filters={"user_id": self.user_id},
            limit=limit,
        )

        elapsed = time.time() - start_time
        self._record_search_stats(time_seconds=elapsed)

        # Normalize results
        results = []
        if isinstance(result, dict):
            memories = result.get("results", result.get("memories", []))
        elif isinstance(result, list):
            memories = result
        else:
            memories = []

        for mem in memories:
            results.append({
                "content": mem.get("memory", mem.get("content", "")),
                "score": mem.get("score", 1.0),
                "memory_id": mem.get("id"),
                "metadata": mem.get("metadata", {}),
            })

        return results

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        self._ensure_initialized()

        # Mem0 doesn't have direct get by ID, use get_all and filter
        all_memories = self._memory_client.get_all(filters={"user_id": self.user_id})

        if isinstance(all_memories, dict):
            memories = all_memories.get("results", [])
        else:
            memories = all_memories

        for mem in memories:
            if mem.get("id") == memory_id:
                return {
                    "content": mem.get("memory", ""),
                    "memory_id": memory_id,
                    "metadata": mem.get("metadata", {}),
                }

        return None

    def update(
        self,
        memory_id: str,
        *,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing memory."""
        self._ensure_initialized()

        if content:
            self._memory_client.update(memory_id, content)
            self.stats.update_calls += 1
            return True
        return False

    def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        self._ensure_initialized()

        self._memory_client.delete(memory_id)
        return True

    def clear(self) -> None:
        """Clear all memories for this user."""
        self._ensure_initialized()

        self._memory_client.delete_all(user_id=self.user_id)

    def save(self) -> None:
        """Persist memory state (Mem0 handles this internally)."""
        # Mem0 persists automatically with on_disk config
        pass

    def load(self) -> bool:
        """Load persisted memory state."""
        self._ensure_initialized()

        # Check if any memories exist
        all_memories = self._memory_client.get_all(filters={"user_id": self.user_id})
        if isinstance(all_memories, dict):
            count = len(all_memories.get("results", []))
        else:
            count = len(all_memories) if all_memories else 0

        self.stats.memory_count = count
        return count > 0