"""LongMemEval dataset loader for memory framework comparison."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.models import Message, Session, Trajectory, QuestionAnswerPair
from .base import MemoryDataset


class LongMemEvalDataset(MemoryDataset):
    """
    LongMemEval dataset loader.

    LongMemEval is a benchmark for evaluating long-term memory capabilities
    of LLM-based assistants. It contains multi-session user-agent conversations
    with questions that require retrieving information from past sessions.

    Dataset structure:
    - question_id: Unique identifier for the question
    - question_type: Type of question (e.g., "single-session-user")
    - question: The question to answer
    - question_date: Date when the question was asked
    - answer: Expected answer
    - haystack_sessions: List of historical conversation sessions
    - haystack_dates: Dates of each session
    - haystack_session_ids: IDs of each session
    """

    name: str = "longmemeval"

    def __init__(
        self,
        data_path: Optional[str] = None,
        max_sessions: Optional[int] = None,
        max_questions: Optional[int] = None,
    ) -> None:
        """
        Initialize LongMemEval dataset.

        Args:
            data_path: Path to the JSON data file. If None, uses default path.
            max_sessions: Maximum number of sessions to load (for testing).
            max_questions: Maximum number of questions to load (for testing).
        """
        # Default path: look in cmemory datasets folder, then LightMem repository
        if data_path is None:
            # Try multiple default paths
            default_paths = [
                Path(__file__).parent.parent.parent / "datasets" / "longmemeval_oracle.json",
                Path(__file__).parent.parent.parent / "datasets" / "longmemeval_single.json",
                Path("/tbase-project/LightMem/tutorial-notebooks/longmemeval_single.json"),
            ]
            for p in default_paths:
                if p.exists():
                    data_path = str(p)
                    break
            if data_path is None:
                raise FileNotFoundError("LongMemEval data not found. Please download from HuggingFace.")

        self._data_path = Path(data_path)
        self._max_sessions = max_sessions
        self._max_questions = max_questions

        # Load data
        trajectories, qa_pairs, metadata = self._load_data()

        super().__init__(
            name="longmemeval",
            trajectories=trajectories,
            qa_pairs=qa_pairs,
            metadata=metadata,
        )

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp from LongMemEval format.

        Input format: '2023/05/30 (Tue) 17:27'
        Output: datetime object
        """
        # Remove day of week (e.g., "(Tue)")
        clean_ts = timestamp_str.split("(")[0].strip()
        if ")" in timestamp_str:
            time_part = timestamp_str.split(")")[1].strip()
            clean_ts = clean_ts + " " + time_part

        # Parse: '2023/05/30 17:27'
        try:
            dt = datetime.strptime(clean_ts, "%Y/%m/%d %H:%M")
        except ValueError:
            # Fallback: try with seconds
            try:
                dt = datetime.strptime(clean_ts, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                dt = datetime.now()

        return dt

    def _load_data(self) -> Tuple[List[Trajectory], List[QuestionAnswerPair], Dict[str, Any]]:
        """
        Load and parse LongMemEval JSON data.

        Returns:
            Tuple of (trajectories, qa_pairs, metadata)
        """
        if not self._data_path.exists():
            raise FileNotFoundError(f"LongMemEval data not found: {self._data_path}")

        with open(self._data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Handle single item or list
        if isinstance(raw_data, dict):
            data_items = [raw_data]
        else:
            data_items = raw_data

        # Limit questions if specified
        if self._max_questions:
            data_items = data_items[:self._max_questions]

        trajectories = []
        qa_pairs = []

        # Collect unique sessions across all questions
        all_sessions: Dict[str, Tuple[List[Dict], str]] = {}

        for item in data_items:
            # Extract sessions
            sessions = item.get("haystack_sessions", [])
            dates = item.get("haystack_dates", [])
            session_ids = item.get("haystack_session_ids", [])

            for session, date, sid in zip(sessions, dates, session_ids):
                if sid not in all_sessions and (self._max_sessions is None or len(all_sessions) < self._max_sessions):
                    all_sessions[sid] = (session, date)

            # Extract question-answer pair
            qa_pair = QuestionAnswerPair(
                question=item.get("question", ""),
                answers=(item.get("answer", ""),),
                question_type=item.get("question_type", "unknown"),
                metadata={
                    "question_id": item.get("question_id"),
                    "question_date": item.get("question_date"),
                    "answer_session_ids": item.get("answer_session_ids", []),
                }
            )
            qa_pairs.append(qa_pair)

        # Convert sessions to Trajectories
        for sid, (session_msgs, date_str) in all_sessions.items():
            timestamp = self._parse_timestamp(date_str)

            # Convert messages
            messages = []
            for msg in session_msgs:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                # Create message with timestamp
                message = Message(
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    metadata={
                        "session_id": sid,
                    }
                )
                messages.append(message)

            # Create session
            session = Session(
                session_id=sid,
                messages=messages,
                timestamp=timestamp,
            )

            # Create trajectory (one session per trajectory for LongMemEval)
            trajectory = Trajectory(
                trajectory_id=f"traj_{sid}",
                sessions=[session],
                metadata={
                    "date": date_str,
                    "source": "longmemeval",
                }
            )
            trajectories.append(trajectory)

        # Sort trajectories by timestamp
        trajectories.sort(key=lambda t: t.sessions[0].timestamp if t.sessions else datetime.min)

        # Generate metadata
        metadata = {
            "name": "longmemeval",
            "description": "LongMemEval benchmark dataset for long-term memory evaluation",
            "num_trajectories": len(trajectories),
            "num_questions": len(qa_pairs),
            "data_path": str(self._data_path),
            "question_types": self._count_question_types(qa_pairs),
        }

        return trajectories, qa_pairs, metadata

    def _count_question_types(self, qa_pairs: List[QuestionAnswerPair]) -> Dict[str, int]:
        """Count question types distribution."""
        counts: Dict[str, int] = {}
        for qa in qa_pairs:
            qtype = qa.question_type
            counts[qtype] = counts.get(qtype, 0) + 1
        return counts

    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate dataset metadata (required by base class)."""
        return self.metadata

    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get a specific session by its ID."""
        for traj in self.trajectories:
            for session in traj.sessions:
                if session.session_id == session_id:
                    return session
        return None

    def get_question_by_id(self, question_id: str) -> Optional[QuestionAnswerPair]:
        """Get a specific question by its ID."""
        for qa in self.qa_pairs:
            if qa.metadata.get("question_id") == question_id:
                return qa
        return None

    def get_answer_sessions(self, question_id: str) -> List[Session]:
        """Get the sessions that contain the answer for a question."""
        qa = self.get_question_by_id(question_id)
        if qa is None:
            return []

        answer_session_ids = qa.metadata.get("answer_session_ids", [])
        sessions = []
        for sid in answer_session_ids:
            session = self.get_session_by_id(sid)
            if session:
                sessions.append(session)
        return sessions