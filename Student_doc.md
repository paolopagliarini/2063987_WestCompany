# SYSTEM DESCRIPTION:

The **Mars Habitat Automation Platform** is a distributed event-driven system designed to monitor and control a Mars habitat's critical infrastructure. The platform ingests heterogeneous sensor data from a simulated IoT environment — both REST-polled sensors and streaming telemetry topics — normalizes all payloads into a unified internal event format, evaluates automation rules, and exposes a real-time dashboard for habitat monitoring and control.

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
The container that provides the PostgreSQL DB for the system.

### USER STORIES:
9. As an operator, I want to create an automation rule (IF sensor_name operator value THEN set actuator_name to ON/OFF), so that the system reacts automatically to environmental conditions.
10. As an operator, I want to view all existing automation rules in a list, so that I can understand what automations are currently configured.
11. As an operator, I want to edit an existing automation rule (change threshold, operator, or actuator action), so that I can adjust automations without deleting and recreating them.
12. As an operator, I want to delete an automation rule, so that I can remove outdated or incorrect automations.
13. As an operator, I want to enable or disable a rule without deleting it, so that I can temporarily suspend an automation and re-enable it later.

### PORTS: 
5433:5432

### PERSISTENCE EVALUATION
The data stored in the container are the automation rules, which are persisted in a PostgreSQL database so they survive service restarts.

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: messaging

### DESCRIPTION: 
The container that provides the RabbitMQ message broker for the system.

### USER STORIES:
??

### PORTS: 
15672:15672

### PERSISTENCE EVALUATION
The data stored in the container are the automation rules, which are persisted in a PostgreSQL database so they survive service restarts.

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: frontend

### DESCRIPTION: 
The container that provides the frontend for the system.

### USER STORIES:
??

### PORTS: 
5173:80

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: actuator-control-service

### DESCRIPTION: 
The container that provides the actuator control service for the system.

### USER STORIES:
??

### PORTS: 
8005:8005

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: automation-engine

### DESCRIPTION: 
The container that provides the automation engine for the system.

### USER STORIES:
??

### PORTS: 
8002:8002

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: data-history-service

### DESCRIPTION: 
The container that provides the data history service for the system.

### USER STORIES:
??

### PORTS: 
8006:8006

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: ingestion

### DESCRIPTION: 
The container that provides the ingestion service for the system.

### USER STORIES:
??

### PORTS: 
8001:8001

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: notification-service

### DESCRIPTION: 
The container that provides the notification service for the system.

### USER STORIES:
??

### PORTS: 
8004:8004

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

## CONTAINER_NAME: rule-manager-service

### DESCRIPTION: 
The container that provides the rule manager service for the system.

### USER STORIES:
??

### PORTS: 
8003:8003

### PERSISTENCE EVALUATION
??

### EXTERNAL SERVICES CONNECTIONS
???

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>