"""Tests for FullContextEngine."""

import pytest
from datetime import datetime

from cmemory.engines.full_context import FullContextEngine
from cmemory.core.models import Message


class TestFullContextEngine:
    """Tests for FullContextEngine."""

    def test_add_and_search(self):
        engine = FullContextEngine(user_id="test_user")

        # Add messages
        id1 = engine.add("我喜欢苹果", role="user")
        id2 = engine.add("好的，记住了", role="assistant")

        assert id1.startswith("msg-")
        assert engine.stats.memory_count == 2

        # Search returns all messages (reversed order - most recent first)
        results = engine.search("苹果", limit=10)
        assert len(results) == 2
        # Check that at least one result contains "苹果"
        has_apple = any("苹果" in r["content"] for r in results)
        assert has_apple

    def test_get_and_delete(self):
        engine = FullContextEngine(user_id="test_user")

        id1 = engine.add("Test message")

        # Get by ID
        msg = engine.get(id1)
        assert msg is not None
        assert msg["content"] == "Test message"

        # Delete
        success = engine.delete(id1)
        assert success
        assert engine.stats.memory_count == 0

        # Get returns None after delete
        msg = engine.get(id1)
        assert msg is None

    def test_save_and_load(self):
        engine = FullContextEngine(
            user_id="test_user_2",
            save_dir=".memory_data/test_user_2",
        )

        engine.add("Saved message 1")
        engine.add("Saved message 2")
        engine.save()

        # Create new engine and load
        engine2 = FullContextEngine(
            user_id="test_user_2",
            save_dir=".memory_data/test_user_2",
        )
        success = engine2.load()
        assert success
        assert engine2.stats.memory_count == 2

        # Cleanup
        engine2.clear()

    def test_stats_tracking(self):
        engine = FullContextEngine(user_id="test_user")

        engine.add("Message 1")
        engine.add("Message 2")
        engine.search("test")

        stats = engine.get_stats()
        assert stats["api_calls"]["add"] == 2
        assert stats["api_calls"]["search"] == 1
        assert stats["memory"]["count"] == 2

    def test_clear(self):
        engine = FullContextEngine(user_id="test_user")

        engine.add("Message 1")
        engine.add("Message 2")
        engine.clear()

        assert engine.stats.memory_count == 0
        results = engine.search("test")
        assert len(results) == 0