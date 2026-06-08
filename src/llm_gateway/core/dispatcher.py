from time import perf_counter

from llm_gateway.core.errors import OpenAIError
from llm_gateway.core.router import ModelRouter
from llm_gateway.core.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionUsage,
    ProviderTarget,
)
from llm_gateway.observability.logging import set_request_log_context
from llm_gateway.providers.base import BaseProvider, ProviderError
from llm_gateway.utils.ids import new_request_id
from llm_gateway.utils.tokens import estimate_completion_tokens, estimate_prompt_tokens


class ChatDispatcher:
    def __init__(self, route_resolver: ModelRouter, providers: dict[str, BaseProvider]) -> None:
        self._route_resolver = route_resolver
        self._providers = providers

    async def chat(
        self,
        request: ChatCompletionRequest,
        *,
        request_id: str | None = None,
        api_key_prefix: str | None = None,
        log_context: dict[str, object] | None = None,
    ) -> ChatCompletionResponse:
        request_id = request_id or new_request_id("chatcmpl")
        started = perf_counter()
        target: ProviderTarget | None = None
        prompt_tokens = estimate_prompt_tokens(request.messages)
        completion_tokens = 0
        error: str | None = None

        try:
            target = self._route_resolver.resolve(request.model)
            provider = self._get_provider(target.provider)
            provider_request = request.model_copy(update={"model": target.model, "stream": False})
            response = await provider.chat(provider_request, target=target, request_id=request_id)
            response.model = request.model

            if response.usage is None:
                completion_tokens = estimate_completion_tokens(response)
                response.usage = CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
            else:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

            return response
        except OpenAIError as exc:
            error = exc.code or exc.message
            raise
        except ProviderError as exc:
            error = exc.code
            raise OpenAIError(
                message=str(exc),
                status_code=502,
                error_type="server_error",
                code=exc.code,
            ) from exc
        finally:
            self._write_log(
                request_id=request_id,
                request=request,
                target=target,
                started=started,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                error=error,
                api_key_prefix=api_key_prefix,
                log_context=log_context,
            )

    def _write_log(
        self,
        *,
        request_id: str,
        request: ChatCompletionRequest,
        target: ProviderTarget | None,
        started: float,
        prompt_tokens: int,
        completion_tokens: int,
        error: str | None,
        api_key_prefix: str | None = None,
        log_context: dict[str, object] | None = None,
    ) -> None:
        total_tokens = prompt_tokens + completion_tokens
        set_request_log_context(
            context=log_context,
            request_id=request_id,
            api_key_prefix=api_key_prefix,
            model_alias=request.model,
            provider=target.provider if target else None,
            provider_model=target.model if target else None,
            dispatcher_latency_ms=int((perf_counter() - started) * 1000),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            token_estimated=True,
            error_code=error,
        )

    def _get_provider(self, name: str) -> BaseProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise OpenAIError(
                message=f"Provider is not registered: {name}",
                status_code=502,
                error_type="server_error",
                code="provider_not_registered",
            )
        return provider
