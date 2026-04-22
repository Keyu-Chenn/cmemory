"""Base dataset class for memory evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from ..core.models import Trajectory, QuestionAnswerPair


@dataclass
class MemoryDataset(ABC):
    """
    Abstract base class for memory evaluation datasets.

    A dataset consists of:
    - Trajectories: Conversation histories to feed into memory systems
    - QA pairs: Questions and expected answers to evaluate memory retrieval
    """

    name: str = "base"
    trajectories: List[Trajectory] = field(default_factory=list)
    qa_pairs: List[QuestionAnswerPair] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if not self.metadata:
            self.metadata = self._generate_metadata()

    def __len__(self) -> int:
        return len(self.trajectories)

    def __iter__(self):
        return iter(zip(self.trajectories, self.qa_pairs))

    def __getitem__(self, index: int) -> Tuple[Trajectory, QuestionAnswerPair]:
        return self.trajectories[index], self.qa_pairs[index]

    @abstractmethod
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate dataset metadata."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        return {
            "name": self.name,
            "num_trajectories": len(self.trajectories),
            "num_questions": len(self.qa_pairs),
            "total_messages": sum(t.total_messages() for t in self.trajectories),
            "metadata": self.metadata,
        }

    def sample(self, n: int) -> "MemoryDataset":
        """Sample n trajectories from the dataset."""
        if n > len(self.trajectories):
            raise ValueError(f"Cannot sample {n} from {len(self.trajectories)} trajectories")

        # For subclasses with custom __init__, use a simpler approach
        new_instance = self.__class__()
        new_instance.trajectories = self.trajectories[:n]
        new_instance.qa_pairs = self.qa_pairs[:n]
        new_instance.metadata = self.metadata.copy()
        return new_instance