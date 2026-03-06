# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mars Habitat Automation Platform - a distributed IoT automation system for managing sensors and actuators in a simulated Mars habitat. This is the Laboratory of Advanced Programming Hackathon Exam project (March 2026).

The system implements:
- REST sensor polling and telemetry stream ingestion (SSE/WebSocket)
- Event normalization to a unified internal schema
- Message broker for event-driven architecture
- Automation engine with IF-THEN rules
- Real-time monitoring dashboard

## Architecture

```
Mars IoT Simulator → Ingestion API → Message Broker → Processing/Automation + State Service
                                                              ↓
                                           Actuator API + Frontend API
```

**Microservices:**
- `database/` - Data persistence layer
- `messagging/` - Message broker (Kafka/RabbitMQ/ActiveMQ)
- `backend/` - Python 3.12 backend using uvicorn (entrypoint: `server_backend.py`)
- `frontend/` - Web dashboard (React/Vue/Angular)

## Running the System

```bash
# Start IoT simulator (port 8080)
docker load -i mars-iot-simulator-oci.tar
docker run --rm -p 8080:8080 mars-iot-simulator:multiarch_v1

# Start all services
docker compose up
```

## Key Endpoints (IoT Simulator)

- `/api/sensors` - REST sensors (polling required)
- `/api/telemetry/topics` - Telemetry stream topics
- `/api/actuators` - Actuator control API
- `/docs` - API documentation
- `/openapi.json` - OpenAPI spec

## Event Schema

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

## Automation Rule Syntax

```
IF <sensor_name> <operator> <value> [unit]
THEN set <actuator_name> to ON | OFF
```

Operators: `<`, `<=`, `=`, `>`, `>=`

Example: `IF greenhouse_temperature > 28 °C THEN set cooling_fan to ON`

## Project Status

This project is in early development. Docker configurations contain placeholders that need to be completed with actual image names, ports, environment variables, and volumes.

## Development Notes

- Backend uses `PYTHONPATH=/backend` for module resolution
- Backend Dockerfile installs curl for health checks
- Frontend Dockerfile needs completion (currently empty CMD)
- requirements.txt needs dependencies added