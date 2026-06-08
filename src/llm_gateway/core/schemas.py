from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_call_id: str | None = None

    model_config = ConfigDict(extra="allow")


class ProviderTarget(BaseModel):
    provider: str
    model: str
    weight: int | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: str | list[str] | None = None
    user: str | None = None

    model_config = ConfigDict(extra="allow")


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponseMessage(BaseModel):
    role: Literal["assistant"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionResponseMessage
    finish_reason: str | None = "stop"

    model_config = ConfigDict(extra="allow")


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: CompletionUsage | None = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionDelta(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: ChatCompletionDelta
    finish_reason: str | None = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]

    model_config = ConfigDict(extra="allow")


class RequestLog(BaseModel):
    request_id: str
    api_key_prefix: str | None = None
    method: str
    path: str
    http_status: int
    model_alias: str | None = None
    provider: str | None = None
    provider_model: str | None = None
    status: Literal["success", "error"]
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    token_estimated: bool = True
    error_code: str | None = None
