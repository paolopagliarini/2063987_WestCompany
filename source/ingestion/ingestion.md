# Ingestion Service

Servizio di acquisizione dati per la Mars Habitat Automation Platform.

## Responsabilità

- Polling periodico dei sensori REST dal simulatore IoT
- Sottoscrizione a 7 topic di telemetria via SSE (Server-Sent Events)
- Normalizzazione di tutti i payload in uno schema unificato
- Pubblicazione eventi normalizzati su RabbitMQ
- Cache in-memory degli ultimi valori letti

## Flusso Dati

```
IoT Simulator (port 8080)
        ↓
    Polling REST (POLL_INTERVAL)
    SSE Streams (7 topics)
        ↓
    Schema Detection
        ↓
    Normalizzazione (schema unificato)
        ↓
    Pubblicazione su RabbitMQ (events.sensor.{sensor_id})
        ↓
    Consumer: automation-engine, data-history, notification-service
```

## Schema Unificato Evento

Tutti i dati vengono normalizzati in questo formato:

```json
{
  "event_id": "uuid",
  "sensor_id": "greenhouse_temperature",
  "timestamp": "2036-03-05T12:45:00Z",
  "metric": "temperature",
  "value": 27.4,
  "unit": "C",
  "source": "rest",
  "status": "ok",
  "raw_schema": "rest.scalar.v1"
}
```

Campi:
- `event_id`: UUID univoco per ogni evento
- `sensor_id`: Identificativo del sensore
- `timestamp`: Timestamp ISO 8601
- `metric`: Nome della metrica (es. "temperature", "ph")
- `value`: Valore numerico
- `unit`: Unità di misura
- `source`: "rest" (polling) o "stream" (telemetria)
- `status`: "ok" o "warning"
- `raw_schema`: Schema originale (es. "rest.scalar.v1")

## Sensori REST e Schemi

| Sensore | Schema | Note |
|---------|--------|------|
| `greenhouse_temperature` | `rest.scalar.v1` | Singolo valore |
| `entrance_humidity` | `rest.scalar.v1` | Singolo valore |
| `co2_hall` | `rest.scalar.v1` | Singolo valore |
| `corridor_pressure` | `rest.scalar.v1` | Singolo valore |
| `hydroponic_ph` | `rest.chemistry.v1` | Array misurazioni |
| `air_quality_voc` | `rest.chemistry.v1` | Array misurazioni |
| `air_quality_pm25` | `rest.particulate.v1` | PM1, PM2.5, PM10 |
| `water_tank_level` | `rest.level.v1` | Percentuale e litri |

## Topic Telemetria e Schemi

| Topic | Schema | Metriche |
|-------|--------|----------|
| `mars/telemetry/solar_array` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/power_bus` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/power_consumption` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/radiation` | `topic.environment.v1` | Array misurazioni |
| `mars/telemetry/life_support` | `topic.environment.v1` | Array misurazioni |
| `mars/telemetry/thermal_loop` | `topic.thermal_loop.v1` | temperature_c, flow_l_min |
| `mars/telemetry/airlock` | `topic.airlock.v1` | cycles_per_hour |

## Normalizzatori

### rest.scalar.v1
Singolo evento diretto:
```python
def normalize_scalar(data: dict) -> list[dict]:
    return [_make_event(
        sensor_id=data["sensor_id"],
        timestamp=data.get("timestamp"),
        metric=data.get("metric", data["sensor_id"]),
        value=data["value"],
        unit=data.get("unit", ""),
        source="rest",
        status=data.get("status", "ok"),
        raw_schema="rest.scalar.v1",
    )]
```

### rest.chemistry.v1
Un evento per ogni misurazione nell'array:
```python
# Input: {"sensor_id": "hydroponic_ph", "measurements": [{"metric": "ph", "value": 6.5, "unit": "pH"}]}
# Output: [Evento con metric="ph", value=6.5, unit="pH"]
```

### rest.particulate.v1
Tre eventi: pm1, pm2.5, pm10:
```python
# Output: 3 eventi con metric "pm1", "pm2.5", "pm10"
```

### rest.level.v1
Due eventi: percentuale e litri:
```python
# Output: 2 eventi con metric "level_pct" e "level_liters"
```

### topic.power.v1
Eventi per ogni metrica di potenza:
```python
# Output: 4 eventi (power_kw, voltage_v, current_a, cumulative_kwh)
```

### topic.environment.v1
Un evento per ogni misurazione nell'array.

### topic.thermal_loop.v1
Due eventi: temperatura e flusso.

### topic.airlock.v1
Un evento con `last_state` codificato in `status`.

## Endpoint API REST

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check con stato connessione RabbitMQ |
| `/sensors/latest` | GET | Cache di tutti gli ultimi valori |
| `/sensors/latest/{sensor_id}` | GET | Ultimi valori per sensore specifico |

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `SIMULATOR_URL` | `http://localhost:8080` | URL del simulatore IoT |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome exchange RabbitMQ |
| `POLL_INTERVAL` | `10` | Intervallo polling REST (secondi) |
| `HOST` | `0.0.0.0` | Host server HTTP |
| `PORT` | `8001` | Porta server HTTP |

## Configurazione Docker Compose

```yaml
ingestion:
  build: ./ingestion
  container_name: ingestion
  restart: always
  environment:
    SIMULATOR_URL: http://mars-iot-simulator:8080
    RABBITMQ_URL: amqp://mars_user:mars_password@messagging:5672/
    EXCHANGE_NAME: mars_events
    POLL_INTERVAL: 10
    HOST: 0.0.0.0
    PORT: 8001
  ports:
    - "8001:8001"
  depends_on:
    messagging:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Dipendenze Python

- `fastapi`: Framework web asincrono
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `httpx`: Client HTTP async per polling e SSE

## Cache In-Memory

Il servizio mantiene una cache in-memory:
- Chiave: `{sensor_id}_{metric}`
- Valore: ultimo evento normalizzato
- Accessibile via `/sensors/latest`
- Utilizzata dal frontend per visualizzazione real-time

## Gestione Errori

- Retry automatico per connessioni RabbitMQ (ogni 5 secondi)
- Retry automatico per connessioni SSE (ogni 5 secondi)
- Log errori per sensori REST non riconosciuti
- Continua elaborazione anche in caso di errori su singoli sensori

## Pubblicazione RabbitMQ

Routing key: `events.sensor.{sensor_id}`

Esempio: Per `greenhouse_temperature`, pubblica su `events.sensor.greenhouse_temperature`

Exchange: Topic exchange `mars_events` (durable)

I consumer sottoscrivono con pattern come:
- `events.sensor.#` - Tutti gli eventi sensori
- `events.#` - Tutti gli eventi