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
import logging

logger = logging.getLogger(__name__)

def init_tracing():
    """Initialize OpenTelemetry tracing with OTLP exporter"""
    try:
        # Create resource with service name
        resource = Resource.create({
            "service.name": "stock-auto-trader-backend",
            "service.version": "1.0.0"
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # OTLP exporter endpoint
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
        logger.info(f"Initializing OpenTelemetry tracing with OTLP endpoint: {otlp_endpoint}")
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        
        # Add span processor
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry tracing initialized successfully")
        
        return tracer_provider
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}", exc_info=True)
        raise

def instrument_app(app):
    """Instrument FastAPI app and dependencies"""
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented")
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumented")
        
        # Instrument requests library
        RequestsInstrumentor().instrument()
        logger.info("Requests library instrumented")
    except Exception as e:
        logger.error(f"Failed to instrument app: {e}", exc_info=True)
