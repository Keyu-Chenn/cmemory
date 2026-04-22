"""QA evaluator for generating answers from retrieved context."""

from __future__ import annotations

from typing import Optional

from ..utils.llm_client import LLMClient


class QAEvaluator:
    """
    QA evaluator that generates answers using retrieved memories as context.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model
        self.llm_client = LLMClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate an answer based on retrieved context.

        Args:
            question: The question to answer
            context: Retrieved memories as context

        Returns:
            Generated answer string
        """
        prompt = self._build_prompt(question, context)
        response = self.llm_client.call(prompt)
        return response.get("content", "")

    def _build_prompt(self, question: str, context: str) -> str:
        """Build the QA prompt."""
        return f"""基于以下记忆信息回答问题。如果记忆中没有相关信息，请回答"不知道"。

记忆信息:
{context}

问题: {question}

请简洁地回答问题，直接给出答案，不要解释: """