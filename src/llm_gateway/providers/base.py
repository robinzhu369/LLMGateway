from abc import ABC, abstractmethod

from llm_gateway.core.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ProviderTarget,
)


class ProviderError(Exception):
    def __init__(self, message: str, *, code: str = "provider_error") -> None:
        super().__init__(message)
        self.code = code


class BaseProvider(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def chat(
        self,
        request: ChatCompletionRequest,
        *,
        target: ProviderTarget,
        request_id: str,
    ) -> ChatCompletionResponse:
        raise NotImplementedError
