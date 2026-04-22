"""Tests for dataset module."""

import pytest

from cmemory.datasets import SimpleTestDataset, MemoryDataset


class TestSimpleTestDataset:
    """Tests for SimpleTestDataset."""

    def test_dataset_creation(self):
        dataset = SimpleTestDataset()

        assert dataset.name == "simple_test"
        assert len(dataset) > 0
        assert len(dataset.trajectories) > 0
        assert len(dataset.qa_pairs) > 0

    def test_dataset_iteration(self):
        dataset = SimpleTestDataset()

        for traj, qa in dataset:
            assert traj is not None
            assert qa is not None
            break  # Just test first

    def test_dataset_stats(self):
        dataset = SimpleTestDataset()
        stats = dataset.get_stats()

        assert stats["name"] == "simple_test"
        assert "num_trajectories" in stats
        assert "num_questions" in stats
        assert stats["num_questions"] == 9  # 9 test questions

    def test_sample(self):
        dataset = SimpleTestDataset()
        sampled = dataset.sample(2)

        assert len(sampled) == 2
        assert len(sampled.trajectories) == 2
        assert len(sampled.qa_pairs) == 2

    def test_qa_pairs_content(self):
        dataset = SimpleTestDataset()

        # Check first QA pair
        qa = dataset.qa_pairs[0]
        assert "水果" in qa.question
        assert "苹果" in qa.answers or "香蕉" in qa.answers

        # Check question types
        single_count = sum(1 for qa in dataset.qa_pairs if qa.question_type == "single")
        assert single_count > 0