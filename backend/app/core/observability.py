import logging

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import Settings

logger = logging.getLogger(__name__)


def setup_observability(app, settings: Settings) -> None:
    service_name = getattr(settings, "OTEL_SERVICE_NAME", "activia-trace")
    resource = Resource.create({"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    exporter_type = getattr(settings, "OTEL_TRACES_EXPORTER", "none")
    if exporter_type == "console":
        tracer_provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    FastAPIInstrumentor.instrument_app(app)
    logger.info("OpenTelemetry instrumentation initialized")
