# Mars Habitat Automation Platform

## Overview

This project implements a **distributed automation platform for a Mars habitat**. The system ingests heterogeneous sensor data coming from a simulated IoT environment, normalizes it into a unified internal representation, evaluates automation rules, and exposes a **real-time monitoring dashboard** for habitat control.

The goal of the platform is to provide a resilient and extensible automation layer capable of coordinating sensors and actuators in a hostile environment where reliability and real-time feedback are critical.

The application has been developed as part of the **Laboratory of Advanced Programming – Hackathon Exam (March 2026)**.

The scenario assumes that the automation stack of a Mars habitat has partially failed, leaving several devices operating with incompatible communication protocols. The system must therefore rebuild a unified platform capable of:

* Collecting data from multiple device types
* Converting heterogeneous payloads into a common event schema
* Evaluating automation rules
* Controlling actuators when conditions are satisfied
* Providing a real-time dashboard for monitoring and management

---

# System Goals

The platform satisfies the following main objectives:

1. **Device Data Ingestion**

   * Poll REST-based sensors
   * Subscribe to streaming telemetry sources

2. **Event Normalization**

   * Convert heterogeneous payload formats into a **standardized internal event schema**

3. **Event-Driven Architecture**

   * Use a **message broker** to decouple ingestion, processing, and presentation layers

4. **Automation Engine**

   * Evaluate rules defined as simple **IF–THEN conditions**
   * Trigger actuator actions when rule conditions are satisfied

5. **Real-Time Monitoring**

   * Provide a dashboard displaying live sensor values and actuator states

6. **Rule Persistence**

   * Persist automation rules in a database so they survive service restarts

---

# System Architecture

The system follows a **microservice-based architecture** where each component has a specific responsibility.

```
                  +----------------------+
                  |  Mars IoT Simulator  |
                  +----------+-----------+
                             |
                REST Polling |  Telemetry Stream
                             |
                    +--------v--------+
                    |  Ingestion API  |
                    |  (Device Adapters)
                    +--------+--------+
                             |
                             | Normalized Events
                             v
                     +---------------+
                     | Message Broker|
                     +-------+-------+
                             |
                 +-----------+------------+
                 |                        |
        +--------v--------+       +-------v-------+
        | Processing /    |       | State Service |
        | Automation Engine|      | Sensor Cache  |
        +--------+--------+       +-------+-------+
                 |                        |
                 | Actuator Commands     |
                 v                        v
         +---------------+        +--------------+
         | Actuator API  |        | Frontend API |
         +-------+-------+        +------+-------+
                 |                       |
                 v                       v
           Habitat Devices         Web Dashboard
```

---

# IoT Simulator

The project integrates with a **Mars IoT simulator** that provides a heterogeneous device environment.

The simulator exposes:

* **REST Sensors**
* **Telemetry Streams**
* **Actuator APIs**

The simulator runs inside a Docker container and exposes services on port **8080**.

Example commands:

```bash
docker load -i mars-iot-simulator-oci.tar
docker run --rm -p 8080:8080 mars-iot-simulator:multiarch_v1
```

Available endpoints include:

```
/api/sensors
/api/telemetry/topics
/api/actuators
/docs
/openapi.json
```

---

# Sensors

The platform ingests data from two categories of devices.

## REST Sensors (Polling)

These sensors must be periodically queried.

Examples:

| Sensor                 | Type              |
| ---------------------- | ----------------- |
| greenhouse_temperature | temperature       |
| entrance_humidity      | humidity          |
| co2_hall               | gas concentration |
| hydroponic_ph          | chemistry         |
| water_tank_level       | liquid level      |
| corridor_pressure      | pressure          |
| air_quality_pm25       | particulate       |
| air_quality_voc        | chemistry         |

Polling services retrieve the sensor values and convert them into normalized events.

---

## Telemetry Streams (Push)

Some devices publish telemetry periodically through streaming channels.

Examples of topics:

| Topic                            | Data Type      |
| -------------------------------- | -------------- |
| mars/telemetry/solar_array       | power          |
| mars/telemetry/radiation         | environmental  |
| mars/telemetry/life_support      | environmental  |
| mars/telemetry/thermal_loop      | thermal        |
| mars/telemetry/power_bus         | power          |
| mars/telemetry/power_consumption | power          |
| mars/telemetry/airlock           | airlock status |

These streams are consumed via:

* **Server Sent Events (SSE)**
* **WebSockets**

---

# Actuators

The platform can control several habitat devices through REST APIs.

Examples:

| Actuator            | Function               |
| ------------------- | ---------------------- |
| cooling_fan         | temperature regulation |
| entrance_humidifier | humidity control       |
| hall_ventilation    | air circulation        |
| habitat_heater      | thermal regulation     |

Example command:

```bash
POST /api/actuators/cooling_fan
{
  "state": "ON"
}
```

---

# Event Normalization

Because sensors produce heterogeneous payloads, the system converts them into a **unified internal event schema**.

Example normalized event:

```json
{
  "sensor_id": "greenhouse_temperature",
  "timestamp": "2036-03-05T12:45:00Z",
  "value": 27.4,
  "unit": "C",
  "source": "rest",
  "type": "temperature"
}
```

This normalized format allows services to process events without knowing the original device protocol.

---

# Automation Engine

The automation engine evaluates **event-driven rules**.

Rules follow the syntax:

```
IF <sensor_name> <operator> <value> [unit]
THEN set <actuator_name> to ON | OFF
```

Supported operators:

```
<
<=
=
>
>=
```

Example rule:

```
IF greenhouse_temperature > 28 °C
THEN set cooling_fan to ON
```

When an event arrives:

1. The rule engine evaluates all relevant rules
2. If a condition is satisfied
3. The actuator API is invoked automatically

Rules are persisted in a database so that they remain available after system restarts.

---

# State Management

The system maintains the **latest state of each sensor** in memory.

This allows:

* fast dashboard updates
* simplified rule evaluation
* real-time monitoring

Historical persistence is **not required**.

---

# Frontend Dashboard

The frontend provides a **real-time monitoring interface**.

Features include:

### Sensor Monitoring

* Live sensor values
* Dynamic updates via WebSocket or SSE

### Visualization

Possible widgets:

* live value display
* charts
* environmental status panels

### Actuator Control

* display actuator states
* allow manual toggling of actuators

### Rule Management

Users can:

* create automation rules
* modify existing rules
* delete rules

---

# Technology Stack

The project uses a modern cloud-native architecture.

Example stack:

### Backend

* Python / Node.js / Java
* REST APIs

### Messaging

* Kafka / ActiveMQ / RabbitMQ

### Database

* PostgreSQL / MongoDB / SQLite

### Frontend

* React / Vue / Angular

### Infrastructure

* Docker
* Docker Compose

---

# Running the System

The entire platform can be started using Docker Compose.

```bash
docker compose up
```

This command launches:

* IoT simulator
* backend services
* message broker
* database
* frontend dashboard

No additional configuration is required after startup.

---

# Repository Structure

```
.
├── input.md
├── Student_doc.md
├── source/
│   ├── services/
│   ├── frontend/
│   ├── ingestion/
│   ├── automation-engine/
│   └── docker-compose.yml
└── booklets/
    ├── slides/
    ├── diagrams/
    └── mockups/
```

---

# Key Design Principles

The platform has been designed with the following principles:

### Event-Driven Architecture

All services communicate through events using a message broker.

### Service Decoupling

Each service performs a single responsibility:

* ingestion
* processing
* rule evaluation
* presentation

### Scalability

The architecture allows independent scaling of services.

### Reliability

Message queues guarantee reliable event delivery.

---

# Future Improvements

Possible extensions include:

* historical data storage
* advanced rule conditions
* alerting and notification systems
* predictive analytics
* multi-user support and authentication

---

# Conclusion

This project demonstrates how a distributed event-driven architecture can be used to manage heterogeneous IoT environments. By combining device ingestion, event normalization, automation rules, and real-time visualization, the system provides a robust platform for monitoring and controlling critical infrastructure such as a Mars habitat.
