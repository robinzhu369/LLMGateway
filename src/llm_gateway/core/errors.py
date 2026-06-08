from typing import Any


class OpenAIError(Exception):
    def __init__(
        self,
        *,
        message: str,
        status_code: int = 400,
        error_type: str = "invalid_request_error",
        code: str | None = None,
        param: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.param = param


def openai_error_payload(
    *,
    message: str,
    error_type: str,
    code: str | None = None,
    param: str | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "message": message,
        "type": error_type,
        "code": code,
    }
    if param is not None:
        error["param"] = param
    return {"error": error}

