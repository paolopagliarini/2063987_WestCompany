# Automation Engine

Automation engine for the Mars Habitat Automation Platform.

## Responsibilities

- Subscribes to normalized sensor events from RabbitMQ
- Loads active automation rules from PostgreSQL database
- Evaluates rule conditions against event values
- Publishes actuator commands when conditions are met
- Periodically reloads rules from the database

## Execution Flow

```
RabbitMQ (events.sensor.#)
        ↓
    Receive normalized event
        ↓
    JSON parsing (sensor_id, value, metric)
        ↓
    Filter matching rules (by sensor_id)
        ↓
    Evaluate condition (value OPERATOR threshold)
        ↓
    If true → Publish command to RabbitMQ
        ↓
    ACK message
```

## Event Model (Input)

```json
{
  "event_id": "uuid",
  "sensor_id": "greenhouse_temperature",
  "timestamp": "2036-03-05T12:45:00Z",
  "metric": "temperature",
  "value": 28.5,
  "unit": "C",
  "source": "rest",
  "status": "ok",
  "raw_schema": "rest.scalar.v1"
}
```

## Command Model (Output)

```json
{
  "command_id": "uuid",
  "actuator_id": "cooling_fan",
  "action": "ON",
  "source": "automation-engine",
  "rule_id": 1,
  "rule_name": "Temperature High",
  "triggered_by": {
    "sensor_id": "greenhouse_temperature",
    "metric": "temperature",
    "value": 28.5,
    "unit": "C",
    "operator": ">",
    "threshold": 28
  },
  "timestamp": "2036-03-05T12:45:00Z"
}
```

## Supported Operators

| Operator | Description |
|----------|-------------|
| `<` | Less than |
| `<=` | Less than or equal |
| `=` | Equal |
| `>` | Greater than |
| `>=` | Greater than or equal |

## Rule Matching

Rules are matched by `sensor_id`. The engine supports two modes:
1. Direct match: rule's `sensor_id` = event's `sensor_id`
2. Combined match: rule's `sensor_id` = event's `sensor_id_metric`

Example: If an event has `sensor_id: "hydroponic_ph"` and `metric: "ph"`, a rule with `sensor_id: "hydroponic_ph_ph"` will be matched.

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with status and statistics |
| `/rules/active` | GET | List active rules in cache |
| `/rules/reload` | POST | Force reload rules from DB |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | PostgreSQL connection |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | RabbitMQ connection URL |
| `EXCHANGE_NAME` | `mars_events` | RabbitMQ exchange name |
| `ROUTING_KEY` | `events.sensor.#` | Routing key for event subscription |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8002` | HTTP server port |
| `RULES_RELOAD_INTERVAL` | `30` | Rules reload interval (seconds) |

## Docker Compose Configuration

```yaml
automation-engine:
  build: ./automation-engine
  container_name: automation-engine
  restart: always
  environment:
    DATABASE_URL: postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat
    RABBITMQ_URL: amqp://mars_user:mars_password@messagging:5672/
    EXCHANGE_NAME: mars_events
    ROUTING_KEY: events.sensor.#
    HOST: 0.0.0.0
    PORT: 8002
    RULES_RELOAD_INTERVAL: 30
  ports:
    - "8002:8002"
  depends_on:
    database:
      condition: service_healthy
    messagging:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
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

## Rule Cache

Rules are loaded at startup and reloaded every `RULES_RELOAD_INTERVAL` seconds. This allows:
- Updating rules without restarting the service
- Dynamically enabling/disabling rules
- Minimizing database queries

## Statistics

The service tracks the following statistics:
- `events_received`: Events received from RabbitMQ
- `rules_evaluated`: Rules evaluated
- `rules_triggered`: Rules that met conditions
- `commands_published`: Commands published to actuators

## RabbitMQ Queue

- Queue name: `automation_engine_queue`
- Durability: `durable=True`
- Message TTL: 60 seconds (rules must be evaluated quickly)
- Prefetch count: 10

## Rule Example

Database: `automation_rules` table

```sql
INSERT INTO automation_rules (
    name, description, sensor_id, operator, threshold_value,
    threshold_unit, actuator_id, actuator_action, is_active
) VALUES (
    'Temperature High',
    'Activate cooling if temperature > 28C',
    'greenhouse_temperature',
    '>',
    28,
    'C',
    'cooling_fan',
    'ON',
    TRUE
);
```

When `greenhouse_temperature` reports a value > 28°C, the engine publishes a command to turn on `cooling_fan`.