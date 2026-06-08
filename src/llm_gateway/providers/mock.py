from time import time

from llm_gateway.core.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    CompletionUsage,
    ProviderTarget,
)
from llm_gateway.providers.base import BaseProvider
from llm_gateway.utils.tokens import estimate_text_tokens


class MockProvider(BaseProvider):
    async def chat(
        self,
        request: ChatCompletionRequest,
        *,
        target: ProviderTarget,
        request_id: str,
    ) -> ChatCompletionResponse:
        content = self._response_text(request, target)
        prompt_tokens = sum(
            estimate_text_tokens(str(message.content or "")) for message in request.messages
        )
        completion_tokens = estimate_text_tokens(content)
        return ChatCompletionResponse(
            id=request_id,
            created=int(time()),
            model=target.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionResponseMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    def _response_text(self, request: ChatCompletionRequest, target: ProviderTarget) -> str:
        user_messages = [message for message in request.messages if message.role == "user"]
        last_user = user_messages[-1].content if user_messages else ""
        return f"Mock response from {target.provider}/{target.model}: {last_user}"
