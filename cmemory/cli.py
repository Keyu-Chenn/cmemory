"""Command-line interface for memory comparison framework."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cmemory import (
    EvaluationPipeline,
    Mem0Engine,
    FullContextEngine,
    get_default_config,
)
from cmemory.datasets import SimpleTestDataset
from cmemory.evaluation.pipeline import PipelineConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Memory framework comparison tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run evaluation")
    run_parser.add_argument(
        "--engines",
        nargs="+",
        default=["mem0", "full_context"],
        help="Engines to evaluate (default: mem0, full_context)",
    )
    run_parser.add_argument(
        "--dataset",
        default="simple_test",
        help="Dataset to use (default: simple_test)",
    )
    run_parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key",
    )
    run_parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_API_BASE"),
        help="OpenAI API base URL",
    )
    run_parser.add_argument(
        "--qa-model",
        default="gpt-4o-mini",
        help="Model for QA generation",
    )
    run_parser.add_argument(
        "--judge-model",
        default="gpt-4o-mini",
        help="Model for judging answers",
    )
    run_parser.add_argument(
        "--output",
        default="results.json",
        help="Output file for results",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available resources")
    list_parser.add_argument(
        "resource",
        choices=["engines", "datasets"],
        help="What to list",
    )

    args = parser.parse_args()

    if args.command == "run":
        run_evaluation(args)
    elif args.command == "list":
        list_resources(args)
    else:
        parser.print_help()


def run_evaluation(args):
    """Run evaluation with specified engines and dataset."""
    print("=" * 50)
    print("Memory Framework Comparison")
    print("=" * 50)

    # Create engines
    engines = {}
    for engine_name in args.engines:
        if engine_name == "mem0":
            engines["mem0"] = Mem0Engine(
                user_id="test_user",
                config={"vector_store": {"provider": "qdrant"}},
            )
        elif engine_name == "full_context":
            engines["full_context"] = FullContextEngine(
                user_id="test_user",
                save_dir=".memory_data/test_user",
            )
        else:
            print(f"Warning: Unknown engine '{engine_name}', skipping")

    if not engines:
        print("Error: No valid engines specified")
        return

    # Create dataset
    if args.dataset == "simple_test":
        dataset = SimpleTestDataset()
    else:
        print(f"Warning: Unknown dataset '{args.dataset}', using simple_test")
        dataset = SimpleTestDataset()

    # Create pipeline config
    config = PipelineConfig(
        qa_model=args.qa_model,
        judge_model=args.judge_model,
        api_key=args.api_key,
        base_url=args.base_url,
    )

    # Run evaluation
    pipeline = EvaluationPipeline(engines, config)
    results = pipeline.run(dataset)

    # Print results
    print("\n" + "=" * 50)
    print("Results Summary")
    print("=" * 50)

    comparison = results.get_comparison_table()
    for engine_name, metrics in comparison.items():
        print(f"\n{engine_name}:")
        print(f"  Accuracy: {metrics['accuracy']:.2%}")
        print(f"  Total tokens: {metrics['total_tokens']}")
        print(f"  Total time: {metrics['total_time_seconds']:.2f}s")
        print(f"  API calls: {metrics['api_calls']}")

    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "dataset": results.dataset_name,
                "evaluation_time": results.evaluation_time_seconds,
                "comparison": comparison,
            },
            f,
            indent=2,
        )

    print(f"\nResults saved to: {args.output}")


def list_resources(args):
    """List available engines or datasets."""
    if args.resource == "engines":
        print("Available engines:")
        print("  - mem0: Mem0 memory engine (requires mem0ai)")
        print("  - full_context: Full context baseline (no memory abstraction)")
        print("  - zep: Zep memory engine (requires zep-python)")
        print("  - letta: Letta/MemGPT engine (requires letta)")

    elif args.resource == "datasets":
        print("Available datasets:")
        print("  - simple_test: Simple test dataset (9 questions, 3 trajectories)")
        print("  - longmemeval: LongMemEval benchmark (requires download)")
        print("  - locomo: LoCoMo benchmark (requires download)")


if __name__ == "__main__":
    main()