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

## Notification Service:
### Events have status:
I do not why but events received by the notification service are forwarded with a 'status' attribute.
Ok it acts like a filter and forwards if a notification is 'relevant'. 
It classifies using a reduntant operation, it assigns severity as it is the status.  eg. status == warning --> severity == warning.
This is the part of code that decentralizes and reduces the importance of the broker, it is possible to register to this service to receive events through SSE.