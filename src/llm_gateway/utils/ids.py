from uuid import uuid4


def new_request_id(prefix: str = "req") -> str:
    return f"{prefix}-{uuid4().hex}"

