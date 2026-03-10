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

# CONTAINERS:

## CONTAINER_NAME: database

### DESCRIPTION: 
The container that provides the PostgreSQL database for the system.

### USER STORIES:
9. As an operator, I want to create an automation rule (IF sensor_name operator value THEN set actuator_name to ON/OFF), so that the system reacts automatically to environmental conditions.
10. As an operator, I want to view all existing automation rules in a list, so that I can understand what automations are currently configured.
11. As an operator, I want to edit an existing automation rule (change threshold, operator, or actuator action), so that I can adjust automations without deleting and recreating them.
12. As an operator, I want to delete an automation rule, so that I can remove outdated or incorrect automations.
13. As an operator, I want to enable or disable a rule without deleting it, so that I can temporarily suspend an automation and re-enable it later.

### PORTS:
- 5433:5432

### DESCRIPTION:
PostgreSQL 16 relational database initialised via init.sql on first startup. Stores automation rules, sensor historical readings, and actuator command history. Data is persisted through a named Docker volume (postgres_data).

### PERSISTENCE EVALUATION
The data stored in the container are the automation rules, sensor historical data, and actuator command execution history, which are persisted in a PostgreSQL database through a volume (`postgres_data`) so they survive service restarts.

### EXTERNAL SERVICES CONNECTIONS
The database is connected to the actuator-control-service, the data-history-service, the rule-manager-service and the automation-engine.

### MICROSERVICES:

#### MICROSERVICE: database
- TYPE: database
- DESCRIPTION: The container that provides the PostgreSQL database for the system.
- PORTS: 5433:5432
- TECHNOLOGICAL SPECIFICATION:
PostgreSQL is a relational database management system that is used to store and manage data.
- SERVICE ARCHITECTURE: 
SQL Database used to store data, with persistent volumes mounted.

## CONTAINER_NAME: messagging

### DESCRIPTION: 
The container that provides the RabbitMQ message broker for the system.

### USER STORIES:
2. As an operator, I want to see the real-time telemetry data from streaming topics (solar array, radiation, life support, thermal loop, power bus, airlock), so that I can monitor all critical subsystems.
3. As an operator, I want the dashboard to update automatically without refreshing the page, so that I always see the current state of the habitat.
14. As an operator, I want the actuator state to change automatically when a rule condition is triggered by an incoming sensor event, so that the habitat is protected without manual intervention.
16. As an operator, I want to receive a real-time visual alert on the dashboard when a rule is triggered, so that I am immediately aware of critical environmental changes without having to watch every sensor.

### PORTS:
- 5672:5672 (AMQP)
- 15672:15672 (Management UI)

### DESCRIPTION:
RabbitMQ 3 message broker configured with a topic exchange (`mars_events`). Routes normalised sensor events to downstream consumers and actuator commands to the actuator control service. Management UI available on port 15672.

### PERSISTENCE EVALUATION
The configurations and durable queues of RabbitMQ are persisted using the `rabbitmq_data` volume to protect queued events from data loss.

### EXTERNAL SERVICES CONNECTIONS
Connected to all event-driven services: automation-engine, actuator-control-service, notification-service, data-history-service, ingestion.

### MICROSERVICES:

#### MICROSERVICE: messagging
- TYPE: message broker
- DESCRIPTION: RabbitMQ message broker used to route normalized sensor events and actuator commands across the system.
- PORTS: 5672:5672, 15672:15672
- TECHNOLOGICAL SPECIFICATION:
RabbitMQ running the Advanced Message Queuing Protocol (AMQP).
- SERVICE ARCHITECTURE: 
Pub/Sub Message Broker using topic exchanges (`mars_events`).

## CONTAINER_NAME: frontend

### DESCRIPTION: 
The container that provides the frontend for the system.

### USER STORIES:

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
15. As an operator, I want to see when each actuator was last changed and whether the change was triggered manually or by a rule, so that I can audit the system's activity.
16. As an operator, I want to receive a real-time visual alert on the dashboard when a rule is triggered, so that I am immediately aware of critical environmental changes without having to watch every sensor.
17. As an operator, I want to see a log of the most recent rule-trigger events (which rule fired, when, and what sensor value caused it), so that I can audit the system's automated behavior.
18. As an operator, I want to filter the sensor view by category (environmental, power, chemical, physical), so that I can quickly focus on a specific subsystem without scrolling through all sensors.
19. As an operator, I want to see all individual measurements from multi-metric sensors displayed together (e.g. PM1, PM2.5, PM10 from air_quality_pm25), so that I have complete information from each device in one place.
20. As an operator, I want to see the connectivity status of each data source (online / offline / degraded), so that I can detect if a sensor or telemetry stream has stopped sending data.

### PORTS:
- 5173:80

### DESCRIPTION:
React 18 single-page application served via Vite dev server (development) or Nginx (production). Communicates exclusively with backend microservices via REST polling (5 s interval) and a persistent SSE connection for real-time notifications.

### PERSISTENCE EVALUATION
No data is persisted by this container. It acts completely statelessly as a user interface.

### EXTERNAL SERVICES CONNECTIONS
Ingestion, automation-engine, actuator-control-service, notification-service, data-history-service, rule-manager-service.

### MICROSERVICES:

#### MICROSERVICE: frontend
- TYPE: frontend
- DESCRIPTION: React-based web dashboard.
- PORTS: 5173:80
- TECHNOLOGICAL SPECIFICATION:
React, TypeScript, styled with Tailwind CSS, utilizing Vite for building.
- SERVICE ARCHITECTURE: 
Single Page Application (SPA).

- PAGES:

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| Sensors | Sensor Dashboard | data-history-service | 1, 6, 18, 19, 20 |
	| Telemetry | Telemetry Page | data-history-service | 2, 3 |
	| Actuators | Actuators Control | actuator-control-service | 4, 5, 15 |
	| Rule Builder | Create/Edit Rules | rule-manager-service | 9, 11 |
	| Rules | Rule List | rule-manager-service | 10, 12, 13 |
	| Status | System Status | notification-service, automation-engine | 7, 16, 17 |

## CONTAINER_NAME: actuator-control-service

### DESCRIPTION: 
The container that provides the actuator control service for the system.

### USER STORIES:
4. As an operator, I want to see the current ON/OFF state of each actuator...
5. As an operator, I want to manually toggle an actuator ON or OFF from the dashboard...
14. As an operator, I want the actuator state to change automatically when a rule condition is triggered...
15. As an operator, I want to see when each actuator was last changed and whether the change was triggered manually or by a rule...

### PORTS:
- 8005:8005

### DESCRIPTION:
Python/FastAPI service that subscribes to RabbitMQ actuator commands, calls the IoT simulator REST API to execute them, and logs every command to PostgreSQL. Also exposes a REST API for manual actuator control and state inspection by the frontend.

### PERSISTENCE EVALUATION
The service itself is stateless and maintains an in-memory cache, but logs all commands directly to the PostgreSQL database for persistent history.

### EXTERNAL SERVICES CONNECTIONS
PostgreSQL database, RabbitMQ message broker, IoT Simulator API.

### MICROSERVICES:

#### MICROSERVICE: actuator-control-service
- TYPE: backend
- DESCRIPTION: Subscribes to actuator commands from RabbitMQ (published by the automation engine), calls the IoT simulator actuator API, and logs all commands to PostgreSQL. Exposes a REST API for manual actuator control and status inspection.
- PORTS: 8005:8005
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, aio_pika, asyncpg, httpx.
- SERVICE ARCHITECTURE: 
Event Consumer and REST API.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /actuators | Cached actuator states | 4 |
	| GET | /actuators/{actuator_id} | State of specific actuator | 4 |
	| POST | /actuators/{actuator_id} | Manually control actuator | 5 |
	| GET | /actuators/{actuator_id}/history | Command history | 15 |

- DB STRUCTURE:

	**_actuator_commands_** :	| **_id_** | actuator_id, previous_state, new_state, source, reason, rule_id, executed_at

## CONTAINER_NAME: automation-engine

### DESCRIPTION: 
The container that provides the automation engine for the system.

### USER STORIES:
14. As an operator, I want the actuator state to change automatically when a rule condition is triggered by an incoming sensor event, so that the habitat is protected without manual intervention.

### PORTS:
- 8002:8002

### DESCRIPTION:
Python/FastAPI service that consumes normalised sensor events from RabbitMQ, evaluates all active automation rules loaded from PostgreSQL, and publishes actuator commands when a rule condition is met. Rules are cached in memory and reloaded every 30 seconds or on demand.

### PERSISTENCE EVALUATION
Stateless component. It caches rules in memory but loads them from the PostgreSQL database on startup and at interval reloads.

### EXTERNAL SERVICES CONNECTIONS
PostgreSQL database, RabbitMQ message broker.

### MICROSERVICES:

#### MICROSERVICE: automation-engine
- TYPE: backend
- DESCRIPTION: Subscribes to normalized sensor events from RabbitMQ, evaluates automation rules loaded from PostgreSQL, and publishes actuator commands when conditions are met.
- PORTS: 8002:8002
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, aio_pika, asyncpg.
- SERVICE ARCHITECTURE: 
Event Consumer and Publisher via RabbitMQ.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /rules/active | Return active rules cached | 10 |
	| POST | /rules/reload | Force reload rules from DB | - |

## CONTAINER_NAME: data-history-service

### DESCRIPTION: 
The container that provides the data history service for the system.

### USER STORIES:
8. As an operator, I want to see a live time chart of a sensor's values while the page is open, so that I can observe trends over time.

### PORTS:
- 8006:8006

### DESCRIPTION:
Python/FastAPI service that subscribes to normalised sensor events from RabbitMQ and persists them to PostgreSQL. Exposes a REST API for historical queries (filtering, pagination, aggregation) and a high-frequency polling endpoint backed by an in-memory cache for the frontend dashboard.

### PERSISTENCE EVALUATION
Acts as the writer to persist data: it stores normalized sensor events into the PostgreSQL database.

### EXTERNAL SERVICES CONNECTIONS
PostgreSQL database, RabbitMQ message broker.

### MICROSERVICES:

#### MICROSERVICE: data-history-service
- TYPE: backend
- DESCRIPTION: Subscribes to normalized sensor events from RabbitMQ and persists them to the PostgreSQL database. Exposes a REST API for querying historical readings with filtering, pagination, and aggregation, as well as an aggressive polling endpoint via an in-memory cache for the frontend.
- PORTS: 8006:8006
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, aio_pika, asyncpg.
- SERVICE ARCHITECTURE: 
Event Consumer and API Server.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /history | Query historical readings | 8 |
	| GET | /history/{sensor_id} | History for specific sensor | 8 |
	| GET | /history/{sensor_id}/aggregate | Aggregated readings | 8 |
	| GET | /sensors | List sensors with history | 8 |
	| GET | /sensors/latest | Aggressive polling endpoint for frontend | 1, 19, 20 |

- DB STRUCTURE:

	**_sensor_readings_** :	| **_id_** | sensor_id, value, unit, source, recorded_at, created_at

## CONTAINER_NAME: ingestion

### DESCRIPTION: 
The container that provides the ingestion service for the system.

### USER STORIES:
1. As an operator, I want to see the real-time value of all REST sensors on the dashboard, so that I can monitor habitat conditions at a glance.
2. As an operator, I want to see the real-time telemetry data from streaming topics (solar array, radiation, life support, thermal loop, power bus, airlock), so that I can monitor all critical subsystems.
19. As an operator, I want to see all individual measurements from multi-metric sensors displayed together (e.g. PM1, PM2.5, PM10 from air_quality_pm25), so that I have complete information from each device in one place.
20. As an operator, I want to see the connectivity status of each data source (online / offline / degraded), so that I can detect if a sensor or telemetry stream has stopped sending data.

### PORTS:
- 8001:8001

### DESCRIPTION:
Python/FastAPI service that polls REST sensors every 10 seconds and subscribes to 7 SSE telemetry topics. Normalises all incoming payloads into the unified 9-field event schema and publishes them to the RabbitMQ topic exchange. Maintains an in-memory cache of the latest reading per sensor.

### PERSISTENCE EVALUATION
Fully stateless, relies only on temporary in-memory caching to serve the latest states locally. frontend no longer polls here.

### EXTERNAL SERVICES CONNECTIONS
RabbitMQ message broker, IoT Simulator API & SSE Streams.

### MICROSERVICES:

#### MICROSERVICE: ingestion
- TYPE: backend
- DESCRIPTION: Polls REST sensors, subscribes to SSE telemetry streams, normalizes all payloads into the unified internal event schema, and publishes them to RabbitMQ.
- PORTS: 8001:8001
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, aio_pika, httpx.
- SERVICE ARCHITECTURE: 
REST Poller, SSE Subscriber, and Event Publisher.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /sensors/latest | Return all latest cached sensor readings (internal use) | - |
	| GET | /sensors/latest/{sensor_id} | Return latest reading for a sensor (internal use) | - |

## CONTAINER_NAME: notification-service

### DESCRIPTION: 
The container that provides the notification service for the system.

### USER STORIES:
16. As an operator, I want to receive a real-time visual alert on the dashboard when a rule is triggered, so that I am immediately aware of critical environmental changes without having to watch every sensor.
17. As an operator, I want to see a log of the most recent rule-trigger events (which rule fired, when, and what sensor value caused it), so that I can audit the system's automated behavior.

### PORTS:
- 8004:8004

### DESCRIPTION:
Python/FastAPI service that consumes sensor events from RabbitMQ, generates notifications for warning-level readings, and pushes them to connected frontend clients via SSE. Stores the last 100 notifications in memory for new client connections.

### PERSISTENCE EVALUATION
Caches the last 100 notifications in-memory only. No long-term persistence implemented directly here.

### EXTERNAL SERVICES CONNECTIONS
RabbitMQ message broker.

### MICROSERVICES:

#### MICROSERVICE: notification-service
- TYPE: backend
- DESCRIPTION: Receives events from RabbitMQ and pushes notifications to clients via SSE. Stores recent notifications in-memory for new client connections.
- PORTS: 8004:8004
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, aio_pika.
- SERVICE ARCHITECTURE: 
Event Consumer and Server-Sent Events (SSE) server.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /notifications | Get recent notifications | 17 |
	| GET | /notifications/stream | SSE endpoint for real-time notifications | 16 |
	| GET | /notifications/stats | Get notification statistics | 7 |

## CONTAINER_NAME: rule-manager-service

### DESCRIPTION: 
The container that provides the rule manager service for the system.

### USER STORIES:
9. As an operator, I want to create an automation rule (IF sensor_name operator value THEN set actuator_name to ON/OFF), so that the system reacts automatically to environmental conditions.
10. As an operator, I want to view all existing automation rules in a list, so that I can understand what automations are currently configured.
11. As an operator, I want to edit an existing automation rule (change threshold, operator, or actuator action), so that I can adjust automations without deleting and recreating them.
12. As an operator, I want to delete an automation rule, so that I can remove outdated or incorrect automations.
13. As an operator, I want to enable or disable a rule without deleting it, so that I can temporarily suspend an automation and re-enable it later.

### PORTS: 
- 8003:8003

### PERSISTENCE EVALUATION
Does not persist data locally. Defers state mutation entirely to the PostgreSQL database.

### EXTERNAL SERVICES CONNECTIONS
PostgreSQL database.

### MICROSERVICES:

#### MICROSERVICE: rule-manager-service
- TYPE: backend
- DESCRIPTION: CRUD API for automation rules stored in PostgreSQL. Provides endpoints to create, read, update, delete, and toggle rules.
- PORTS: 8003:8003
- TECHNOLOGICAL SPECIFICATION:
Python, FastAPI, SQLAlchemy ORM, asyncpg.
- SERVICE ARCHITECTURE: 
REST API layer.

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| GET | /health | Health check | 7 |
	| GET | /rules | Get all rules | 10 |
	| GET | /rules/{rule_id} | Get specific rule | 10 |
	| POST | /rules | Create a rule | 9 |
	| PUT | /rules/{rule_id} | Update a rule | 11 |
	| DELETE | /rules/{rule_id} | Delete a rule | 12 |
	| PATCH | /rules/{rule_id}/toggle | Toggle rule status | 13 |

- DB STRUCTURE:

	**_automation_rules_** :	| **_id_** | name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at