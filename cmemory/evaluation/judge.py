"""LLM-as-Judge for evaluating answer correctness."""

from __future__ import annotations

from typing import Optional, Tuple

from ..utils.llm_client import LLMClient


class LLMJudge:
    """
    LLM-as-Judge evaluator for determining answer correctness.
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

    def evaluate(
        self,
        question: str,
        expected_answers: Tuple[str, ...],
        generated_answer: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Judge if the generated answer matches expected answers.

        Args:
            question: The original question
            expected_answers: Acceptable answer variants
            generated_answer: The answer to evaluate

        Returns:
            Tuple of (is_correct, reasoning)
        """
        # First try exact/simple matching
        if self._simple_match(expected_answers, generated_answer):
            return True, "Exact match with expected answer"

        # Use LLM for more nuanced evaluation
        prompt = self._build_judge_prompt(
            question, expected_answers, generated_answer
        )
        response = self.llm_client.call(prompt)

        content = response.get("content", "").strip().lower()

        # Parse response
        if content.startswith("yes") or "正确" in content or "匹配" in content:
            return True, response.get("content", "")
        elif content.startswith("no") or "不正确" in content or "不匹配" in content:
            return False, response.get("content", "")

        # Default to False if unclear
        return False, response.get("content", "Unable to determine")

    def _simple_match(
        self,
        expected: Tuple[str, ...],
        generated: str,
    ) -> bool:
        """Simple string matching for obvious cases."""
        generated_lower = generated.strip().lower()

        for exp in expected:
            exp_lower = exp.strip().lower()

            # Exact match
            if generated_lower == exp_lower:
                return True

            # Contains match (for partial answers)
            if exp_lower in generated_lower or generated_lower in exp_lower:
                return True

            # Number matching (handle "two" vs "2" etc)
            try:
                if float(generated_lower) == float(exp_lower):
                    return True
            except ValueError:
                pass

        return False

    def _build_judge_prompt(
        self,
        question: str,
        expected_answers: Tuple[str, ...],
        generated_answer: str,
    ) -> str:
        """Build the judge prompt."""
        expected_str = "或".join(expected_answers)

        return f"""判断生成的答案是否正确匹配预期答案。

问题: {question}
预期答案: {expected_str}
生成答案: {generated_answer}

判断规则:
1. 如果生成答案包含预期的关键信息，视为正确
2. 如果答案语义上等价，视为正确
3. 如果答案不完整但包含正确信息的一部分，根据具体情况判断
4. 如果答案与预期完全不相关，视为不正确

请回答 "yes" 或 "no"，并简要说明理由: """