from typing import Callable, ClassVar, NoReturn, TypeVar

from pydantic import AmqpDsn, Field, HttpUrl, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shiro.util.telemetry import OtelConfig, is_set_up, set_up_otel


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
    otel_collector_endpoint: HttpUrl | None = None
    otel_service_name: str = "shiro"

    @model_validator(mode="after")
    def set_up_telemetry(self) -> "OtelEnvConfig":
        if self.otel_collector_endpoint is not None and not is_set_up():
            set_up_otel(
                OtelConfig(
                    otel_collector_endpoint=self.otel_collector_endpoint,
                    otel_service_name=self.otel_service_name,
                )
            )
        return self


class EnvConfig(BrokerEnvConfig, OtelEnvConfig):
    pass
