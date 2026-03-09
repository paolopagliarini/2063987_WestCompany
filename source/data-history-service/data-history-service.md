# Data History Service

Historical data persistence service for the Mars Habitat Automation Platform.

## Responsibilities

- Subscribes to normalized sensor events from RabbitMQ
- Persists readings to PostgreSQL database (`sensor_readings` table)
- Uses batch insert with buffering for performance optimization
- Exposes REST API for historical queries with filters and pagination
- Provides aggregation endpoints for analytics and trends

## Execution Flow

```
RabbitMQ (events.sensor.#)
        ↓
    Receive normalized event
        ↓
    Parse and add to buffer
        ↓
    If buffer >= BATCH_SIZE → immediate flush
        ↓
    Otherwise periodic flush (FLUSH_INTERVAL)
        ↓
    ACK message
```

## Batch Insert

The service uses an in-memory buffer with two flush triggers:
1. **Size**: When buffer reaches `BATCH_SIZE` (default: 20)
2. **Time**: Every `FLUSH_INTERVAL` seconds (default: 5.0)

This approach balances:
- Latency: data is available in DB within 5 seconds
- Throughput: reduces number of queries with batch inserts

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with DB status and statistics |
| `/history` | GET | Query history with filters and pagination |
| `/history/{sensor_id}` | GET | History for a specific sensor |
| `/history/{sensor_id}/aggregate` | GET | Temporal aggregations (avg, min, max) |
| `/sensors` | GET | List sensors with latest reading |

## Endpoint: `/history`

Query with optional filters:

```
GET /history?sensor_id=greenhouse_temperature&source=rest&start=2036-03-01T00:00:00Z&end=2036-03-09T23:59:59Z&limit=100&offset=0
```

Parameters:
- `sensor_id`: Filter by sensor ID
- `source`: Filter by source ("rest" or "stream")
- `start`: Start timestamp (ISO 8601)
- `end`: End timestamp (ISO 8601)
- `limit`: Maximum results (1-1000, default: 100)
- `offset`: Offset for pagination (default: 0)

Response:
```json
{
  "total": 1500,
  "count": 100,
  "offset": 0,
  "limit": 100,
  "readings": [
    {
      "id": 1,
      "sensor_id": "greenhouse_temperature",
      "value": 27.4,
      "unit": "C",
      "source": "rest",
      "recorded_at": "2036-03-09T12:45:00",
      "created_at": "2036-03-09T12:45:05"
    }
  ]
}
```

## Endpoint: `/history/{sensor_id}/aggregate`

Temporal aggregations:

```
GET /history/greenhouse_temperature/aggregate?interval=1h&start=2036-03-09T00:00:00Z
```

Supported intervals:
- `5m`: 5 minutes
- `15m`: 15 minutes
- `1h`: 1 hour
- `6h`: 6 hours
- `1d`: 1 day

Response:
```json
{
  "sensor_id": "greenhouse_temperature",
  "interval": "1h",
  "buckets": [
    {
      "timestamp": "2036-03-09T12:00:00",
      "avg": 27.5,
      "min": 26.8,
      "max": 28.2,
      "count": 60,
      "unit": "C"
    }
  ]
}
```

## Database: sensor_readings Table

| Field | Type | Description |
|-------|------|-------------|
| id | BIGSERIAL | Unique identifier |
| sensor_id | VARCHAR(100) | Sensor ID |
| value | DECIMAL(10,4) | Read value |
| unit | VARCHAR(20) | Unit of measurement |
| source | VARCHAR(50) | Source: "rest" or "stream" |
| recorded_at | TIMESTAMP | Reading timestamp |
| created_at | TIMESTAMP | DB insertion timestamp |

Indexes:
- `idx_sensor_readings_sensor_id` on `sensor_id`
- `idx_sensor_readings_recorded_at` on `recorded_at`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | PostgreSQL connection |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | RabbitMQ connection URL |
| `EXCHANGE_NAME` | `mars_events` | RabbitMQ exchange name |
| `ROUTING_KEY` | `events.sensor.#` | Routing key for subscription |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8006` | HTTP server port |
| `BATCH_SIZE` | `20` | Buffer size for batch insert |
| `FLUSH_INTERVAL` | `5.0` | Flush interval (seconds) |

## Docker Compose Configuration

```yaml
data-history-service:
  build: ./data-history-service
  container_name: data-history-service
  restart: always
  environment:
    DATABASE_URL: postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat
    RABBITMQ_URL: amqp://mars_user:mars_password@messagging:5672/
    EXCHANGE_NAME: mars_events
    ROUTING_KEY: events.sensor.#
    HOST: 0.0.0.0
    PORT: 8006
    BATCH_SIZE: 20
    FLUSH_INTERVAL: 5.0
  ports:
    - "8006:8006"
  depends_on:
    database:
      condition: service_healthy
    messagging:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Python Dependencies

- `fastapi`: Async web framework
- `uvicorn`: ASGI server
- `aio-pika`: Async client for RabbitMQ
- `sqlalchemy`: Async ORM for PostgreSQL
- `asyncpg`: Async PostgreSQL driver

## RabbitMQ Queue

- Queue name: `data_history_queue`
- Durability: `durable=True`
- Message TTL: 24 hours (86400000 ms)
- Prefetch count: 50 (high for throughput)

## Statistics

The service tracks:
- `events_received`: Events received from RabbitMQ
- `events_stored`: Events saved to database
- `events_failed`: Events with save errors

## Use Cases for Frontend

The service is designed to support:
1. **Historical charts**: Sensor trend visualization over time
2. **Anomaly analysis**: Identify anomalous patterns
3. **Reporting**: Generate aggregated reports
4. **Dashboard**: Latest values per sensor