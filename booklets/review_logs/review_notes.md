# REVIEW NOTES
In this document are written some notes on every single service and how they works.

## Automation Engine:
### Description:
The automation engine reads the rules from the database through the load_rules() function.
Rules are loaded directly in the cache to achieve the max response speed possible and to not overload the database.
Once the rules are loaded, when an even is dispatched by the broker the condition of each single rule are verified. If a rule triggers the Automation Engine publishes a message to the "mars_events" exchange.

Rules are updated every 30s by an internal loop.

### Endpoints:
#### /health:
To request an healtcheck.

#### /rules/active:
Shows all active rules.

#### /rules/reload:
Forcely reloads all the rules.
Practically the engine communicates with the db to retrieve all written rules.

## Actuator Control Service:
### Description: 
The Actuator Control Service subscribes to 'actuator_commands' from the broker, this are broadcasted when an automation rule is triggered. 

On setup the ACS poll from the IoT Env all the available actuators and their status (TODO: check if it is legal).

When a message is streamed to the ACS in order to switch an actuator, it will fetch a call directly to the IoT Env (TODO: check if it is legal).

All actuators executed commands are logged to the database.

### Endpoints:
#### /health: 
To request an healtcheck.

#### /actuators:
Return all the cached actuator informations after refreshing the list from the IoT Env.

#### /actuators/{actuator_id}: 
- GET: Return the cached state of the given actuator.
- POST: To set the state of an actuator manually. 

#### /actuators/{actuator_id}/history:
Returns the command history for a given actuator. 