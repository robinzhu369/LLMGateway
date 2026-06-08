from fastapi import Request

from llm_gateway.core.errors import OpenAIError


async def require_api_key(request: Request) -> str:
    configured_keys: set[str] = request.app.state.settings.api_keys
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if token:
        request.state.api_key_prefix = mask_api_key(token)

    if scheme.lower() != "bearer" or not token or token not in configured_keys:
        raise OpenAIError(
            message="Invalid or missing API key.",
            status_code=401,
            error_type="authentication_error",
            code="invalid_api_key",
        )
    return token


def mask_api_key(api_key: str) -> str:
    suffix = api_key[-4:] if len(api_key) >= 4 else api_key
    if api_key.startswith("sk-gw-"):
        return f"sk-gw-****{suffix}"
    return f"****{suffix}"
