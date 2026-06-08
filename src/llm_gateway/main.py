from fastapi import FastAPI, Request
from starlette.responses import Response

from llm_gateway.api.errors import register_error_handlers
from llm_gateway.api.v1.chat import router as chat_router
from llm_gateway.api.v1.health import router as health_router
from llm_gateway.api.v1.models import router as models_router
from llm_gateway.core.dispatcher import ChatDispatcher
from llm_gateway.core.router import ModelRouter
from llm_gateway.observability.logging import configure_logging, request_logging_middleware
from llm_gateway.providers.base import BaseProvider
from llm_gateway.providers.mock import MockProvider
from llm_gateway.providers.openai_compatible import OpenAICompatibleProvider
from llm_gateway.settings import ProviderConfig, load_app_config
from llm_gateway.utils.ids import new_request_id


def _load_providers(configs: list[ProviderConfig]) -> dict[str, BaseProvider]:
    providers: dict[str, BaseProvider] = {}
    for config in configs:
        if config.type == "mock":
            providers[config.name] = MockProvider(name=config.name)
        elif config.type in {"openai", "openai_compatible"}:
            providers[config.name] = OpenAICompatibleProvider(
                name=config.name,
                base_url=config.base_url,
                api_key_env=config.api_key_env,
                timeout=config.timeout,
            )
    return providers


def create_app() -> FastAPI:
    app_config = load_app_config()
    configure_logging(app_config.gateway.logging)

    app = FastAPI(
        title="LLM Gateway",
        version="0.1.0",
        description="OpenAI-compatible LLM Gateway V0.1",
    )
    register_error_handlers(app)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or new_request_id()
        request.state.request_id = request_id
        response = await request_logging_middleware(request, call_next)
        response.headers["x-request-id"] = request_id
        return response

    route_resolver = ModelRouter(app_config.routes)
    providers = _load_providers(app_config.providers)

    app.state.settings = app_config.settings
    app.state.route_resolver = route_resolver
    app.state.dispatcher = ChatDispatcher(
        route_resolver=route_resolver,
        providers=providers,
    )

    app.include_router(health_router)
    app.include_router(models_router, prefix="/v1")
    app.include_router(chat_router, prefix="/v1")
    return app


app = create_app()
