import os
from flask import Flask

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ImportError:
    trace = None
    OTLPSpanExporter = None
    FlaskInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None


def instrument(app: Flask) -> None:
    if not FlaskInstrumentor or not trace or not TracerProvider or not Resource:
        return

    FlaskInstrumentor().instrument_app(app)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    attrs_str = os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    attributes = {}
    if attrs_str:
        for item in attrs_str.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                attributes[key.strip()] = value.strip()

    resource = Resource.create(attributes)
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if endpoint and BatchSpanProcessor and OTLPSpanExporter:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
