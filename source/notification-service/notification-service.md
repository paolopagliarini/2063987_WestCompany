# Notification Service

Servizio di notifica real-time per la Mars Habitat Automation Platform.

## Responsabilità

- Riceve eventi normalizzati da RabbitMQ
- Genera notifiche per eventi con status `warning` o `critical`
- Genera notifiche quando una regola di automazione viene attivata
- Espone endpoint SSE per il frontend
- Mantiene uno storico in-memory delle ultime 100 notifiche

## Endpoint API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check del servizio |
| `/notifications` | GET | Lista delle ultime notifiche |
| `/notifications/stream` | GET | SSE endpoint per notifiche real-time |
| `/notifications/stats` | GET | Statistiche sulle notifiche |

## Endpoint SSE: `/notifications/stream`

Endpoint Server-Sent Events per ricevere notifiche in tempo reale.

**Formato messaggi:**
```
event: connected
data: {"status": "connected", "timestamp": "2036-03-05T12:45:00Z"}

data: {"notification_id": "...", "sensor_id": "...", "message": "...", ...}

event: keepalive
data: {"timestamp": "2036-03-05T12:45:30Z"}
```

**Eventi inviati:**
- `connected`: Conferma connessione
- `keepalive`: Heartbeat ogni 30 secondi
- Dati: Notifiche in formato JSON

## Modello Notifica

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

**Livelli di severità:**
- `info`: Evento normale
- `warning`: Valore oltre soglia o regola attivata
- `critical`: Condizione critica

## Configurazione Docker Compose

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

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome dell'exchange RabbitMQ |
| `ROUTING_KEY` | `events.#` | Routing key per sottoscrizione |
| `HOST` | `0.0.0.0` | Host del server HTTP |
| `PORT` | `8004` | Porta del server HTTP |

## Dipendenze

- `fastapi`: Framework web
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `pydantic`: Validazione dati

## Integrazione Frontend

Esempio di connessione SSE in JavaScript:

```javascript
const eventSource = new EventSource('http://localhost:8004/notifications/stream');

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to notification stream');
});

eventSource.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('Notification:', notification);
  // Aggiorna UI con la notifica
};

eventSource.addEventListener('keepalive', (event) => {
  console.log('Keepalive received');
});
```