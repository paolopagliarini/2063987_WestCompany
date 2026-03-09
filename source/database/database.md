# Database Service

Servizio di persistenza dati per la Mars Habitat Automation Platform.

## Responsabilità

- Fornisce database PostgreSQL per la persistenza
- Esegue lo script di inizializzazione allo startup
- Gestisce la connessione per tutti i servizi backend

## Schema del Database

### Tabella: automation_rules

Definisce le regole di automazione.

| Campo | Tipo | Vincoli | Descrizione |
|-------|------|---------|-------------|
| id | SERIAL | PRIMARY KEY | Identificativo univoco |
| name | VARCHAR(100) | NOT NULL | Nome della regola |
| description | TEXT | | Descrizione opzionale |
| sensor_id | VARCHAR(100) | NOT NULL | ID sensore da monitorare |
| operator | VARCHAR(10) | NOT NULL, CHECK | Operatore: `<`, `<=`, `=`, `>`, `>=` |
| threshold_value | DECIMAL(10,2) | NOT NULL | Valore soglia |
| threshold_unit | VARCHAR(20) | | Unità di misura |
| actuator_id | VARCHAR(100) | NOT NULL | ID attuatore da controllare |
| actuator_action | VARCHAR(20) | NOT NULL | Azione: `ON` o `OFF` |
| is_active | BOOLEAN | DEFAULT TRUE | Regola attiva/disattiva |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data creazione |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data ultima modifica |

Vincolo CHECK:
```sql
CONSTRAINT valid_operator CHECK (operator IN ('<', '<=', '=', '>', '>='))
```

### Tabella: sensor_readings

Storico delle letture sensori.

| Campo | Tipo | Vincoli | Descrizione |
|-------|------|---------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Identificativo univoco |
| sensor_id | VARCHAR(100) | NOT NULL | ID sensore |
| value | DECIMAL(10,4) | NOT NULL | Valore letto |
| unit | VARCHAR(20) | | Unità di misura |
| source | VARCHAR(50) | | Fonte: "rest" o "stream" |
| recorded_at | TIMESTAMP | NOT NULL | Timestamp della lettura |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp inserimento DB |

### Tabella: actuator_commands

Audit trail dei comandi eseguiti.

| Campo | Tipo | Vincoli | Descrizione |
|-------|------|---------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Identificativo univoco |
| actuator_id | VARCHAR(100) | NOT NULL | ID attuatore |
| previous_state | VARCHAR(20) | | Stato precedente |
| new_state | VARCHAR(20) | NOT NULL | Nuovo stato |
| source | VARCHAR(50) | | Fonte: "automation-engine" o "manual" |
| reason | TEXT | | Motivazione del comando |
| rule_id | INTEGER | FK → automation_rules.id | ID regola (se automatizzato) |
| executed_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp esecuzione |

Foreign Key:
```sql
rule_id INTEGER REFERENCES automation_rules(id) ON DELETE SET NULL
```

## Indici

```sql
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings(recorded_at);
CREATE INDEX idx_automation_rules_active ON automation_rules(is_active);
CREATE INDEX idx_automation_rules_sensor_id ON automation_rules(sensor_id);
```

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `POSTGRES_USER` | `mars_user` | Nome utente database |
| `POSTGRES_PASSWORD` | `mars_password` | Password database |
| `POSTGRES_DB` | `mars_habitat` | Nome database |
| `PGPORT` | `5432` | Porta interna PostgreSQL |

## Configurazione Docker Compose

```yaml
database:
  image: postgres:16
  container_name: database
  restart: always
  environment:
    POSTGRES_USER: mars_user
    POSTGRES_PASSWORD: mars_password
    POSTGRES_DB: mars_habitat
  ports:
    - "5433:5432"
  volumes:
    - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U mars_user -d mars_habitat"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Connessione dai Servizi

I servizi backend usano SQLAlchemy async con il driver `asyncpg`:

```python
DATABASE_URL = "postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat"
```

La porta esterna è 5433, ma i container Docker usano la porta interna 5432.

## Script di Inizializzazione

Il file `init.sql` viene eseguito automaticamente al primo avvio del container:
1. Crea le tabelle `automation_rules`, `sensor_readings`, `actuator_commands`
2. Crea gli indici per performance
3. (Opzionalmente) inserisce dati seed per testing

## Volumi Docker

Il volume `postgres_data` persiste i dati tra riavvii:
- I dati sopravvivono ai riavvii del container
- Per resettare il database, rimuovere il volume: `docker volume rm postgres_data`

## Backup e Recovery

Per esportare il database:
```bash
docker exec database pg_dump -U mars_user mars_habitat > backup.sql
```

Per ripristinare:
```bash
docker exec -i database psql -U mars_user mars_habitat < backup.sql
```

## Considerazioni di Performance

- Indici su `sensor_id` e `recorded_at` per query storiche veloci
- Indice su `automation_rules.is_active` per caricamento regole attive
- `BIGSERIAL` per tabelle con alto volume di inserimenti
- Connection pooling nei servizi backend (pool_size=10, max_overflow=20)