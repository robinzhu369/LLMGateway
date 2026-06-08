from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from llm_gateway.core.errors import OpenAIError, openai_error_payload
from llm_gateway.observability.logging import set_request_log_context


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OpenAIError)
    async def handle_openai_error(request: Request, exc: OpenAIError) -> JSONResponse:
        set_request_log_context(request, error_code=exc.code)
        return JSONResponse(
            status_code=exc.status_code,
            content=openai_error_payload(
                message=exc.message,
                error_type=exc.error_type,
                code=exc.code,
                param=exc.param,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        set_request_log_context(request, error_code="validation_error")
        return JSONResponse(
            status_code=422,
            content=openai_error_payload(
                message=str(exc.errors()),
                error_type="invalid_request_error",
                code="validation_error",
            ),
        )
