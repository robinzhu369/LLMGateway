from fastapi import APIRouter, Request

from llm_gateway.api.deps import Authorized, DispatcherDep
from llm_gateway.core.errors import OpenAIError
from llm_gateway.core.schemas import ChatCompletionRequest
from llm_gateway.observability.logging import set_request_log_context

router = APIRouter(tags=["chat"])


@router.post("/chat/completions")
async def create_chat_completion(
    raw_request: Request,
    request: ChatCompletionRequest,
    _auth: Authorized,
    dispatcher: DispatcherDep,
):
    set_request_log_context(raw_request, model_alias=request.model)
    if request.stream:
        set_request_log_context(raw_request, error_code="not_implemented")
        raise OpenAIError(
            message="Streaming chat completions are not implemented in V0.1.",
            status_code=501,
            error_type="server_error",
            code="not_implemented",
        )
    return await dispatcher.chat(
        request,
        request_id=raw_request.state.request_id,
        api_key_prefix=raw_request.state.api_key_prefix,
        log_context=raw_request.state.request_log_context,
    )
