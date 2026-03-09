# Actuator Control Service

Actuator control service for the Mars Habitat Automation Platform.

## Responsibilities

- Subscribes to actuator commands from RabbitMQ (published by automation-engine)
- Executes commands by calling the IoT simulator REST API
- Maintains an in-memory state of actuators
- Logs all executed commands to the PostgreSQL database (`actuator_commands` table)
- Exposes REST API for manual control and state inspection

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check with statistics |
| `/actuators` | GET | List actuator states (updated from simulator) |
| `/actuators/{id}` | GET | State of a specific actuator |
| `/actuators/{id}` | POST | Manual actuator control (body: `{"state": "ON"|"OFF"}`) |
| `/actuators/{id}/history` | GET | Command history for an actuator |

## Execution Flow

```
RabbitMQ (commands.actuator.#)
        ↓
    Message received
        ↓
    JSON command parsing
        ↓
    Check current state (skip if unchanged)
        ↓
    Call simulator API (/api/actuators/{id})
        ↓
    Update in-memory cache
        ↓
    Log to database (actuator_commands)
        ↓
    ACK RabbitMQ message
```

## Command Model (from RabbitMQ)

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

## Manual Control

To manually control an actuator:

```bash
curl -X POST http://localhost:8005/actuators/cooling_fan \
  -H "Content-Type: application/json" \
  -d '{"state": "ON"}'
```

The service:
1. Calls the IoT simulator
2. Updates the local cache
3. Logs the command with source="manual"

## Database: actuator_commands Table

| Field | Type | Description |
|-------|------|-------------|
| id | BIGSERIAL | Unique identifier |
| actuator_id | VARCHAR(100) | Actuator ID |
| previous_state | VARCHAR(20) | Previous state |
| new_state | VARCHAR(20) | New state |
| source | VARCHAR(50) | Source: "automation-engine" or "manual" |
| reason | TEXT | Reason (e.g., triggered rule) |
| rule_id | INTEGER | Rule ID (if automated) |
| executed_at | TIMESTAMP | Execution timestamp |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMULATOR_URL` | `http://localhost:8080` | IoT simulator URL |
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | PostgreSQL connection |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | RabbitMQ connection URL |
| `EXCHANGE_NAME` | `mars_events` | RabbitMQ exchange name |
| `COMMAND_ROUTING_KEY` | `commands.actuator.#` | Routing key for commands |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8005` | HTTP server port |

## Docker Compose Configuration

```yaml
actuator-control-service:
  build: ./actuator-control-service
  container_name: actuator-control-service
  restart: always
  environment:
    SIMULATOR_URL: http://mars-iot-simulator:8080
    DATABASE_URL: postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat
    RABBITMQ_URL: amqp://mars_user:mars_password@messagging:5672/
    EXCHANGE_NAME: mars_events
    COMMAND_ROUTING_KEY: commands.actuator.#
    HOST: 0.0.0.0
    PORT: 8005
  ports:
    - "8005:8005"
  depends_on:
    database:
      condition: service_healthy
    messagging:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Python Dependencies

- `fastapi`: Async web framework
- `uvicorn`: ASGI server
- `aio-pika`: Async client for RabbitMQ
- `httpx`: Async HTTP client for simulator calls
- `sqlalchemy`: Async ORM for PostgreSQL
- `asyncpg`: Async PostgreSQL driver
- `pydantic`: Data validation

## Statistics

The service tracks the following statistics:
- `commands_received`: Commands received from RabbitMQ
- `commands_executed`: Successfully executed commands
- `commands_failed`: Failed commands