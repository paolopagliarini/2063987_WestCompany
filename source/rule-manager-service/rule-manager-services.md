# Rule Manager Service

Rule management service for the Mars Habitat Automation Platform.

## Responsibilities

- Provides CRUD REST API for automation rules
- Validation of rule syntax (operators, actions)
- Persistence to PostgreSQL
- Endpoint for enabling/disabling rules

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with DB status |
| `/rules` | GET | List all rules |
| `/rules` | POST | Create new rule |
| `/rules/{id}` | GET | Rule details |
| `/rules/{id}` | PUT | Update rule (partial update) |
| `/rules/{id}` | DELETE | Delete rule |
| `/rules/{id}/toggle` | PATCH | Enable/disable rule |

## Rule Model

```json
{
  "id": 1,
  "name": "Temperature High",
  "description": "Activate cooling if temperature > 28C",
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

## Validation

### Supported Operators

```python
VALID_OPERATORS = ("<", "<=", "=", ">", ">=")
```

### Supported Actions

```python
VALID_ACTIONS = ("ON", "OFF")
```

Validation is performed via Pydantic:
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

## Rule Creation

**Request:**
```bash
POST /rules
Content-Type: application/json

{
  "name": "Temperature High",
  "description": "Activate cooling if temperature > 28C",
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
  "description": "Activate cooling if temperature > 28C",
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

## Rule Update

**Request (Partial Update):**
```bash
PUT /rules/1
Content-Type: application/json

{
  "threshold_value": 30.0,
  "is_active": false
}
```

Only provided fields are updated.

## Rule Toggle

```bash
PATCH /rules/1/toggle
```

Activates if inactive, deactivates if active. Useful for quick activation without body.

**Response:**
```json
{
  "id": 1,
  "is_active": false
}
```

## Rule Deletion

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

## Database Schema

`automation_rules` table:

| Field | Type | Constraints |
|-------|------|-------------|
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

CHECK constraint:
```sql
CONSTRAINT valid_operator CHECK (operator IN ('<', '<=', '=', '>', '>='))
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat` | PostgreSQL connection |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8003` | HTTP server port |

## Docker Compose Configuration

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

## Python Dependencies

- `fastapi`: Async web framework
- `uvicorn`: ASGI server
- `sqlalchemy`: Async ORM for PostgreSQL
- `asyncpg`: Async PostgreSQL driver
- `pydantic`: Data validation

## Pydantic Schemas

### RuleCreate
For creating new rules:
```python
class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sensor_id: str
    operator: str  # Validated: <, <=, =, >, >=
    threshold_value: float
    threshold_unit: Optional[str] = None
    actuator_id: str
    actuator_action: str  # Validated: ON, OFF
```

### RuleUpdate
For partial updates:
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

## Integration with Automation Engine

The automation engine:
1. Loads active rules (`is_active = TRUE`) at startup
2. Periodically reloads every `RULES_RELOAD_INTERVAL` seconds
3. Evaluates conditions of incoming events
4. Publishes commands to actuators when conditions are met

The Rule Manager does not communicate directly with the automation engine - synchronization occurs through the database.

## Best Practices

1. **Descriptive names**: Use clear names for rules
2. **Descriptions**: Document the purpose of the rule
3. **Consistent units**: Always specify the unit of measurement
4. **Testing**: Verify rules with real data before activating them
5. **Monitoring**: Check automation engine logs to verify activations

## Rule Examples

### Temperature Control
```json
{
  "name": "Temperature High",
  "description": "Activate cooling if temperature > 28C",
  "sensor_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "ON"
}
```

### CO2 Control
```json
{
  "name": "CO2 High",
  "description": "Activate ventilation if CO2 > 1000 ppm",
  "sensor_id": "co2_hall",
  "operator": ">",
  "threshold_value": 1000,
  "threshold_unit": "ppm",
  "actuator_id": "ventilation",
  "actuator_action": "ON"
}
```

### Automatic Deactivation
```json
{
  "name": "Temperature Normal",
  "description": "Turn off cooling if temperature < 25C",
  "sensor_id": "greenhouse_temperature",
  "operator": "<",
  "threshold_value": 25,
  "threshold_unit": "C",
  "actuator_id": "cooling_fan",
  "actuator_action": "OFF"
}
```