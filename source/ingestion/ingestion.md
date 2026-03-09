# Ingestion Service

Data acquisition service for the Mars Habitat Automation Platform.

## Responsibilities

- Periodic polling of REST sensors from IoT simulator
- Subscription to 7 telemetry topics via SSE (Server-Sent Events)
- Normalization of all payloads to a unified schema
- Publishing normalized events to RabbitMQ
- In-memory cache of latest read values

## Data Flow

```
IoT Simulator (port 8080)
        ↓
    REST Polling (POLL_INTERVAL)
    SSE Streams (7 topics)
        ↓
    Schema Detection
        ↓
    Normalization (unified schema)
        ↓
    Publish to RabbitMQ (events.sensor.{sensor_id})
        ↓
    Consumers: automation-engine, data-history, notification-service
```

## Unified Event Schema

All data is normalized to this format:

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

Fields:
- `event_id`: Unique UUID for each event
- `sensor_id`: Sensor identifier
- `timestamp`: ISO 8601 timestamp
- `metric`: Metric name (e.g., "temperature", "ph")
- `value`: Numeric value
- `unit`: Unit of measurement
- `source`: "rest" (polling) or "stream" (telemetry)
- `status`: "ok" or "warning"
- `raw_schema`: Original schema (e.g., "rest.scalar.v1")

## REST Sensors and Schemas

| Sensor | Schema | Notes |
|--------|--------|-------|
| `greenhouse_temperature` | `rest.scalar.v1` | Single value |
| `entrance_humidity` | `rest.scalar.v1` | Single value |
| `co2_hall` | `rest.scalar.v1` | Single value |
| `corridor_pressure` | `rest.scalar.v1` | Single value |
| `hydroponic_ph` | `rest.chemistry.v1` | Measurements array |
| `air_quality_voc` | `rest.chemistry.v1` | Measurements array |
| `air_quality_pm25` | `rest.particulate.v1` | PM1, PM2.5, PM10 |
| `water_tank_level` | `rest.level.v1` | Percentage and liters |

## Telemetry Topics and Schemas

| Topic | Schema | Metrics |
|-------|--------|---------|
| `mars/telemetry/solar_array` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/power_bus` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/power_consumption` | `topic.power.v1` | power_kw, voltage_v, current_a, cumulative_kwh |
| `mars/telemetry/radiation` | `topic.environment.v1` | Measurements array |
| `mars/telemetry/life_support` | `topic.environment.v1` | Measurements array |
| `mars/telemetry/thermal_loop` | `topic.thermal_loop.v1` | temperature_c, flow_l_min |
| `mars/telemetry/airlock` | `topic.airlock.v1` | cycles_per_hour |

## Normalizers

### rest.scalar.v1
Direct single event:
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
One event per measurement in array:
```python
# Input: {"sensor_id": "hydroponic_ph", "measurements": [{"metric": "ph", "value": 6.5, "unit": "pH"}]}
# Output: [Event with metric="ph", value=6.5, unit="pH"]
```

### rest.particulate.v1
Three events: pm1, pm2.5, pm10:
```python
# Output: 3 events with metrics "pm1", "pm2.5", "pm10"
```

### rest.level.v1
Two events: percentage and liters:
```python
# Output: 2 events with metrics "level_pct" and "level_liters"
```

### topic.power.v1
Events for each power metric:
```python
# Output: 4 events (power_kw, voltage_v, current_a, cumulative_kwh)
```

### topic.environment.v1
One event per measurement in array.

### topic.thermal_loop.v1
Two events: temperature and flow.

### topic.airlock.v1
One event with `last_state` encoded in `status`.

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with RabbitMQ connection status |
| `/sensors/latest` | GET | Cache of all latest values |
| `/sensors/latest/{sensor_id}` | GET | Latest values for specific sensor |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMULATOR_URL` | `http://localhost:8080` | IoT simulator URL |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | RabbitMQ connection URL |
| `EXCHANGE_NAME` | `mars_events` | RabbitMQ exchange name |
| `POLL_INTERVAL` | `10` | REST polling interval (seconds) |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8001` | HTTP server port |

## Docker Compose Configuration

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

## Python Dependencies

- `fastapi`: Async web framework
- `uvicorn`: ASGI server
- `aio-pika`: Async client for RabbitMQ
- `httpx`: Async HTTP client for polling and SSE

## In-Memory Cache

The service maintains an in-memory cache:
- Key: `{sensor_id}_{metric}`
- Value: latest normalized event
- Accessible via `/sensors/latest`
- Used by frontend for real-time display

## Error Handling

- Automatic retry for RabbitMQ connections (every 5 seconds)
- Automatic retry for SSE connections (every 5 seconds)
- Error logging for unrecognized REST sensors
- Continues processing even if individual sensors fail

## RabbitMQ Publishing

Routing key: `events.sensor.{sensor_id}`

Example: For `greenhouse_temperature`, publishes to `events.sensor.greenhouse_temperature`

Exchange: Topic exchange `mars_events` (durable)

Consumers subscribe with patterns like:
- `events.sensor.#` - All sensor events
- `events.#` - All events