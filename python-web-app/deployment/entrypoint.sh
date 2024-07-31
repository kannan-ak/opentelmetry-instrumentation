#!/bin/sh

# Run the Flask app with OpenTelemetry instrumentation
opentelemetry-instrument \
    --traces_exporter console \
    --service_name auto-k8s-flask-weather-app \
    --exporter_otlp_endpoint 0.0.0.0:4317 \
    --exporter_otlp_insecure true \
    --metrics_exporter none \
    python app.py