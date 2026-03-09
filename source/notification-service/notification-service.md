# Notification Service

Real-time notification service for the Mars Habitat Automation Platform.

## Responsibilities

- Receives normalized events from RabbitMQ
- Generates notifications for events with `warning` or `critical` status
- Generates notifications when an automation rule is triggered
- Exposes SSE endpoint for frontend
- Maintains in-memory history of the last 100 alerts (no normal telemetry)

## Data Flow

```
RabbitMQ (events.#)
        ↓
    Receive all events
        ↓
    Parse and generate notification
        ↓
    Save to memory (last 100)
        ↓
    Broadcast to connected SSE clients
        ↓
    Frontend (EventSource)
```

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/notifications` | GET | List of latest notifications |
| `/notifications/stream` | GET | SSE endpoint for real-time notifications |
| `/notifications/stats` | GET | Notification statistics |

## SSE Endpoint: `/notifications/stream`

Server-Sent Events endpoint for receiving real-time notifications.

**Message format:**
```
event: connected
data: {"status": "connected", "timestamp": "2036-03-05T12:45:00Z"}

data: {"notification_id": "...", "sensor_id": "...", "message": "...", ...}

event: keepalive
data: {"timestamp": "2036-03-05T12:45:30Z"}
```

**Events sent:**
- `connected`: Connection confirmation
- `keepalive`: Heartbeat every 30 seconds
- Data: Notifications in JSON format

**Initial connection:**
On connection, the service sends the last 10 notifications to give context to the client.

## Notification Model

```json
{
  "notification_id": "uuid",
  "event_id": "uuid",
  "sensor_id": "greenhouse_temperature",
  "metric": "temperature",
  "value": 28.5,
  "unit": "C",
  "status": "warning",
  "rule_id": 1,
  "rule_name": "Temperature High",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON",
  "message": "Rule 'Temperature High' triggered: greenhouse_temperature temperature=28.5C → cooling_fan=ON",
  "timestamp": "2036-03-05T12:45:00Z",
  "severity": "warning"
}
```

**Severity levels:**
- `info`: Normal event (discarded, not saved as notification)
- `warning`: Value above threshold or rule triggered
- `critical`: Critical condition

## Notification Generation

The service generates notifications based on event content:

### Events with warning/critical status
```python
if status == "warning":
    severity = "warning"
    message = f"⚠️ {sensor_id}: {metric} = {value} {unit} (WARNING)"
elif status == "critical":
    severity = "critical"
    message = f"🚨 {sensor_id}: {metric} = {value} {unit} (CRITICAL)"
```

### Events from triggered rule
When an event contains `rule_id` and `actuator_id`:
```python
if rule_id and actuator_id:
    severity = "warning"
    message = f"🔧 Rule '{rule_name}' triggered: {sensor_id} {metric}={value}{unit} → {actuator_id}={actuator_action}"
```

## Endpoint: `/notifications`

Query notifications with optional filters:

```
GET /notifications?limit=50&severity=warning
```

Parameters:
- `limit`: Maximum results (1-100, default: 50)
- `severity`: Filter by severity (`info`, `warning`, `critical`)

Response:
```json
{
  "count": 10,
  "notifications": [
    { "notification_id": "...", "message": "...", ... }
  ]
}
```

## Endpoint: `/notifications/stats`

Aggregated notification statistics:

```json
{
  "total_notifications": 150,
  "by_severity": {
    "info": 80,
    "warning": 50,
    "critical": 20
  },
  "by_sensor": {
    "greenhouse_temperature": 45,
    "hydroponic_ph": 30,
    ...
  },
  "connected_clients": 3
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | RabbitMQ connection URL |
| `EXCHANGE_NAME` | `mars_events` | RabbitMQ exchange name |
| `ROUTING_KEY` | `events.#` | Routing key for subscription |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8004` | HTTP server port |

## Docker Compose Configuration

```yaml
notification-service:
  build: ./notification-service
  container_name: notification-service
  restart: always
  environment:
    RABBITMQ_URL: amqp://mars_user:mars_password@messagging:5672/
    EXCHANGE_NAME: mars_events
    ROUTING_KEY: events.#
    HOST: 0.0.0.0
    PORT: 8004
  ports:
    - "8004:8004"
  depends_on:
    messagging:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Python Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `aio-pika`: Async client for RabbitMQ
- `pydantic`: Data validation

## RabbitMQ Queue

- Queue name: `notification_queue`
- Durability: `durable=True`
- Message TTL: 24 hours (86400000 ms)
- Routing key: `events.#` (all events)

## SSE Client Management

The service manages a list of connected clients:
1. New connection: adds an `asyncio.Queue` to the list
2. New notification: sends to all queues
3. Timeout/disconnection: removes queue from list

```python
# Broadcasting to all clients
async def broadcast_notification(notification: Notification):
    async with sse_clients_lock:
        for queue in sse_clients:
            await queue.put(notification)
```

## Frontend Integration

Example SSE connection in JavaScript:

```javascript
const eventSource = new EventSource('http://localhost:8004/notifications/stream');

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to notification stream');
});

eventSource.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('Notification:', notification);
  // Update UI with notification
};

eventSource.addEventListener('keepalive', (event) => {
  console.log('Keepalive received');
});
```

## In-Memory Storage

- Maximum 100 notifications in memory (configurable: `MAX_NOTIFICATIONS`)
- Uses `collections.deque` with `maxlen` for auto-eviction
- Persistence only during process lifetime (not persistent across restarts)

```python
from collections import deque
notifications_store: deque = deque(maxlen=MAX_NOTIFICATIONS)
```