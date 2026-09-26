from typing import Callable, ClassVar, NoReturn, TypeVar

from pydantic import AmqpDsn, Field, HttpUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def require(var_name: str) -> Callable[[], NoReturn]:
    def r() -> NoReturn:
        raise ValueError(f"Set {var_name.upper()} in .env")

    return r


T = TypeVar("T")


def required_field(
    var_name: str,
) -> T:  # pyright: ignore[reportInvalidTypeVarUse]
    return Field(default_factory=require(var_name))


class BaseEnvConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", case_sensitive=False
    )


class BrokerEnvConfig(BaseEnvConfig):
    broker_url: AmqpDsn = required_field("broker_url")
    broker_result_backend_url: RedisDsn = required_field(
        "broker_result_backend_url"
    )


class OtelEnvConfig(BaseEnvConfig):
    # Unset = telemetry off (see shiro.util.telemetry.otel_setup.is_set_up).
    otel_collector_endpoint: HttpUrl | None = None
    otel_service_name: str = "shiro"


class EnvConfig(BrokerEnvConfig, OtelEnvConfig):
    pass
