from math import ceil
from typing import Any

from llm_gateway.core.schemas import ChatMessage


def estimate_text_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, ceil(len(stripped) / 4))


def estimate_prompt_tokens(messages: list[ChatMessage]) -> int:
    return sum(4 + estimate_text_tokens(_content_as_text(message.content)) for message in messages)


def estimate_completion_tokens(response_or_chunk: Any) -> int:
    choices = getattr(response_or_chunk, "choices", [])
    text_parts: list[str] = []
    for choice in choices:
        message = getattr(choice, "message", None)
        delta = getattr(choice, "delta", None)
        if message is not None:
            text_parts.append(_content_as_text(getattr(message, "content", "")))
        if delta is not None:
            text_parts.append(_content_as_text(getattr(delta, "content", "")))
    return estimate_text_tokens("".join(text_parts))


def _content_as_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return str(content)

