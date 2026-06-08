from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from llm_gateway.core.schemas import ProviderTarget


class Settings(BaseSettings):
    gateway_api_keys: str = ""
    gateway_config_dir: Path = Path("config")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_keys(self) -> set[str]:
        return {key.strip() for key in self.gateway_api_keys.split(",") if key.strip()}


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    redact_content: bool = True


class GatewayConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    observability: dict[str, Any] = Field(default_factory=dict)
    rag: dict[str, Any] = Field(default_factory=dict)
    agent: dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    name: str
    type: str
    base_url: str = ""
    api_key_env: str = ""
    timeout: float = 60.0


class RouteConfig(BaseModel):
    alias: str
    strategy: str = "priority"
    targets: list[ProviderTarget]


class AppConfig(BaseModel):
    settings: Settings
    gateway: GatewayConfig
    providers: list[ProviderConfig]
    routes: list[RouteConfig]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    if not isinstance(loaded, dict):
        msg = f"YAML config must be an object: {path}"
        raise ValueError(msg)
    return loaded


def load_app_config(settings: Settings | None = None) -> AppConfig:
    settings = settings or Settings()
    config_dir = settings.gateway_config_dir

    gateway_data = _read_yaml(config_dir / "gateway.yaml")
    providers_data = _read_yaml(config_dir / "providers.yaml")
    routes_data = _read_yaml(config_dir / "routes.yaml")

    return AppConfig(
        settings=settings,
        gateway=GatewayConfig.model_validate(gateway_data),
        providers=[
            ProviderConfig.model_validate(item) for item in providers_data.get("providers", [])
        ],
        routes=[RouteConfig.model_validate(item) for item in routes_data.get("routes", [])],
    )
