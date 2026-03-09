# Database Service

Data persistence service for the Mars Habitat Automation Platform.

## Responsibilities

- Provides PostgreSQL database for persistence
- Executes initialization script at startup
- Manages connections for all backend services

## Database Schema

### Table: automation_rules

Defines automation rules.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Rule name |
| description | TEXT | | Optional description |
| sensor_id | VARCHAR(100) | NOT NULL | Sensor ID to monitor |
| operator | VARCHAR(10) | NOT NULL, CHECK | Operator: `<`, `<=`, `=`, `>`, `>=` |
| threshold_value | DECIMAL(10,2) | NOT NULL | Threshold value |
| threshold_unit | VARCHAR(20) | | Unit of measurement |
| actuator_id | VARCHAR(100) | NOT NULL | Actuator ID to control |
| actuator_action | VARCHAR(20) | NOT NULL | Action: `ON` or `OFF` |
| is_active | BOOLEAN | DEFAULT TRUE | Rule active/inactive |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation date |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update date |

CHECK constraint:
```sql
CONSTRAINT valid_operator CHECK (operator IN ('<', '<=', '=', '>', '>='))
```

### Table: sensor_readings

Historical sensor readings.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique identifier |
| sensor_id | VARCHAR(100) | NOT NULL | Sensor ID |
| value | DECIMAL(10,4) | NOT NULL | Read value |
| unit | VARCHAR(20) | | Unit of measurement |
| source | VARCHAR(50) | | Source: "rest" or "stream" |
| recorded_at | TIMESTAMP | NOT NULL | Reading timestamp |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | DB insertion timestamp |

### Table: actuator_commands

Audit trail of executed commands.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique identifier |
| actuator_id | VARCHAR(100) | NOT NULL | Actuator ID |
| previous_state | VARCHAR(20) | | Previous state |
| new_state | VARCHAR(20) | NOT NULL | New state |
| source | VARCHAR(50) | | Source: "automation-engine" or "manual" |
| reason | TEXT | | Command reason |
| rule_id | INTEGER | FK → automation_rules.id | Rule ID (if automated) |
| executed_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Execution timestamp |

Foreign Key:
```sql
rule_id INTEGER REFERENCES automation_rules(id) ON DELETE SET NULL
```

## Indexes

```sql
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings(recorded_at);
CREATE INDEX idx_automation_rules_active ON automation_rules(is_active);
CREATE INDEX idx_automation_rules_sensor_id ON automation_rules(sensor_id);
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `mars_user` | Database username |
| `POSTGRES_PASSWORD` | `mars_password` | Database password |
| `POSTGRES_DB` | `mars_habitat` | Database name |
| `PGPORT` | `5432` | PostgreSQL internal port |

## Docker Compose Configuration

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

## Connection from Services

Backend services use SQLAlchemy async with the `asyncpg` driver:

```python
DATABASE_URL = "postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat"
```

The external port is 5433, but Docker containers use the internal port 5432.

## Initialization Script

The `init.sql` file is executed automatically at first container startup:
1. Creates tables `automation_rules`, `sensor_readings`, `actuator_commands`
2. Creates indexes for performance
3. (Optionally) inserts seed data for testing

## Docker Volumes

The `postgres_data` volume persists data across restarts:
- Data survives container restarts
- To reset the database, remove the volume: `docker volume rm postgres_data`

## Backup and Recovery

To export the database:
```bash
docker exec database pg_dump -U mars_user mars_habitat > backup.sql
```

To restore:
```bash
docker exec -i database psql -U mars_user mars_habitat < backup.sql
```

## Performance Considerations

- Indexes on `sensor_id` and `recorded_at` for fast historical queries
- Index on `automation_rules.is_active` for loading active rules
- `BIGSERIAL` for tables with high insert volume
- Connection pooling in backend services (pool_size=10, max_overflow=20)