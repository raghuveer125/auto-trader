"""OpenTelemetry tracing configuration for Stock Auto Trader API"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
import os

def init_tracing():
    """Initialize OpenTelemetry tracing with OTLP exporter"""
    
    # Create resource with service name
    resource = Resource.create({
        "service.name": "stock-auto-trader-backend",
        "service.version": "1.0.0"
    })
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # OTLP exporter endpoint
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4318")
    
    # Create OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Add span processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider

def instrument_app(app):
    """Instrument FastAPI app and dependencies"""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument requests library
    RequestsInstrumentor().instrument()
