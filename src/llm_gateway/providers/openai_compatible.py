import os

import httpx

from llm_gateway.core.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ProviderTarget,
)
from llm_gateway.providers.base import BaseProvider, ProviderError


class OpenAICompatibleProvider(BaseProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key_env: str = "",
        timeout: float = 60.0,
    ) -> None:
        super().__init__(name=name)
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout = timeout

    async def chat(
        self,
        request: ChatCompletionRequest,
        *,
        target: ProviderTarget,
        request_id: str,
    ) -> ChatCompletionResponse:
        del target, request_id
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=request.model_dump(exclude_none=True),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Provider {self.name} returned HTTP {exc.response.status_code}",
                code="provider_http_error",
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"Provider {self.name} request failed: {exc}",
                code="provider_request_error",
            ) from exc
        return ChatCompletionResponse.model_validate(response.json())

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            api_key = os.getenv(self.api_key_env)
            if not api_key:
                raise ProviderError(
                    f"Provider API key env is not set: {self.api_key_env}",
                    code="provider_api_key_missing",
                )
            headers["Authorization"] = f"Bearer {api_key}"
        return headers
