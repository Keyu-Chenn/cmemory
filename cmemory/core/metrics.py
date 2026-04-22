"""Metrics collection for memory framework comparison."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


@dataclass
class TokenUsage:
    """Token usage for a single operation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt": self.prompt_tokens,
            "completion": self.completion_tokens,
            "total": self.total_tokens,
        }


@dataclass
class TimingRecord:
    """Timing record for an operation."""

    operation: str
    start_time: float
    end_time: float
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class MetricsCollector:
    """Collector for all metrics during evaluation."""

    # Token tracking per engine
    engine_tokens: Dict[str, TokenUsage] = field(default_factory=dict)

    # Timing records per engine
    engine_timings: Dict[str, List[TimingRecord]] = field(default_factory=dict)

    # API call counts per engine
    engine_calls: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Accuracy results per engine
    engine_accuracy: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize empty dicts for tracked engines."""
        pass

    def register_engine(self, engine_name: str) -> None:
        """Register a new engine for tracking."""
        if engine_name not in self.engine_tokens:
            self.engine_tokens[engine_name] = TokenUsage()
        if engine_name not in self.engine_timings:
            self.engine_timings[engine_name] = []
        if engine_name not in self.engine_calls:
            self.engine_calls[engine_name] = {
                "add": 0,
                "search": 0,
                "update": 0,
                "delete": 0,
            }
        if engine_name not in self.engine_accuracy:
            self.engine_accuracy[engine_name] = {
                "correct": 0,
                "total": 0,
                "accuracy": 0.0,
            }

    def record_tokens(
        self,
        engine_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Record token usage for an engine."""
        self.register_engine(engine_name)
        usage = self.engine_tokens[engine_name]
        usage.prompt_tokens += prompt_tokens
        usage.completion_tokens += completion_tokens
        usage.total_tokens += prompt_tokens + completion_tokens

    def record_call(self, engine_name: str, operation: str) -> None:
        """Record an API call for an engine."""
        self.register_engine(engine_name)
        if operation in self.engine_calls[engine_name]:
            self.engine_calls[engine_name][operation] += 1

    @contextmanager
    def track_time(self, engine_name: str, operation: str):
        """Context manager to track operation time."""
        self.register_engine(engine_name)
        start = time.time()
        yield
        end = time.time()
        record = TimingRecord(
            operation=operation,
            start_time=start,
            end_time=end,
            duration_seconds=end - start,
        )
        self.engine_timings[engine_name].append(record)

    def record_accuracy(
        self,
        engine_name: str,
        is_correct: bool,
        question_type: Optional[str] = None,
    ) -> None:
        """Record an accuracy result."""
        self.register_engine(engine_name)
        acc = self.engine_accuracy[engine_name]
        acc["total"] += 1
        if is_correct:
            acc["correct"] += 1
        acc["accuracy"] = acc["correct"] / acc["total"] if acc["total"] > 0 else 0.0

        if question_type:
            type_key = f"accuracy_{question_type}"
            if type_key not in acc:
                acc[type_key] = {"correct": 0, "total": 0}
            acc[type_key]["total"] += 1
            if is_correct:
                acc[type_key]["correct"] += 1

    def get_summary(self, engine_name: str) -> Dict[str, Any]:
        """Get summary metrics for an engine."""
        self.register_engine(engine_name)

        timings = self.engine_timings.get(engine_name, [])
        total_time = sum(t.duration_seconds for t in timings)

        return {
            "tokens": self.engine_tokens.get(engine_name, TokenUsage()).to_dict(),
            "calls": self.engine_calls.get(engine_name, {}),
            "timing": {
                "total_seconds": total_time,
                "operations": [t.to_dict() for t in timings],
            },
            "accuracy": self.engine_accuracy.get(engine_name, {}),
        }

    def get_comparison_report(self) -> Dict[str, Dict[str, Any]]:
        """Get comparison report across all engines."""
        return {
            name: self.get_summary(name)
            for name in self.engine_tokens.keys()
        }


class TokenMonitor:
    """
    Token usage monitor using monkey-patching approach.
    Inspired by LightMem's token_monitor.py.
    """

    _original_create: Optional[Any] = None
    _tracked_usage: Dict[str, List[TokenUsage]] = {}

    @classmethod
    def start_tracking(cls, engine_name: str = "default") -> None:
        """Start tracking token usage for API calls."""
        if engine_name not in cls._tracked_usage:
            cls._tracked_usage[engine_name] = []

        # Monkey-patch OpenAI client if available
        try:
            from openai import OpenAI
            if cls._original_create is None:
                cls._original_create = OpenAI.chat.completions.create

                def tracked_create(self, *args, **kwargs):
                    response = cls._original_create(self, *args, **kwargs)
                    if hasattr(response, "usage"):
                        usage = TokenUsage(
                            prompt_tokens=response.usage.prompt_tokens,
                            completion_tokens=response.usage.completion_tokens,
                            total_tokens=response.usage.total_tokens,
                        )
                        cls._tracked_usage[engine_name].append(usage)
                    return response

                OpenAI.chat.completions.create = tracked_create
        except ImportError:
            pass

    @classmethod
    def stop_tracking(cls) -> None:
        """Stop tracking and restore original method."""
        if cls._original_create is not None:
            try:
                from openai import OpenAI
                OpenAI.chat.completions.create = cls._original_create
                cls._original_create = None
            except ImportError:
                pass

    @classmethod
    def get_usage(cls, engine_name: str) -> TokenUsage:
        """Get total token usage for an engine."""
        usages = cls._tracked_usage.get(engine_name, [])
        total = TokenUsage()
        for u in usages:
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.total_tokens += u.total_tokens
        return total

    @classmethod
    def reset(cls, engine_name: Optional[str] = None) -> None:
        """Reset tracked usage."""
        if engine_name:
            cls._tracked_usage[engine_name] = []
        else:
            cls._tracked_usage = {}