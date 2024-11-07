### Steps

### Pre-requisites

#### Jaeger
Run `jaeger` all-in-one docker deployment

```
docker run -d --rm --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:1.57
```

#### Vault

```
# Spin up vault container
docker run --cap-add=IPC_LOCK -d --name=dev-vault -e VAULT_DEV_ROOT_TOKEN_ID="myvault"  -p 8200:8200 hashicorp/vault

# Exec into vault
docker exec -it dev-vault /bin/sh

# Update vault addr to http
export VAULT_ADDR='http://127.0.0.1:8200'

# login
vault login myvault

# Add the api key secret for the openweather
vault kv put secret/weather-app api_key="7abd0dca65b8c774e4da352fc178e90e"

# Verify secret
vault kv get secret/weather-app
```


Under auto/ folder, we have `auto_app.py`
To instrument it locally, 

Install the below packages
```
pip3 install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
```

Run it with the following command
```
opentelemetry-instrument \
    --traces_exporter console,otlp \
    --service_name auto-flask-weather-app \
    --exporter_otlp_endpoint 0.0.0.0:4317 \
    --exporter_otlp_insecure true \
    --metrics_exporter none \
    python3 auto_app.py
```    

To demonstrate manual instrumentation, go to manual/ folder
and run the manual_app.py

Jaeger UI can be accessed on `$JAEGER_URL:16686`