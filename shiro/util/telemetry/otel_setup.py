import logging
from typing import ClassVar

from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel, ConfigDict, HttpUrl


class OtelConfig(BaseModel):
    otel_collector_endpoint: HttpUrl
    otel_service_name: str


class _OtelState(BaseModel):
    duration_histogram: metrics.Histogram

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )


_state: _OtelState | None = None


def set_up_otel(otel_config: OtelConfig):
    global _state
    if _state is not None:
        raise RuntimeError("OTEL is already set up.")

    resource = Resource(
        attributes={SERVICE_NAME: otel_config.otel_service_name}
    )
    endpoint = str(otel_config.otel_collector_endpoint)

    trace_provider = TracerProvider(resource=resource)
    trace_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    meter_provider = MeterProvider(resource=resource)
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    meter_provider.add_metric_reader(
        PeriodicExportingMetricReader(metric_exporter)
    )
    metrics.set_meter_provider(meter_provider)

    log_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(log_provider)

    LoggingInstrumentor().instrument(set_logging_format=True)

    meter = metrics.get_meter(otel_config.otel_service_name)

    duration_histogram = meter.create_histogram(
        "function.duration", unit="ms", description="Function execution time"
    )

    _state = _OtelState(duration_histogram=duration_histogram)


def is_set_up() -> bool:
    """Telemetry is optional: without set_up_otel() the tracer and meter
    below are the SDK's no-op defaults and nothing is exported."""
    return _state is not None


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)


def get_duration_histogram() -> metrics.Histogram | None:
    return _state.duration_histogram if _state is not None else None
