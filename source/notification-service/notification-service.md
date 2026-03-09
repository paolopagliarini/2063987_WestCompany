# Notification Service

Servizio di notifica real-time per la Mars Habitat Automation Platform.

## Responsabilità

- Riceve eventi normalizzati da RabbitMQ
- Genera notifiche per eventi con status `warning` o `critical`
- Genera notifiche quando una regola di automazione viene attivata
- Espone endpoint SSE per il frontend
- Mantiene uno storico in-memory delle ultime 100 notifiche

## Flusso Dati

```
RabbitMQ (events.#)
        ↓
    Ricezione tutti gli eventi
        ↓
    Parsing e generazione notifica
        ↓
    Salvataggio in memoria (ultime 100)
        ↓
    Broadcast a client SSE connessi
        ↓
    Frontend (EventSource)
```

## Endpoint API REST

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

**Connessione iniziale:**
Alla connessione, il servizio invia le ultime 10 notifiche per dare contesto al client.

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

## Generazione Notifiche

Il servizio genera notifiche basandosi sul contenuto dell'evento:

### Eventi con status warning/critical
```python
if status == "warning":
    severity = "warning"
    message = f"⚠️ {sensor_id}: {metric} = {value} {unit} (WARNING)"
elif status == "critical":
    severity = "critical"
    message = f"🚨 {sensor_id}: {metric} = {value} {unit} (CRITICAL)"
```

### Eventi da regola attivata
Quando un evento contiene `rule_id` e `actuator_id`:
```python
if rule_id and actuator_id:
    severity = "warning"
    message = f"🔧 Rule '{rule_name}' triggered: {sensor_id} {metric}={value}{unit} → {actuator_id}={actuator_action}"
```

## Endpoint: `/notifications`

Query delle notifiche con filtri opzionali:

```
GET /notifications?limit=50&severity=warning
```

Parametri:
- `limit`: Numero massimo di risultati (1-100, default: 50)
- `severity`: Filtra per severità (`info`, `warning`, `critical`)

Risposta:
```json
{
  "count": 10,
  "notifications": [
    { "notification_id": "...", "message": "...", ... }
  ]
}
```

## Endpoint: `/notifications/stats`

Statistiche aggregate sulle notifiche:

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

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome dell'exchange RabbitMQ |
| `ROUTING_KEY` | `events.#` | Routing key per sottoscrizione |
| `HOST` | `0.0.0.0` | Host del server HTTP |
| `PORT` | `8004` | Porta del server HTTP |

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

## Dipendenze Python

- `fastapi`: Framework web
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `pydantic`: Validazione dati

## Coda RabbitMQ

- Nome coda: `notification_queue`
- Durabilità: `durable=True`
- TTL messaggi: 24 ore (86400000 ms)
- Routing key: `events.#` (tutti gli eventi)

## Gestione Client SSE

Il servizio gestisce una lista di client connessi:
1. Nuova connessione: aggiunge una `asyncio.Queue` alla lista
2. Nuova notifica: invia a tutte le code
3. Timeout/disconnessione: rimuove la coda dalla lista

```python
# Broadcasting a tutti i client
async def broadcast_notification(notification: Notification):
    async with sse_clients_lock:
        for queue in sse_clients:
            await queue.put(notification)
```

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

## Storage In-Memory

- Massimo 100 notifiche in memoria (configurabile: `MAX_NOTIFICATIONS`)
- Utilizzo di `collections.deque` con `maxlen` per auto-evizione
- Persistenza solo durante il lifetime del processo (non persistente tra riavvii)

```python
from collections import deque
notifications_store: deque = deque(maxlen=MAX_NOTIFICATIONS)
```