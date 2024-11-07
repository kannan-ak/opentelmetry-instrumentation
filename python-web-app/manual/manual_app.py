from flask import Flask, render_template, request, redirect, url_for
import requests
import hvac
import sys
import time

# importing opentelemetry packages for manual instrumentation
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from manual_database import init_db, add_search, get_recent_searches  # Import database functions



app = Flask(__name__)

BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'


# Tracing configuration
resource = Resource(attributes={
    "service.name": "manual-flask-web-app"
})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)


# Configure OTLP exporter to send traces to Jaeger
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)


# FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)

# Fetch api key from vault
def fetch_api_key(path):
    with tracer.start_as_current_span("fetch_api_key") as span:
        # Add span attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)        
        client = hvac.Client(url='http://127.0.0.1:8200', token='myvault')
        try: 
            # time.sleep(2)
            secret = client.secrets.kv.v2.read_secret_version(path=path)
            API_KEY = secret['data']['data']['api_key']
            return API_KEY
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            print(e.args)
            sys.exit(1)


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    # Create a span for the HTTP request
    with tracer.start_as_current_span("HTTP " + request.method) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("http.client_ip", request.remote_addr)

        if request.method == 'POST':
            API_KEY = fetch_api_key('weather-app')
            if not API_KEY:
                error = 'Could not retrieve API key from Vault.'
                recent_searches = get_recent_searches()
                return render_template('index.html', weather_data={'error': error}, recent_searches=recent_searches)

            city = request.form['city']
            params = {'q': city, 'appid': API_KEY, 'units': 'metric'}

            # Create a span for the weather API call
            with tracer.start_as_current_span("fetch_weather_data") as weather_span:
                weather_span.set_attribute("http.url", BASE_URL)
                weather_span.set_attribute("http.method", "GET")
                weather_span.set_attribute("weather.city", city)

                response = requests.get(BASE_URL, params=params)
                weather_span.set_attribute("http.status_code", response.status_code)
                
                if response.status_code == 200:
                    weather_data = response.json()
                    
                    # Add attributes to the span
                    weather_span.set_attribute("weather.temperature", weather_data['main']['temp'])
                    weather_span.set_attribute("weather.description", weather_data['weather'][0]['description'])
                    
                    # Update the db with the search result
                    add_search(
                        city=city,
                        temperature=weather_data['main']['temp'],
                        description=weather_data['weather'][0]['description']
                    )
                else:
                    weather_data = {'error': 'City not found or invalid API key.'}
                    weather_span.set_attribute("error", True)
                    weather_span.set_attribute("weather.error", weather_data['error'])

        recent_searches = get_recent_searches()
        return render_template('index.html', weather_data=weather_data, recent_searches=recent_searches)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8082)
