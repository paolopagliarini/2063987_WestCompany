# Mars Habitat Automation Platform - Comprehensive Project Summary

## 1. Introduction
The **Mars Habitat Automation Platform** is a distributed, event-driven system built to automate a Mars habitat's critical infrastructure. Due to a partial failure of the previous automation stack, this platform rebuilds a resilient layer that integrates multiple hardware endpoints (sensors and actuators) working with varying and initially incompatible communication protocols.

All incoming data streams are ingested and translated into a generic system-wide protocol. This unified data stream then rules the automatic activation of actuators and provides human operators with real-time insight through a frontend dashboard.

---

## 2. Microservices Architecture and Responsibilities

The system is compartmentalized into several individual microservices communicating asynchronously via **RabbitMQ**.

### 🏗 Core Services:
*   **IoT Simulator (External)**: An application mimicking the physical Mars environment. It provides REST-polled sensors (like `greenhouse_temperature`) and WebSocket-based telemetry streams (like `mars/telemetry/solar_array`).
*   **Ingestion Service**: The main entryway. It maps and converts completely different payloads (REST vs Stream) into the exact same structure before dispatching them to RabbitMQ.
*   **RabbitMQ (Message Broker)**: Routes `events.sensor.#` (data readings) to all interested services and `commands.actuator.#` (actions) specifically to the actuator controller.
*   **Automation Engine**: The brain. It listens to the message broker. When an event fires, it compares it against stored user rules (e.g., *Is the new temperature higher than my set threshold?*). If a rule passes, it publishes a command back to RabbitMQ.
*   **Rule Manager Service**: An API enabling operators to Create, Read, Update, or Delete (CRUD) the automation rules. These rules are safely persisted in PostgreSQL.
*   **Actuator Control Service**: The arm. It intercepts commands from RabbitMQ and makes HTTP calls to the simulator to turn devices (like fans, or heaters) ON or OFF.
*   **Data History / State Service**: Stores and recalls the *latest known state* of every sensor. When a user opens the web page, the backend reads from here to instantly paint the real-time UI without waiting for a new reading.
*   **Notification Service**: A WebSocket or SSE engine pushing data straight into the frontend client. Whenever RabbitMQ receives a reading or rule triggers, this service "pushes" it to the browser.
*   **Frontend Dashboard**: A user interface allowing operators to visualize values (React/Vue/Angular), analyze charts, change rules and manually push actuator buttons.

---

## 3. The "Standard Internal Event Schema"

The platform handles highly diverse sensors. For example, a "REST Chemical Sensor" might output an array of strings while the "Telemetry Stream" outputs a single binary integer. 

The **Ingestion Service** solves this by normalizing EVERYTHING into this strict, standard schema:

```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "sensor_id": "hydroponic_ph",
  "timestamp": "2036-03-05T12:45:00Z",
  "metric": "chemistry",
  "value": 6.5,
  "unit": "pH",
  "source": "rest",
  "status": "warning",
  "raw_schema": "rest.chemistry.v1"
}
```
**Why this matters**: Because of this normalization, the *Automation Engine* or the *Frontend* do not need to know *how* to parse a specific chemical sensor format. They simply read `value` and `unit` regardless of the source.

---

## 4. Automation Rules Engine (IF-THEN)

Operators create rules stored in PostgreSQL. 

**Rule syntax:** `IF <sensor_id> <operator> <value> THEN <actuator_id> to <ON/OFF>`

### 🛠 Practical Example: The Heating Process

1.  **Rule Setup**: An operator uses the dashboard to save: `IF greenhouse_temperature < 15.0 THEN set habitat_heater to ON`.
2.  **Ingestion Phase**: The *Ingestion Service* queries the Simulator and receives `14.2 °C` for the greenhouse. It standardizes it to JSON and sends it over RabbitMQ on the `events.sensor.greenhouse_temperature` topic.
3.  **State & UI update**:
    *   The *Notification Service* sees the message and pushes it automatically to the user's browser, turning the UI chart line downwards.
    *   The *State Service* updates the DB caching this new lowest value.
4.  **Rule Evaluation Phase**: The *Automation Engine* pulls the message from RabbitMQ. It queries the PostgreSQL DB for rules bound to `greenhouse_temperature`. It finds the rule and checks: `Is 14.2 < 15.0?`. The statement is **True**.
5.  **Command Phase**: The *Automation Engine* acts by publishing a new payload `{ action: 'ON' }` into RabbitMQ under `commands.actuator.habitat_heater`.
6.  **Actuation Phase**: The *Actuator Control Service* intercepts this command and sends an HTTP POST to the IoT Simulator (`/api/actuators/habitat_heater {"state": "ON"}`). The heater starts up in the simulator.

---

## 5. User Stories Covered (Key Workflows)

This architecture comprehensively serves the mandatory user goals outlined in the input specification:
-   **"Operators need automatic UI updates without refreshing"**: Accomplished by the Notification Service establishing an SSE/WebSocket link with the frontend.
-   **"Operators must be able to view live trends"**: The Frontend draws a time-chart based on pushing data.
-   **"Operators must quickly enable/disable rules or delete them"**: Controlled via Frontend components interfacing directly with the Rule Manager Service.
-   **"Sensor anomalies tracking"**: The `status: "warning"` key inside the Standard Event Schema directly maps to red warning icons on the frontend dashboard.
