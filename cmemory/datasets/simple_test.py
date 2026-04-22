"""Simple test dataset for framework validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..core.models import Message, Session, Trajectory, QuestionAnswerPair
from .base import MemoryDataset


class SimpleTestDataset(MemoryDataset):
    """
    Simple test dataset for validating the comparison framework.

    Contains a few trajectories with clear facts and corresponding
    questions to test basic memory retrieval capabilities.
    """

    name: str = "simple_test"

    def __init__(self) -> None:
        trajectories = self._create_trajectories()
        qa_pairs = self._create_qa_pairs()

        super().__init__(
            name="simple_test",
            trajectories=trajectories,
            qa_pairs=qa_pairs,
            metadata={},
        )

    def _create_trajectories(self) -> List[Trajectory]:
        """Create test trajectories with simple facts."""
        trajectories = []

        # Trajectory 1: User preferences
        sessions = [
            Session(
                session_id="session-1",
                messages=(
                    Message(
                        role="user",
                        content="我喜欢吃苹果，每天吃两个苹果。",
                        timestamp=datetime(2024, 1, 1, 10, 0),
                    ),
                    Message(
                        role="assistant",
                        content="好的，我记住了您喜欢吃苹果，每天两个。",
                        timestamp=datetime(2024, 1, 1, 10, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 1, 10, 0),
            ),
            Session(
                session_id="session-2",
                messages=(
                    Message(
                        role="user",
                        content="我还喜欢吃香蕉，尤其是在早餐时。",
                        timestamp=datetime(2024, 1, 2, 8, 0),
                    ),
                    Message(
                        role="assistant",
                        content="明白了，您早餐喜欢吃香蕉。",
                        timestamp=datetime(2024, 1, 2, 8, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 2, 8, 0),
            ),
        ]
        trajectories.append(
            Trajectory(
                trajectory_id="traj-1-preferences",
                sessions=sessions,
                metadata={"category": "user_preference"},
            )
        )

        # Trajectory 2: Personal information
        sessions = [
            Session(
                session_id="session-3",
                messages=(
                    Message(
                        role="user",
                        content="我的名字是张三，我住在北京市朝阳区。",
                        timestamp=datetime(2024, 1, 3, 14, 0),
                    ),
                    Message(
                        role="assistant",
                        content="好的张三，我记住了您住在北京朝阳区。",
                        timestamp=datetime(2024, 1, 3, 14, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 3, 14, 0),
            ),
            Session(
                session_id="session-4",
                messages=(
                    Message(
                        role="user",
                        content="我的生日是1990年5月15日。",
                        timestamp=datetime(2024, 1, 4, 9, 0),
                    ),
                    Message(
                        role="assistant",
                        content="我记住了，您的生日是1990年5月15日。",
                        timestamp=datetime(2024, 1, 4, 9, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 4, 9, 0),
            ),
        ]
        trajectories.append(
            Trajectory(
                trajectory_id="traj-2-personal",
                sessions=sessions,
                metadata={"category": "personal_info"},
            )
        )

        # Trajectory 3: Work-related information
        sessions = [
            Session(
                session_id="session-5",
                messages=(
                    Message(
                        role="user",
                        content="我在阿里巴巴工作，是一名软件工程师。",
                        timestamp=datetime(2024, 1, 5, 11, 0),
                    ),
                    Message(
                        role="assistant",
                        content="了解了，您在阿里巴巴做软件工程师。",
                        timestamp=datetime(2024, 1, 5, 11, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 5, 11, 0),
            ),
            Session(
                session_id="session-6",
                messages=(
                    Message(
                        role="user",
                        content="我正在做一个名为 LightMem 的项目。",
                        timestamp=datetime(2024, 1, 6, 15, 0),
                    ),
                    Message(
                        role="assistant",
                        content="好的，您正在做 LightMem 项目。",
                        timestamp=datetime(2024, 1, 6, 15, 1),
                    ),
                ),
                timestamp=datetime(2024, 1, 6, 15, 0),
            ),
        ]
        trajectories.append(
            Trajectory(
                trajectory_id="traj-3-work",
                sessions=sessions,
                metadata={"category": "work_info"},
            )
        )

        return trajectories

    def _create_qa_pairs(self) -> List[QuestionAnswerPair]:
        """Create test questions and expected answers."""
        qa_pairs = [
            # Preference questions
            QuestionAnswerPair(
                question="我喜欢吃什么水果？",
                answers=("苹果", "香蕉"),
                question_type="multi",  # Multiple facts
            ),
            QuestionAnswerPair(
                question="我每天吃几个苹果？",
                answers=("两个", "2"),
                question_type="single",
            ),
            QuestionAnswerPair(
                question="我早餐喜欢吃什么？",
                answers=("香蕉",),
                question_type="single",
            ),

            # Personal info questions
            QuestionAnswerPair(
                question="我叫什么名字？",
                answers=("张三",),
                question_type="single",
            ),
            QuestionAnswerPair(
                question="我住在哪里？",
                answers=("北京市朝阳区", "北京朝阳区", "北京"),
                question_type="single",
            ),
            QuestionAnswerPair(
                question="我的生日是什么时候？",
                answers=("1990年5月15日", "1990-05-15", "5月15日"),
                question_type="single",
            ),

            # Work questions
            QuestionAnswerPair(
                question="我在哪家公司工作？",
                answers=("阿里巴巴",),
                question_type="single",
            ),
            QuestionAnswerPair(
                question="我的职业是什么？",
                answers=("软件工程师",),
                question_type="single",
            ),
            QuestionAnswerPair(
                question="我在做什么项目？",
                answers=("LightMem",),
                question_type="single",
            ),
        ]
        return qa_pairs

    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate dataset metadata."""
        return {
            "name": self.name,
            "description": "Simple test dataset for framework validation",
            "num_trajectories": len(self.trajectories),
            "num_questions": len(self.qa_pairs),
            "question_types": {
                "single": sum(1 for qa in self.qa_pairs if qa.question_type == "single"),
                "multi": sum(1 for qa in self.qa_pairs if qa.question_type == "multi"),
            },
            "categories": ["user_preference", "personal_info", "work_info"],
            "language": "zh-CN",
        }