from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from app.core.config import settings


def setup_telemetry(app, engine: AsyncEngine):
    resource = Resource.create({SERVICE_NAME: "inventory_service"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    AioHttpClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)