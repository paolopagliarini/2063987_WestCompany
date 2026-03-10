# SYSTEM DESCRIPTION:

The **Mars Habitat Automation Platform** is a distributed event-driven system designed to monitor and control a Mars habitat's critical infrastructure. The platform ingests heterogeneous sensor data from a simulated IoT environment - both REST-polled sensors and streaming telemetry topics - normalizes all payloads into a unified internal event format, evaluates automation rules, and exposes a real-time dashboard for habitat monitoring and control.

The system is composed of multiple decoupled microservices communicating through a message broker (RabbitMQ). Automation rules follow an IF–THEN model and are persisted in a PostgreSQL database so they survive service restarts. The latest state of each sensor is maintained in-memory for fast dashboard rendering. Actuators are controlled both manually (via the dashboard) and automatically (when a rule condition is triggered by an incoming sensor event).

# USER STORIES:

1. As an operator, I want to see the real-time value of all REST sensors on the dashboard, so that I can monitor habitat conditions at a glance.
2. As an operator, I want to see the real-time telemetry data from streaming topics (solar array, radiation, life support, thermal loop, power bus, airlock), so that I can monitor all critical subsystems.
3. As an operator, I want the dashboard to update automatically without refreshing the page, so that I always see the current state of the habitat.
4. As an operator, I want to see the current ON/OFF state of each actuator, so that I know what devices are active in the habitat.
5. As an operator, I want to manually toggle an actuator ON or OFF from the dashboard, so that I can directly control habitat devices without writing commands.
6. As an operator, I want to see the status indicator (ok / warning) for each sensor, so that I can immediately identify anomalies.
7. As an operator, I want to see a habitat health summary (number of warnings, number of active rules, actuator states overview), so that I can assess the overall system status at a glance.
8. As an operator, I want to see a live time chart of a sensor's values while the page is open, so that I can observe trends over time.
9. As an operator, I want to create an automation rule (IF sensor_name operator value THEN set actuator_name to ON/OFF), so that the system reacts automatically to environmental conditions.
10. As an operator, I want to view all existing automation rules in a list, so that I can understand what automations are currently configured.
11. As an operator, I want to edit an existing automation rule (change threshold, operator, or actuator action), so that I can adjust automations without deleting and recreating them.
12. As an operator, I want to delete an automation rule, so that I can remove outdated or incorrect automations.
13. As an operator, I want to enable or disable a rule without deleting it, so that I can temporarily suspend an automation and re-enable it later.
14. As an operator, I want the actuator state to change automatically when a rule condition is triggered by an incoming sensor event, so that the habitat is protected without manual intervention.
15. As an operator, I want to see when each actuator was last changed and whether the change was triggered manually or by a rule, so that I can audit the system's activity.
16. As an operator, I want to receive a real-time visual alert on the dashboard when a rule is triggered, so that I am immediately aware of critical environmental changes without having to watch every sensor.
17. As an operator, I want to see a log of the most recent rule-trigger events (which rule fired, when, and what sensor value caused it), so that I can audit the system's automated behavior.
18. As an operator, I want to filter the sensor view by category (environmental, power, chemical, physical), so that I can quickly focus on a specific subsystem without scrolling through all sensors.
19. As an operator, I want to see all individual measurements from multi-metric sensors displayed together (e.g. PM1, PM2.5, PM10 from air_quality_pm25), so that I have complete information from each device in one place.
20. As an operator, I want to see the connectivity status of each data source (online / offline / degraded), so that I can detect if a sensor or telemetry stream has stopped sending data.

# STANDARD INTERNAL EVENT SCHEMA

All incoming sensor data - regardless of the original device protocol or schema - is normalized into the following unified internal event format before being published to the message broker:

```json
{
  "event_id": "<uuid>",
  "sensor_id": "<string>",
  "timestamp": "<ISO 8601 datetime>",
  "metric": "<string>",
  "value": "<number>",
  "unit": "<string>",
  "source": "rest | stream",
  "status": "ok | warning",
  "raw_schema": "<original schema family, e.g. rest.scalar.v1>"
}
```

**Field descriptions:**

| Field | Type | Description |
| --- | --- | --- |
| `event_id` | string (UUID) | Unique identifier for this event instance |
| `sensor_id` | string | Identifier of the originating sensor or topic |
| `timestamp` | string (ISO 8601) | Time the reading was captured by the device |
| `metric` | string | Name of the measured quantity (e.g. `temperature`, `power_kw`) |
| `value` | number | Numeric value of the measurement |
| `unit` | string | Unit of measure (e.g. `C`, `ppm`, `kW`) |
| `source` | string | Origin type: `rest` for polled sensors, `stream` for telemetry topics |
| `status` | string | Device-reported status: `ok` or `warning` |
| `raw_schema` | string | Original schema family from SCHEMA_CONTRACT.md |

**Normalization notes:**

- `rest.scalar.v1` (greenhouse_temperature, entrance_humidity, co2_hall, corridor_pressure): one event, `metric` and `value` mapped directly from the payload.
- `rest.chemistry.v1` (hydroponic_ph, air_quality_voc): one normalized event emitted per entry in the `measurements` array.
- `rest.particulate.v1` (air_quality_pm25): three events emitted, one each for `pm1_ug_m3`, `pm25_ug_m3`, `pm10_ug_m3`.
- `rest.level.v1` (water_tank_level): two events emitted, one for `level_pct` (unit: `%`) and one for `level_liters` (unit: `L`).
- `topic.power.v1` (solar_array, power_bus, power_consumption): one event per power metric (`power_kw`, `voltage_v`, `current_a`, `cumulative_kwh`).
- `topic.environment.v1` (radiation, life_support): one event per entry in the `measurements` array.
- `topic.thermal_loop.v1`: two events per message (`temperature_c` in `C`, `flow_l_min` in `L/min`).
- `topic.airlock.v1`: one event with metric `cycles_per_hour`; `last_state` is encoded in the `status` field.

# RULE MODEL

Automation rules follow the syntax:

```text
IF <sensor_id> <operator> <value> [unit]
THEN set <actuator_id> to ON | OFF
```

**Supported operators:** `<`, `<=`, `=`, `>`, `>=`

**Rule storage schema (PostgreSQL table: `automation_rules`):**

| Column | Type | Description |
| --- | --- | --- |
| `id` | SERIAL PRIMARY KEY | Unique rule identifier |
| `name` | VARCHAR(100) | Human-readable rule name |
| `description` | TEXT | Optional description |
| `sensor_id` | VARCHAR(100) | Sensor to monitor |
| `operator` | VARCHAR(10) | Comparison operator |
| `threshold_value` | DECIMAL(10,2) | Threshold numeric value |
| `threshold_unit` | VARCHAR(20) | Optional unit for clarity |
| `actuator_id` | VARCHAR(100) | Actuator to command |
| `actuator_action` | VARCHAR(20) | `ON` or `OFF` |
| `is_active` | BOOLEAN | Whether the rule is currently enabled |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last modification time |

**Example rules:**

```text
IF greenhouse_temperature > 28 THEN set cooling_fan to ON
IF entrance_humidity < 30 THEN set entrance_humidifier to ON
IF co2_hall > 1000 THEN set hall_ventilation to ON
IF greenhouse_temperature < 18 THEN set habitat_heater to ON
```

Rules are evaluated dynamically on every incoming normalized event. If a rule's `sensor_id` matches the event's `sensor_id` and the condition evaluates to true, the actuator command is dispatched immediately to the actuator control service.
