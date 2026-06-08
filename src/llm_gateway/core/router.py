from llm_gateway.core.errors import OpenAIError
from llm_gateway.core.schemas import ProviderTarget
from llm_gateway.settings import RouteConfig


class ModelRouter:
    def __init__(self, routes: list[RouteConfig]) -> None:
        self._routes = {route.alias: route for route in routes}

    def list_routes(self) -> list[RouteConfig]:
        return sorted(self._routes.values(), key=lambda route: route.alias)

    def resolve(self, model_alias: str) -> ProviderTarget:
        route = self._routes.get(model_alias)
        if route is None or not route.targets:
            raise OpenAIError(
                message=f"Model alias is not configured: {model_alias}",
                status_code=404,
                error_type="invalid_request_error",
                code="model_not_found",
                param="model",
            )
        return route.targets[0]
