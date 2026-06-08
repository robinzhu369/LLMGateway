from fastapi import APIRouter

from llm_gateway.api.deps import Authorized, RouteResolverDep

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models(
    _auth: Authorized,
    route_resolver: RouteResolverDep,
) -> dict[str, object]:
    return {
        "object": "list",
        "data": [
            {
                "id": route.alias,
                "object": "model",
                "created": 0,
                "owned_by": "llm-gateway",
            }
            for route in route_resolver.list_routes()
        ],
    }
