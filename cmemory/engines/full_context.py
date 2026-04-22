"""Full context engine - baseline with complete history."""

from __future__ import annotations

import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..core.base import BaseMemoryEngine


class FullContextEngine(BaseMemoryEngine):
    """
    Full context engine that stores all messages without any memory processing.

    This serves as a baseline for comparison - it simply retrieves all
    stored messages as context, simulating a system without memory abstraction.
    """

    engine_name = "full_context"

    def __init__(
        self,
        user_id: str = "default",
        *,
        save_dir: Optional[str] = None,
        max_context_tokens: int = 100000,
        **kwargs,
    ) -> None:
        super().__init__(user_id=user_id, **kwargs)

        self._save_dir = Path(save_dir or f".memory_data/{self.user_id}")
        self._max_context_tokens = max_context_tokens

        # In-memory storage
        self._messages: List[Dict[str, Any]] = []
        self._message_counter = 0

    def add(
        self,
        content: str,
        *,
        role: str = "user",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a single message."""
        start_time = time.time()

        self._message_counter += 1
        msg_id = f"msg-{self._message_counter}"

        msg = {
            "id": msg_id,
            "content": content,
            "role": role,
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "metadata": metadata or {},
        }

        self._messages.append(msg)
        self.stats.memory_count = len(self._messages)

        elapsed = time.time() - start_time
        self._record_add_stats(time_seconds=elapsed)

        return msg_id

    def add_batch(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        timestamps: Optional[Sequence[datetime]] = None,
    ) -> List[str]:
        """Add multiple messages."""
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
        """
        Return all messages as context (no actual search).

        For full context baseline, we return all stored messages
        since there's no memory abstraction layer.
        """
        start_time = time.time()

        # Return all messages (reversed for recency)
        results = []
        for msg in reversed(self._messages[:limit]):
            results.append({
                "content": msg["content"],
                "score": 1.0,  # No scoring for full context
                "memory_id": msg["id"],
                "timestamp": msg["timestamp"],
                "metadata": msg["metadata"],
            })

        elapsed = time.time() - start_time
        self._record_search_stats(time_seconds=elapsed)

        return results

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID."""
        for msg in self._messages:
            if msg["id"] == memory_id:
                return {
                    "content": msg["content"],
                    "memory_id": memory_id,
                    "timestamp": msg["timestamp"],
                    "metadata": msg["metadata"],
                }
        return None

    def update(
        self,
        memory_id: str,
        *,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a message."""
        for msg in self._messages:
            if msg["id"] == memory_id:
                if content:
                    msg["content"] = content
                if metadata:
                    msg["metadata"].update(metadata)
                self.stats.update_calls += 1
                return True
        return False

    def delete(self, memory_id: str) -> bool:
        """Delete a message."""
        for i, msg in enumerate(self._messages):
            if msg["id"] == memory_id:
                self._messages.pop(i)
                self.stats.memory_count = len(self._messages)
                return True
        return False

    def clear(self) -> None:
        """Clear all messages."""
        self._messages = []
        self._message_counter = 0
        self.stats.memory_count = 0

    def save(self) -> None:
        """Save messages to disk."""
        self._save_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "messages": self._messages,
            "counter": self._message_counter,
            "user_id": self.user_id,
        }

        save_path = self._save_dir / "full_context.pkl"
        with open(save_path, "wb") as f:
            pickle.dump(data, f)

    def load(self) -> bool:
        """Load messages from disk."""
        save_path = self._save_dir / "full_context.pkl"

        if not save_path.exists():
            return False

        with open(save_path, "rb") as f:
            data = pickle.load(f)

        self._messages = data.get("messages", [])
        self._message_counter = data.get("counter", 0)

        self.stats.memory_count = len(self._messages)
        return len(self._messages) > 0

    def get_all_context(self) -> str:
        """Get all messages as a single context string."""
        lines = []
        for msg in self._messages:
            ts = msg.get("timestamp", "")
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"[{ts}] {role}: {content}")
        return "\n".join(lines)