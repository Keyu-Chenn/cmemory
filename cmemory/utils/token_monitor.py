"""Token counting utilities."""

from __future__ import annotations

import tiktoken
from typing import Optional


def count_tokens(
    text: str,
    model: str = "gpt-4o-mini",
) -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count
        model: Model to use for tokenization

    Returns:
        Number of tokens
    """
    try:
        # Try to get encoding for the model
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fall back to cl100k_base (GPT-4 encoding)
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def count_messages_tokens(
    messages: list,
    model: str = "gpt-4o-mini",
) -> int:
    """
    Count tokens in a list of messages.

    Args:
        messages: List of message dicts
        model: Model for tokenization

    Returns:
        Total tokens including message overhead
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # Approximate token count with message overhead
    # Each message has ~4 tokens overhead for formatting
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        total += len(encoding.encode(content))
        total += 4  # Message overhead

    total += 2  # Conversation overhead
    return max(total, 1)