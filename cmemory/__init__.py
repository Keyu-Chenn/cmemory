"""Memory framework comparison framework.

cmemory provides a unified interface for comparing different memory frameworks
(Mem0, Zep, Letta/MemGPT) on memory retrieval and QA tasks.

Usage:
    from cmemory import EvaluationPipeline, Mem0Engine, FullContextEngine
    from cmemory.datasets import SimpleTestDataset

    # Create engines
    engines = {
        "mem0": Mem0Engine(user_id="test"),
        "full_context": FullContextEngine(user_id="test"),
    }

    # Run evaluation
    pipeline = EvaluationPipeline(engines)
    dataset = SimpleTestDataset()
    results = pipeline.run(dataset)

    # View comparison
    print(results.get_comparison_table())
"""

from .core import (
    BaseMemoryEngine,
    EngineStats,
    Message,
    Session,
    Trajectory,
    SearchResult,
    EvaluationResult,
    MetricsCollector,
)
from .engines import Mem0Engine, FullContextEngine
from .evaluation import EvaluationPipeline, QAEvaluator, LLMJudge
from .datasets import MemoryDataset, SimpleTestDataset
from .config import Config, get_default_config

__version__ = "0.1.0"

__all__ = [
    # Core
    "BaseMemoryEngine",
    "EngineStats",
    "Message",
    "Session",
    "Trajectory",
    "SearchResult",
    "EvaluationResult",
    "MetricsCollector",
    # Engines
    "Mem0Engine",
    "FullContextEngine",
    # Evaluation
    "EvaluationPipeline",
    "QAEvaluator",
    "LLMJudge",
    # Datasets
    "MemoryDataset",
    "SimpleTestDataset",
    # Config
    "Config",
    "get_default_config",
]