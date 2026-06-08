import json
import logging
from time import perf_counter
from typing import Any

from fastapi import Request
from starlette.responses import Response

from llm_gateway.core.errors import OpenAIError
from llm_gateway.core.schemas import RequestLog
from llm_gateway.settings import LoggingConfig

LOGGER_NAME = "llm_gateway.requests"
REQUEST_LOG_STATE = "request_log_context"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }
        record_payload = getattr(record, "payload", None)
        if isinstance(record_payload, dict):
            payload.update(record_payload)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(config: LoggingConfig) -> None:
    root = logging.getLogger()
    root.setLevel(config.level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if config.format == "json" else logging.Formatter())
    root.handlers = [handler]


def log_request(record: RequestLog) -> None:
    logging.getLogger(LOGGER_NAME).info(
        "llm_request",
        extra={"payload": record.model_dump(exclude_none=True)},
    )


def get_request_log_context(request: Request) -> dict[str, Any]:
    context = getattr(request.state, REQUEST_LOG_STATE, None)
    if not isinstance(context, dict):
        context = {}
        setattr(request.state, REQUEST_LOG_STATE, context)
    return context


def set_request_log_context(
    request: Request | None = None,
    *,
    context: dict[str, Any] | None = None,
    **values: Any,
) -> None:
    if context is None:
        if request is None:
            return
        context = get_request_log_context(request)
    context.update({key: value for key, value in values.items() if value is not None})


async def request_logging_middleware(request: Request, call_next) -> Response:
    started = perf_counter()
    request_id = request.state.request_id
    context: dict[str, Any] = {}
    setattr(request.state, REQUEST_LOG_STATE, context)

    try:
        response = await call_next(request)
    except Exception as exc:
        _write_http_request_log(
            request=request,
            request_id=request_id,
            started=started,
            http_status=exc.status_code if isinstance(exc, OpenAIError) else 500,
            error_code=_error_code(exc),
        )
        raise

    _write_http_request_log(
        request=request,
        request_id=request_id,
        started=started,
        http_status=response.status_code,
        error_code=_response_error_code(response),
    )
    return response


def _write_http_request_log(
    *,
    request: Request,
    request_id: str,
    started: float,
    http_status: int,
    error_code: str | None,
) -> None:
    context = getattr(request.state, REQUEST_LOG_STATE, {})
    if not isinstance(context, dict):
        context = {}

    log_request(
        RequestLog(
            request_id=request_id,
            api_key_prefix=getattr(request.state, "api_key_prefix", None),
            method=request.method,
            path=request.url.path,
            http_status=http_status,
            model_alias=context.get("model_alias"),
            provider=context.get("provider"),
            provider_model=context.get("provider_model"),
            status="success" if http_status < 400 else "error",
            latency_ms=int((perf_counter() - started) * 1000),
            prompt_tokens=context.get("prompt_tokens", 0),
            completion_tokens=context.get("completion_tokens", 0),
            total_tokens=context.get("total_tokens", 0),
            token_estimated=context.get("token_estimated", True),
            error_code=error_code or context.get("error_code"),
        )
    )


def _error_code(exc: Exception) -> str:
    if isinstance(exc, OpenAIError) and exc.code:
        return exc.code
    return exc.__class__.__name__


def _response_error_code(response: Response) -> str | None:
    if response.status_code < 400:
        return None
    return response.headers.get("x-error-code")
