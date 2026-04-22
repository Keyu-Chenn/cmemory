"""Tests for core module."""

import pytest
from datetime import datetime

from cmemory.core.base import BaseMemoryEngine, EngineStats
from cmemory.core.models import Message, Session, Trajectory, SearchResult


class TestModels:
    """Tests for data models."""

    def test_message_creation(self):
        msg = Message(
            role="user",
            content="Hello",
            timestamp=datetime(2024, 1, 1, 10, 0),
        )
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.to_dict()["role"] == "user"

    def test_session_creation(self):
        msg1 = Message(role="user", content="Hello")
        msg2 = Message(role="assistant", content="Hi there")
        session = Session(
            session_id="test-1",
            messages=(msg1, msg2),
        )
        assert len(session) == 2
        assert session.session_id == "test-1"

    def test_trajectory_creation(self):
        session = Session(
            session_id="test-1",
            messages=(Message(role="user", content="Test"),),
        )
        traj = Trajectory(
            trajectory_id="traj-1",
            sessions=(session,),
        )
        assert len(traj) == 1
        assert traj.total_messages() == 1

    def test_engine_stats(self):
        stats = EngineStats(
            prompt_tokens=100,
            completion_tokens=50,
            add_calls=5,
        )
        d = stats.to_dict()
        assert d["tokens"]["prompt"] == 100
        assert d["api_calls"]["add"] == 5


class TestSearchResult:
    """Tests for SearchResult."""

    def test_search_result_creation(self):
        result = SearchResult(
            content="Test memory",
            score=0.95,
            memory_id="mem-1",
        )
        assert result.content == "Test memory"
        assert result.score == 0.95
        d = result.to_dict()
        assert d["content"] == "Test memory"