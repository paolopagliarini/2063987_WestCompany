# Automation Engine

Motore di automazione per la Mars Habitat Automation Platform.

## Responsabilità

- Sottoscrive eventi normalizzati dei sensori da RabbitMQ
- Carica le regole di automazione attive dal database PostgreSQL
- Valuta le condizioni delle regole contro i valori degli eventi
- Pubblica comandi per gli attuatori quando le condizioni sono soddisfatte
- Ricarica periodicamente le regole dal database

## Flusso di Esecuzione

```
RabbitMQ (events.sensor.#)
        ↓
    Ricezione evento normalizzato
        ↓
    Parsing JSON (sensor_id, value, metric)
        ↓
    Filtro regole matching (per sensor_id)
        ↓
    Valutazione condizione (value OPERATOR threshold)
        ↓
    Se vero → Pubblica comando su RabbitMQ
        ↓
    ACK messaggio
```

## Modello Evento (Input)

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

## Modello Comando (Output)

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

## Operatori Supportati

| Operatore | Descrizione |
|-----------|-------------|
| `<` | Minore di |
| `<=` | Minore o uguale |
| `=` | Uguale |
| `>` | Maggiore di |
| `>=` | Maggiore o uguale |

## Matching Regole

Le regole vengono matchate per `sensor_id`. Il motore supporta due modalità:
1. Match diretto: `sensor_id` della regola = `sensor_id` dell'evento
2. Match combinato: `sensor_id` della regola = `sensor_id_metric` dell'evento

Esempio: Se l'evento ha `sensor_id: "hydroponic_ph"` e `metric: "ph"`, una regola con `sensor_id: "hydroponic_ph_ph"` verrà matchata.

## Endpoint API REST

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check con stato e statistiche |
| `/rules/active` | GET | Lista regole attive in cache |
| `/rules/reload` | POST | Forza ricaricamento regole dal DB |

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | Connessione PostgreSQL |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome exchange RabbitMQ |
| `ROUTING_KEY` | `events.sensor.#` | Routing key per sottoscrizione eventi |
| `HOST` | `0.0.0.0` | Host server HTTP |
| `PORT` | `8002` | Porta server HTTP |
| `RULES_RELOAD_INTERVAL` | `30` | Intervallo (secondi) di ricaricamento regole |

## Configurazione Docker Compose

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

## Dipendenze Python

- `fastapi`: Framework web asincrono
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `sqlalchemy`: ORM async per PostgreSQL
- `asyncpg`: Driver async PostgreSQL

## Cache Regole

Le regole vengono caricate all'avvio e ricaricate ogni `RULES_RELOAD_INTERVAL` secondi. Questo permette di:
- Aggiornare le regole senza riavviare il servizio
- Abilitare/disabilitare regole dinamicamente
- Minimizzare le query al database

## Statistiche

Il servizio traccia le seguenti statistiche:
- `events_received`: Eventi ricevuti da RabbitMQ
- `rules_evaluated`: Regole valutate
- `rules_triggered`: Regole che hanno soddisfatto la condizione
- `commands_published`: Comandi pubblicati verso gli attuatori

## Coda RabbitMQ

- Nome coda: `automation_engine_queue`
- Durabilità: `durable=True`
- TTL messaggi: 60 secondi (le regole devono essere valutate rapidamente)
- Prefetch count: 10

## Esempio di Regola

Database: Tabella `automation_rules`

```sql
INSERT INTO automation_rules (
    name, description, sensor_id, operator, threshold_value,
    threshold_unit, actuator_id, actuator_action, is_active
) VALUES (
    'Temperature High',
    'Attiva raffreddamento se temperatura > 28C',
    'greenhouse_temperature',
    '>',
    28,
    'C',
    'cooling_fan',
    'ON',
    TRUE
);
```

Quando `greenhouse_temperature` riporta un valore > 28°C, il motore pubblica un comando per accendere `cooling_fan`.