/**
 * Frontend OpenTelemetry tracing configuration
 * Automatically instruments fetch and XMLHttpRequest calls
 */

import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor, WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

export function initTracingWeb() {
  const exporter = new OTLPTraceExporter({
    url: import.meta.env.VITE_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
    headers: {
      // Avoid CORS issues with credentials
      'Content-Type': 'application/json',
    },
  });

  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'stock-auto-trader-frontend',
      [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    }),
  );

  const tracerProvider = new WebTracerProvider({
    resource: resource,
  });

  tracerProvider.addSpanProcessor(new BatchSpanProcessor(exporter));
  tracerProvider.register();

  registerInstrumentations({
    instrumentations: [
      new FetchInstrumentation({
        // Don't trace internal OTLP requests to avoid recursion
        requestHook: (span, request) => {
          if (request.url?.includes('localhost:4318')) {
            return false;
          }
        },
      }),
      new XMLHttpRequestInstrumentation({
        requestHook: (span, request) => {
          if (request.url?.includes('localhost:4318')) {
            return false;
          }
        },
      }),
    ],
  });

  console.log('OpenTelemetry tracing initialized for frontend');
  return tracerProvider;
}
