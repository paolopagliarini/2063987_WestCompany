# REVIEW NOTES
In this document are written some notes on every single service and how they works.

## Automation Engine:
### Description:
The automation engine reads the rules from the database through the load_rules() function.
Rules are loaded directly in the cache to achieve the max response speed possible and to not overload the database.

Once the rules are loaded, when an even is dispatched by the broker the condition of each single rule are verified. If a rule triggers the Automation Engine publishes a message to the "mars_events" exchange.

Rules are updated every 30s by an internal loop.

Access to cache is regulated with a Lock ensuring thread safety.

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

## Data History Service:
### Description:
It receives data from the broker containing historical data to insert in the database from sensors.

### Functioning:
Data is delivered by the broker and are put in a buffer.
Once the buffer is full then all data contained in it is flushed to the db.
It is possible to force the flush to the buffer.

### Endpoints: 
#### /health: 
To request an healtcheck.

#### /history:
Returns the history of sensor values.
It is possible to apply filters.

#### /history/{sensor_id}:
Retrieves the historical data of the given sensor.
It is possible to apply filters.

#### /history/{sensor_id}/aggregate:
Get aggregated readings for the given sensor grouped in a given time interval.

#### /sensors:
List all sensors that have historical data stored ordered in LIFO order.

## Notification Service:
### Description:
It receives events from the broker and forwards them to clients connected via SSE.

### Functioning:
When the broker notifies it, the message is processed, parsing the event into a custom Notification, and then broadcasted to all connected clients.
Notification are stored in a buffer containing the last 100 notifications.

### Endpoints: 
#### /health: 
To request an healtcheck.

#### /notifications:
Returns the last requested number of notifications. May filter by severity.

#### /notifications/stream:
For a client it is possible to subscribe to this endpoint to receive notifications in real-time.
Sends also the last 10 notifications on subscription.

#### /notifications/stats:
Returns statistics about notifications.


