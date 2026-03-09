# Actuator Control Service

Servizio di controllo attuatori per la Mars Habitat Automation Platform.

## Responsabilità

- Sottoscrive i comandi degli attuatori da RabbitMQ (pubblicati dall'automation-engine)
- Esegue i comandi chiamando l'API REST del simulatore IoT
- Mantiene uno stato in-memory degli attuatori
- Registra tutti i comandi eseguiti nel database PostgreSQL (tabella `actuator_commands`)
- Espone API REST per controllo manuale e ispezione stato

## Endpoint API REST

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check del servizio con statistiche |
| `/actuators` | GET | Lista stati attuatori (aggiornati dal simulatore) |
| `/actuators/{id}` | GET | Stato di un attuatore specifico |
| `/actuators/{id}` | POST | Controllo manuale attuatore (body: `{"state": "ON"|"OFF"}`) |
| `/actuators/{id}/history` | GET | Storico comandi per attuatore |

## Flusso di Esecuzione

```
RabbitMQ (commands.actuator.#)
        ↓
    Ricezione messaggio
        ↓
    Parsing comando JSON
        ↓
    Verifica stato attuale (skip se invariato)
        ↓
    Chiamata API simulatore (/api/actuators/{id})
        ↓
    Aggiornamento cache in-memory
        ↓
    Log nel database (actuator_commands)
        ↓
    ACK messaggio RabbitMQ
```

## Modello Comando (da RabbitMQ)

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

## Controllo Manuale

Per controllare manualmente un attuatore:

```bash
curl -X POST http://localhost:8005/actuators/cooling_fan \
  -H "Content-Type: application/json" \
  -d '{"state": "ON"}'
```

Il servizio:
1. Chiama il simulatore IoT
2. Aggiorna la cache locale
3. Registra il comando con source="manual"

## Database: Tabella actuator_commands

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| id | BIGSERIAL | Identificativo univoco |
| actuator_id | VARCHAR(100) | ID attuatore |
| previous_state | VARCHAR(20) | Stato precedente |
| new_state | VARCHAR(20) | Nuovo stato |
| source | VARCHAR(50) | Fonte: "automation-engine" o "manual" |
| reason | TEXT | Motivazione (es. regola triggerata) |
| rule_id | INTEGER | ID regola (se automatizzato) |
| executed_at | TIMESTAMP | Data/ora esecuzione |

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `SIMULATOR_URL` | `http://localhost:8080` | URL del simulatore IoT |
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | Connessione PostgreSQL |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome exchange RabbitMQ |
| `COMMAND_ROUTING_KEY` | `commands.actuator.#` | Routing key per comandi |
| `HOST` | `0.0.0.0` | Host server HTTP |
| `PORT` | `8005` | Porta server HTTP |

## Configurazione Docker Compose

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

## Dipendenze Python

- `fastapi`: Framework web asincrono
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `httpx`: Client HTTP async per chiamate al simulatore
- `sqlalchemy`: ORM async per PostgreSQL
- `asyncpg`: Driver async PostgreSQL
- `pydantic`: Validazione dati

## Statistiche

Il servizio traccia le seguenti statistiche:
- `commands_received`: Comandi ricevuti da RabbitMQ
- `commands_executed`: Comandi eseguiti con successo
- `commands_failed`: Comandi falliti