"""Data models for memory comparison framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now()


@dataclass
class Message:
    """A single message in a conversation."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Session:
    """A conversation session containing multiple messages."""

    session_id: str
    messages: Tuple[Message, ...] = ()
    timestamp: datetime = field(default_factory=utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Trajectory:
    """A trajectory containing multiple sessions over time."""

    trajectory_id: str
    sessions: Tuple[Session, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.sessions)

    def __iter__(self):
        return iter(self.sessions)

    def total_messages(self) -> int:
        return sum(len(s) for s in self.sessions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "sessions": [s.to_dict() for s in self.sessions],
            "metadata": self.metadata,
        }


@dataclass
class QuestionAnswerPair:
    """A question and its expected answer(s)."""

    question: str
    answers: Tuple[str, ...]  # Multiple acceptable answers
    timestamp: datetime = field(default_factory=utcnow)
    question_type: str = "normal"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single search result from memory retrieval."""

    content: str
    score: float
    memory_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "score": self.score,
            "memory_id": self.memory_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    """Results from memory retrieval for a question."""

    question: str
    retrieved_memories: List[SearchResult]
    engine_name: str
    retrieval_time_seconds: float = 0.0


@dataclass
class QAResult:
    """Result from QA evaluation."""

    question: str
    expected_answers: Tuple[str, ...]
    generated_answer: str
    retrieved_context: str  # Memories used as context
    is_correct: bool
    judge_reasoning: Optional[str] = None
    confidence: float = 1.0


@dataclass
class EngineEvaluation:
    """Evaluation results for a single engine."""

    engine_name: str
    qa_results: List[QAResult]
    retrieval_results: List[RetrievalResult]
    stats: Dict[str, Any]

    # Aggregated metrics
    accuracy: float = 0.0
    retrieval_recall: float = 0.0
    total_tokens: int = 0
    total_time_seconds: float = 0.0

    def compute_accuracy(self) -> float:
        """Compute overall accuracy from QA results."""
        if not self.qa_results:
            return 0.0
        correct = sum(1 for r in self.qa_results if r.is_correct)
        self.accuracy = correct / len(self.qa_results)
        return self.accuracy


@dataclass
class EvaluationResult:
    """Complete evaluation results across all engines."""

    dataset_name: str
    engine_results: Dict[str, EngineEvaluation]
    evaluation_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_comparison_table(self) -> Dict[str, Dict[str, Any]]:
        """Get a comparison table of all engines."""
        return {
            name: {
                "accuracy": result.accuracy,
                "total_tokens": result.stats.get("tokens", {}).get("total", 0),
                "total_time_seconds": result.stats.get("time_seconds", {}).get("total", 0),
                "api_calls": sum(
                    result.stats.get("api_calls", {}).values()
                ),
                "memory_count": result.stats.get("memory", {}).get("count", 0),
            }
            for name, result in self.engine_results.items()
        }