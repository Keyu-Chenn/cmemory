"""Evaluation pipeline for memory framework comparison."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.base import BaseMemoryEngine
from ..core.models import (
    EngineEvaluation,
    EvaluationResult,
    QAResult,
    RetrievalResult,
    SearchResult,
)
from ..core.metrics import MetricsCollector
from ..datasets.base import MemoryDataset
from .qa_evaluator import QAEvaluator
from .judge import LLMJudge


@dataclass
class PipelineConfig:
    """Configuration for evaluation pipeline."""

    retrieval_limit: int = 10
    qa_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class EvaluationPipeline:
    """
    Three-stage evaluation pipeline for memory frameworks.

    Stage 1: Memory Construction - Feed trajectories to memory engines
    Stage 2: Memory Retrieval - Retrieve memories for each question
    Stage 3: QA Evaluation - Generate and evaluate answers
    """

    def __init__(
        self,
        engines: Dict[str, BaseMemoryEngine],
        config: Optional[PipelineConfig] = None,
    ) -> None:
        self.engines = engines
        self.config = config or PipelineConfig()
        self.metrics = MetricsCollector()

        # Initialize QA evaluator and judge
        self.qa_evaluator = QAEvaluator(
            model=self.config.qa_model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        self.judge = LLMJudge(
            model=self.config.judge_model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def run(self, dataset: MemoryDataset) -> EvaluationResult:
        """
        Run full evaluation pipeline on dataset.

        Args:
            dataset: MemoryDataset to evaluate

        Returns:
            EvaluationResult with all engine results
        """
        start_time = time.time()

        # Register all engines for metrics tracking
        for name in self.engines:
            self.metrics.register_engine(name)

        engine_results = {}

        for engine_name, engine in self.engines.items():
            print(f"\n=== Evaluating engine: {engine_name} ===")

            # Stage 1: Memory Construction
            print("Stage 1: Memory Construction...")
            self._construct_memories(engine, dataset)

            # Stage 2: Memory Retrieval
            print("Stage 2: Memory Retrieval...")
            retrieval_results = self._retrieve_memories(engine, dataset)

            # Stage 3: QA Evaluation
            print("Stage 3: QA Evaluation...")
            qa_results = self._evaluate_answers(
                engine_name, retrieval_results, dataset.qa_pairs
            )

            # Collect results
            engine_eval = EngineEvaluation(
                engine_name=engine_name,
                qa_results=qa_results,
                retrieval_results=retrieval_results,
                stats=engine.get_stats(),
            )
            engine_eval.compute_accuracy()

            engine_results[engine_name] = engine_eval

            # Clear engine for next run
            engine.clear()
            engine.reset_stats()

        elapsed = time.time() - start_time

        return EvaluationResult(
            dataset_name=dataset.name,
            engine_results=engine_results,
            evaluation_time_seconds=elapsed,
            metadata=dataset.metadata,
        )

    def _construct_memories(
        self,
        engine: BaseMemoryEngine,
        dataset: MemoryDataset,
    ) -> None:
        """Stage 1: Build memory from trajectories."""
        for trajectory in dataset.trajectories:
            for session in trajectory.sessions:
                for message in session.messages:
                    engine.add(
                        content=message.content,
                        role=message.role,
                        timestamp=message.timestamp,
                    )

        engine.save()

    def _retrieve_memories(
        self,
        engine: BaseMemoryEngine,
        dataset: MemoryDataset,
    ) -> List[RetrievalResult]:
        """Stage 2: Retrieve memories for each question."""
        results = []

        for qa_pair in dataset.qa_pairs:
            with self.metrics.track_time(engine.engine_name, "search"):
                memories = engine.search(
                    qa_pair.question,
                    limit=self.config.retrieval_limit,
                )

            retrieval_result = RetrievalResult(
                question=qa_pair.question,
                retrieved_memories=[
                    SearchResult(
                        content=m["content"],
                        score=m.get("score", 1.0),
                        memory_id=m.get("memory_id"),
                    )
                    for m in memories
                ],
                engine_name=engine.engine_name,
            )
            results.append(retrieval_result)

        return results

    def _evaluate_answers(
        self,
        engine_name: str,
        retrieval_results: List[RetrievalResult],
        qa_pairs: List,
    ) -> List[QAResult]:
        """Stage 3: Generate and judge answers."""
        qa_results = []

        for retrieval, qa_pair in zip(retrieval_results, qa_pairs):
            # Format retrieved memories as context
            context = self._format_context(retrieval.retrieved_memories)

            # Generate answer using QA evaluator
            generated_answer = self.qa_evaluator.generate_answer(
                question=qa_pair.question,
                context=context,
            )

            # Judge if answer is correct
            is_correct, reasoning = self.judge.evaluate(
                question=qa_pair.question,
                expected_answers=qa_pair.answers,
                generated_answer=generated_answer,
            )

            # Record accuracy
            self.metrics.record_accuracy(
                engine_name,
                is_correct,
                qa_pair.question_type,
            )

            qa_result = QAResult(
                question=qa_pair.question,
                expected_answers=qa_pair.answers,
                generated_answer=generated_answer,
                retrieved_context=context,
                is_correct=is_correct,
                judge_reasoning=reasoning,
            )
            qa_results.append(qa_result)

        return qa_results

    def _format_context(self, memories: List[SearchResult]) -> str:
        """Format retrieved memories as context string."""
        if not memories:
            return "No relevant memories found."

        lines = ["Retrieved memories:"]
        for i, mem in enumerate(memories, 1):
            lines.append(f"{i}. {mem.content} (score: {mem.score:.2f})")
        return "\n".join(lines)