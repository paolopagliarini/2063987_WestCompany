# Rule Manager Service

Servizio di gestione regole per la Mars Habitat Automation Platform.

## Responsabilità

- Fornisce API REST CRUD per le regole di automazione
- Validazione della sintassi delle regole (operatori, azioni)
- Persistenza su PostgreSQL
- Endpoint per attivazione/disattivazione regole

## Endpoint API REST

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check con stato DB |
| `/rules` | GET | Lista tutte le regole |
| `/rules` | POST | Crea nuova regola |
| `/rules/{id}` | GET | Dettaglio regola |
| `/rules/{id}` | PUT | Aggiorna regola (partial update) |
| `/rules/{id}` | DELETE | Elimina regola |
| `/rules/{id}/toggle` | PATCH | Attiva/disattiva regola |

## Modello Regola

```json
{
  "id": 1,
  "name": "Temperature High",
  "description": "Attiva raffreddamento se temperatura > 28C",
  "sensor_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28.0,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON",
  "is_active": true,
  "created_at": "2036-03-05T10:00:00Z",
  "updated_at": "2036-03-05T12:00:00Z"
}
```

## Validazione

### Operatori Supportati

```python
VALID_OPERATORS = ("<", "<=", "=", ">", ">=")
```

### Azioni Supportate

```python
VALID_ACTIONS = ("ON", "OFF")
```

La validazione avviene tramite Pydantic:
```python
@field_validator("operator")
@classmethod
def validate_operator(cls, v):
    if v not in VALID_OPERATORS:
        raise ValueError(f"operator must be one of {VALID_OPERATORS}")
    return v

@field_validator("actuator_action")
@classmethod
def validate_action(cls, v):
    v_upper = v.upper()
    if v_upper not in ("ON", "OFF"):
        raise ValueError("actuator_action must be ON or OFF")
    return v_upper
```

## Creazione Regola

**Request:**
```bash
POST /rules
Content-Type: application/json

{
  "name": "Temperature High",
  "description": "Attiva raffreddamento se temperatura > 28C",
  "sensor_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28.0,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Temperature High",
  "description": "Attiva raffreddamento se temperatura > 28C",
  "sensor_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28.0,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON",
  "is_active": true,
  "created_at": "2036-03-05T10:00:00Z",
  "updated_at": "2036-03-05T10:00:00Z"
}
```

## Aggiornamento Regola

**Request (Partial Update):**
```bash
PUT /rules/1
Content-Type: application/json

{
  "threshold_value": 30.0,
  "is_active": false
}
```

Solo i campi forniti vengono aggiornati.

## Toggle Regola

```bash
PATCH /rules/1/toggle
```

Attiva se disattiva, disattiva se attiva. Utile per attivazione rapida senza body.

**Response:**
```json
{
  "id": 1,
  "is_active": false
}
```

## Eliminazione Regola

```bash
DELETE /rules/1
```

**Response:**
```json
{
  "message": "Rule deleted",
  "id": 1
}
```

## Schema Database

Tabella `automation_rules`:

| Campo | Tipo | Vincoli |
|-------|------|---------|
| id | SERIAL | PRIMARY KEY |
| name | VARCHAR(100) | NOT NULL |
| description | TEXT | |
| sensor_id | VARCHAR(100) | NOT NULL |
| operator | VARCHAR(10) | NOT NULL, CHECK |
| threshold_value | DECIMAL(10,2) | NOT NULL |
| threshold_unit | VARCHAR(20) | |
| actuator_id | VARCHAR(100) | NOT NULL |
| actuator_action | VARCHAR(20) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Constraint CHECK:
```sql
CONSTRAINT valid_operator CHECK (operator IN ('<', '<=', '=', '>', '>='))
```

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | Connessione PostgreSQL |
| `HOST` | `0.0.0.0` | Host server HTTP |
| `PORT` | `8003` | Porta server HTTP |

## Configurazione Docker Compose

```yaml
rule-manager-service:
  build: ./rule-manager-service
  container_name: rule-manager-service
  restart: always
  environment:
    DATABASE_URL: postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat
    HOST: 0.0.0.0
    PORT: 8003
  ports:
    - "8003:8003"
  depends_on:
    database:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Dipendenze Python

- `fastapi`: Framework web asincrono
- `uvicorn`: Server ASGI
- `sqlalchemy`: ORM async per PostgreSQL
- `asyncpg`: Driver async PostgreSQL
- `pydantic`: Validazione dati

## Pydantic Schemas

### RuleCreate
Per la creazione di nuove regole:
```python
class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sensor_id: str
    operator: str  # Validato: <, <=, =, >, >=
    threshold_value: float
    threshold_unit: Optional[str] = None
    actuator_id: str
    actuator_action: str  # Validato: ON, OFF
```

### RuleUpdate
Per aggiornamenti parziali:
```python
class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sensor_id: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_unit: Optional[str] = None
    actuator_id: Optional[str] = None
    actuator_action: Optional[str] = None
    is_active: Optional[bool] = None
```

## Integrazione con Automation Engine

L'automation engine:
1. Carica le regole attive (`is_active = TRUE`) all'avvio
2. Ricarica periodicamente ogni `RULES_RELOAD_INTERVAL` secondi
3. Valuta le condizioni degli eventi in arrivo
4. Pubblica comandi per gli attuatori quando le condizioni sono soddisfatte

Il Rule Manager non comunica direttamente con l'automation engine - la sincronizzazione avviene tramite il database.

## Best Practices

1. **Nomi descrittivi**: Usare nomi chiari per le regole
2. **Descrizioni**: Documentare lo scopo della regola
3. **Unità coerenti**: Specificare sempre l'unità di misura
4. **Test**: Verificare le regole con dati reali prima di attivarle
5. **Monitoraggio**: Controllare i log dell'automation engine per verificare le attivazioni

## Esempi di Regole

### Controllo Temperatura
```json
{
  "name": "Temperature High",
  "description": "Attiva raffreddamento se temperatura > 28C",
  "sensor_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON"
}
```

### Controllo CO2
```json
{
  "name": "CO2 High",
  "description": "Attiva ventilazione se CO2 > 1000 ppm",
  "sensor_id": "co2_hall",
  "operator": ">",
  "threshold_value": 1000,
  "threshold_unit": "ppm",
  "actuator_id": "ventilation",
  "actuator_action": "ON"
}
```

### Disattivazione Automatica
```json
{
  "name": "Temperature Normal",
  "description": "Spegni raffreddamento se temperatura < 25C",
  "sensor_id": "greenhouse_temperature",
  "operator": "<",
  "threshold_value": 25,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "OFF"
}
```