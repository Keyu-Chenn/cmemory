"""OpenAI LLM client wrapper."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


class LLMClient:
    """
    Wrapper for OpenAI API calls.

    Supports both OpenAI and OpenAI-compatible APIs.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._base_url = base_url or os.getenv("OPENAI_API_BASE")

        self._client = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize the OpenAI client."""
        if self._initialized:
            return

        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

    def call(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Make a simple text completion call.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'content', 'tokens', etc.
        """
        self._ensure_initialized()

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "content": content,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

    def call_with_messages(
        self,
        messages: list,
        *,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Make a completion call with full message list.

        Args:
            messages: Full message list
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Dict with response info
        """
        self._ensure_initialized()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "content": content,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }