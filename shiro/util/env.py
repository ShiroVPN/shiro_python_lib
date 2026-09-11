from typing import Callable, ClassVar, NoReturn

from pydantic import AmqpDsn, Field, HttpUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def require(var_name: str) -> Callable[[], NoReturn]:
    def r() -> NoReturn:
        raise ValueError(f"Set {var_name.upper()} in .env")

    return r


class BaseEnvConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", case_sensitive=False
    )


class BrokerEnvConfig(BaseEnvConfig):
    broker_url: AmqpDsn = Field(default_factory=require("broker_url"))
    broker_result_backend_url: RedisDsn = Field(
        default_factory=require("backend_url")
    )


class OtelEnvConfig(BaseEnvConfig):
    otel_collector_endpoint: HttpUrl = Field(
        default_factory=require("otel_collector_endpoint")
    )
    otel_service_name: str = Field(default_factory=require("otel_service_name"))


class EnvConfig(BrokerEnvConfig, OtelEnvConfig):
    pass
