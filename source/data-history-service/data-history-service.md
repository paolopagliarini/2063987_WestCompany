# Data History Service

Servizio di persistenza storica per la Mars Habitat Automation Platform.

## Responsabilità

- Sottoscrive eventi normalizzati dei sensori da RabbitMQ
- Persiste le letture nel database PostgreSQL (tabella `sensor_readings`)
- Usa batch insert con buffering per ottimizzare le performance
- Espone API REST per query storiche con filtri e paginazione
- Fornisce endpoint di aggregazione per analytics e trend

## Flusso di Esecuzione

```
RabbitMQ (events.sensor.#)
        ↓
    Ricezione evento normalizzato
        ↓
    Parsing e aggiunta al buffer
        ↓
    Se buffer >= BATCH_SIZE → flush immediato
        ↓
    Altrimenti flush periodico (FLUSH_INTERVAL)
        ↓
    ACK messaggio
```

## Batch Insert

Il servizio utilizza un buffer in-memory con due trigger di flush:
1. **Dimensione**: Quando il buffer raggiunge `BATCH_SIZE` (default: 20)
2. **Tempo**: Ogni `FLUSH_INTERVAL` secondi (default: 5.0)

Questo approccio bilancia:
- Latenza: i dati sono disponibili nel DB entro 5 secondi
- Throughput: riduce il numero di query con insert batch

## Endpoint API REST

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check con stato DB e statistiche |
| `/history` | GET | Query storico con filtri e paginazione |
| `/history/{sensor_id}` | GET | Storico per sensore specifico |
| `/history/{sensor_id}/aggregate` | GET | Aggregazioni temporali (avg, min, max) |
| `/sensors` | GET | Lista sensori con ultima lettura |

## Endpoint: `/history`

Query con filtri opzionali:

```
GET /history?sensor_id=greenhouse_temperature&source=rest&start=2036-03-01T00:00:00Z&end=2036-03-09T23:59:59Z&limit=100&offset=0
```

Parametri:
- `sensor_id`: Filtra per ID sensore
- `source`: Filtra per fonte ("rest" o "stream")
- `start`: Timestamp inizio (ISO 8601)
- `end`: Timestamp fine (ISO 8601)
- `limit`: Numero massimo risultati (1-1000, default: 100)
- `offset: Offset per paginazione (default: 0)

Risposta:
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

Aggregazioni temporali:

```
GET /history/greenhouse_temperature/aggregate?interval=1h&start=2036-03-09T00:00:00Z
```

Intervalli supportati:
- `5m`: 5 minuti
- `15m`: 15 minuti
- `1h`: 1 ora
- `6h`: 6 ore
- `1d`: 1 giorno

Risposta:
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

## Database: Tabella sensor_readings

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| id | BIGSERIAL | Identificativo univoco |
| sensor_id | VARCHAR(100) | ID sensore |
| value | DECIMAL(10,4) | Valore letto |
| unit | VARCHAR(20) | Unità di misura |
| source | VARCHAR(50) | Fonte: "rest" o "stream" |
| recorded_at | TIMESTAMP | Timestamp della lettura |
| created_at | TIMESTAMP | Timestamp inserimento DB |

Indici:
- `idx_sensor_readings_sensor_id` su `sensor_id`
- `idx_sensor_readings_recorded_at` su `recorded_at`

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | Connessione PostgreSQL |
| `RABBITMQ_URL` | `amqp://guest:guest@messagging:5672/` | URL connessione RabbitMQ |
| `EXCHANGE_NAME` | `mars_events` | Nome exchange RabbitMQ |
| `ROUTING_KEY` | `events.sensor.#` | Routing key per sottoscrizione |
| `HOST` | `0.0.0.0` | Host server HTTP |
| `PORT` | `8006` | Porta server HTTP |
| `BATCH_SIZE` | `20` | Dimensione buffer per batch insert |
| `FLUSH_INTERVAL` | `5.0` | Intervallo flush (secondi) |

## Configurazione Docker Compose

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

## Dipendenze Python

- `fastapi`: Framework web asincrono
- `uvicorn`: Server ASGI
- `aio-pika`: Client async per RabbitMQ
- `sqlalchemy`: ORM async per PostgreSQL
- `asyncpg`: Driver async PostgreSQL

## Coda RabbitMQ

- Nome coda: `data_history_queue`
- Durabilità: `durable=True`
- TTL messaggi: 24 ore (86400000 ms)
- Prefetch count: 50 (alto per throughput)

## Statistiche

Il servizio traccia:
- `events_received`: Eventi ricevuti da RabbitMQ
- `events_stored`: Eventi salvati nel database
- `events_failed`: Eventi con errore di salvataggio

## Use Case per Frontend

Il servizio è progettato per supportare:
1. **Grafici storici**: Visualizzazione trend sensori nel tempo
2. **Analisi anomalie**: Identificazione pattern anomali
3. **Reportistica**: Generazione report aggregati
4. **Dashboard**: Ultimi valori per sensore