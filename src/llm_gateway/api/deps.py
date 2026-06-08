from typing import Annotated

from fastapi import Depends, Request

from llm_gateway.core.dispatcher import ChatDispatcher
from llm_gateway.core.router import ModelRouter
from llm_gateway.policy.auth import require_api_key


def get_dispatcher(request: Request) -> ChatDispatcher:
    return request.app.state.dispatcher


def get_route_resolver(request: Request) -> ModelRouter:
    return request.app.state.route_resolver


Authorized = Annotated[str, Depends(require_api_key)]
DispatcherDep = Annotated[ChatDispatcher, Depends(get_dispatcher)]
RouteResolverDep = Annotated[ModelRouter, Depends(get_route_resolver)]
