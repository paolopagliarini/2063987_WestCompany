# CODE REVIEW LOG
This document contains the log of the code review process.

## General
### Services are subscribed to the same topic:
Broker usage is not consistent nor useful due to the fact that all services are subscribed to the same topic. 
#### ToDo:
processes should have their own topics.
#### Notes:
See function consume_events.

## Actuator Control Service
### Service directly calls the IoT simulator API:
The service directly calls the Simulator to get the names and status of the actuator.
Specifically in function:
- fetch_actuator_states
#### ToDo:
The service should communicate with the Broker which will then notify the ingestor to communicate with the simulator and the same way back. 
Understand if the call directly to the env is legit.

## Automation Engine:
None

