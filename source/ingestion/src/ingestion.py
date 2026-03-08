"""
Ingestion Service - Mars Habitat Automation Platform

Polls REST sensors, subscribes to SSE telemetry streams, normalizes all payloads
into the unified internal event schema, and publishes them to RabbitMQ.
"""

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aio_pika
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SIMULATOR_URL = os.getenv("SIMULATOR_URL", "http://localhost:8080")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@messagging:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "mars_events")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# In-memory cache: key = "{sensor_id}_{metric}" -> latest normalized event
sensor_cache: dict[str, dict] = {}

# RabbitMQ exchange reference (set during startup)
rmq_exchange: aio_pika.abc.AbstractExchange | None = None
rmq_connection: aio_pika.abc.AbstractConnection | None = None

# REST sensor -> schema mapping
REST_SCHEMA_MAP = {
    "greenhouse_temperature": "rest.scalar.v1",
    "entrance_humidity": "rest.scalar.v1",
    "co2_hall": "rest.scalar.v1",
    "corridor_pressure": "rest.scalar.v1",
    "hydroponic_ph": "rest.chemistry.v1",
    "air_quality_voc": "rest.chemistry.v1",
    "air_quality_pm25": "rest.particulate.v1",
    "water_tank_level": "rest.level.v1",
}

# Telemetry topic -> schema mapping (full topic names from /api/telemetry/topics)
TOPIC_SCHEMA_MAP = {
    "mars/telemetry/solar_array": "topic.power.v1",
    "mars/telemetry/power_bus": "topic.power.v1",
    "mars/telemetry/power_consumption": "topic.power.v1",
    "mars/telemetry/radiation": "topic.environment.v1",
    "mars/telemetry/life_support": "topic.environment.v1",
    "mars/telemetry/thermal_loop": "topic.thermal_loop.v1",
    "mars/telemetry/airlock": "topic.airlock.v1",
}

TELEMETRY_TOPICS = list(TOPIC_SCHEMA_MAP.keys())


# --- Normalizers ---

def normalize_scalar(data: dict) -> list[dict]:
    """rest.scalar.v1: single event, direct mapping."""
    return [_make_event(
        sensor_id=data["sensor_id"],
        timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        metric=data.get("metric", data.get("sensor_id", "unknown")),
        value=data["value"],
        unit=data.get("unit", ""),
        source="rest",
        status=data.get("status", "ok"),
        raw_schema="rest.scalar.v1",
    )]


def normalize_chemistry(data: dict) -> list[dict]:
    """rest.chemistry.v1: one event per measurement in the measurements array."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data["sensor_id"]
    status = data.get("status", "ok")

    for m in data.get("measurements", []):
        events.append(_make_event(
            sensor_id=sensor_id,
            timestamp=timestamp,
            metric=m.get("metric", m.get("name", "unknown")),
            value=m["value"],
            unit=m.get("unit", ""),
            source="rest",
            status=status,
            raw_schema="rest.chemistry.v1",
        ))
    return events


def normalize_particulate(data: dict) -> list[dict]:
    """rest.particulate.v1: three events for pm1, pm2.5, pm10."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data["sensor_id"]
    status = data.get("status", "ok")
    readings = data.get("readings", data)

    pm_fields = [
        ("pm1_ug_m3", "pm1", "µg/m³"),
        ("pm25_ug_m3", "pm2.5", "µg/m³"),
        ("pm10_ug_m3", "pm10", "µg/m³"),
    ]
    for field, metric, unit in pm_fields:
        value = readings.get(field)
        if value is not None:
            events.append(_make_event(
                sensor_id=sensor_id,
                timestamp=timestamp,
                metric=metric,
                value=value,
                unit=unit,
                source="rest",
                status=status,
                raw_schema="rest.particulate.v1",
            ))
    return events


def normalize_level(data: dict) -> list[dict]:
    """rest.level.v1: two events for level_pct and level_liters."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data["sensor_id"]
    status = data.get("status", "ok")
    readings = data.get("readings", data)

    level_fields = [
        ("level_pct", "level_pct", "%"),
        ("level_liters", "level_liters", "L"),
    ]
    for field, metric, unit in level_fields:
        value = readings.get(field)
        if value is not None:
            events.append(_make_event(
                sensor_id=sensor_id,
                timestamp=timestamp,
                metric=metric,
                value=value,
                unit=unit,
                source="rest",
                status=status,
                raw_schema="rest.level.v1",
            ))
    return events


def normalize_power(data: dict) -> list[dict]:
    """topic.power.v1: one event per power metric."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data.get("sensor_id", data.get("topic", "unknown"))
    status = data.get("status", "ok")

    power_fields = [
        ("power_kw", "power_kw", "kW"),
        ("voltage_v", "voltage_v", "V"),
        ("current_a", "current_a", "A"),
        ("cumulative_kwh", "cumulative_kwh", "kWh"),
    ]
    readings = data.get("readings", data)
    for field, metric, unit in power_fields:
        value = readings.get(field)
        if value is not None:
            events.append(_make_event(
                sensor_id=sensor_id,
                timestamp=timestamp,
                metric=metric,
                value=value,
                unit=unit,
                source="stream",
                status=status,
                raw_schema="topic.power.v1",
            ))
    return events


def normalize_environment(data: dict) -> list[dict]:
    """topic.environment.v1: one event per measurement entry."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data.get("sensor_id", data.get("topic", "unknown"))
    status = data.get("status", "ok")

    for m in data.get("measurements", []):
        events.append(_make_event(
            sensor_id=sensor_id,
            timestamp=timestamp,
            metric=m.get("metric", m.get("name", "unknown")),
            value=m["value"],
            unit=m.get("unit", ""),
            source="stream",
            status=status,
            raw_schema="topic.environment.v1",
        ))
    return events


def normalize_thermal_loop(data: dict) -> list[dict]:
    """topic.thermal_loop.v1: two events for temperature_c and flow_l_min."""
    events = []
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    sensor_id = data.get("sensor_id", data.get("topic", "thermal_loop"))
    status = data.get("status", "ok")
    readings = data.get("readings", data)

    thermal_fields = [
        ("temperature_c", "temperature_c", "C"),
        ("flow_l_min", "flow_l_min", "L/min"),
    ]
    for field, metric, unit in thermal_fields:
        value = readings.get(field)
        if value is not None:
            events.append(_make_event(
                sensor_id=sensor_id,
                timestamp=timestamp,
                metric=metric,
                value=value,
                unit=unit,
                source="stream",
                status=status,
                raw_schema="topic.thermal_loop.v1",
            ))
    return events


def normalize_airlock(data: dict) -> list[dict]:
    """topic.airlock.v1: one event with cycles_per_hour; last_state in status."""
    readings = data.get("readings", data)
    last_state = readings.get("last_state", data.get("last_state", "ok"))
    status = last_state if last_state in ("ok", "warning") else "ok"

    return [_make_event(
        sensor_id=data.get("sensor_id", data.get("topic", "airlock")),
        timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        metric="cycles_per_hour",
        value=readings.get("cycles_per_hour", 0),
        unit="cycles/h",
        source="stream",
        status=status,
        raw_schema="topic.airlock.v1",
    )]


def _make_event(*, sensor_id, timestamp, metric, value, unit, source, status, raw_schema) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "metric": metric,
        "value": value,
        "unit": unit,
        "source": source,
        "status": status,
        "raw_schema": raw_schema,
    }


# Schema -> normalizer dispatch
NORMALIZER_MAP = {
    "rest.scalar.v1": normalize_scalar,
    "rest.chemistry.v1": normalize_chemistry,
    "rest.particulate.v1": normalize_particulate,
    "rest.level.v1": normalize_level,
    "topic.power.v1": normalize_power,
    "topic.environment.v1": normalize_environment,
    "topic.thermal_loop.v1": normalize_thermal_loop,
    "topic.airlock.v1": normalize_airlock,
}


# --- RabbitMQ publisher ---

async def connect_rabbitmq():
    """Connect to RabbitMQ and declare the exchange."""
    global rmq_exchange, rmq_connection
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
            rmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await rmq_connection.channel()
            rmq_exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            logger.info("Connected to RabbitMQ, exchange declared")
            return
        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}")
            logger.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def publish_event(event: dict):
    """Publish a normalized event to RabbitMQ and update cache."""
    global rmq_exchange

    # Update in-memory cache
    cache_key = f"{event['sensor_id']}_{event['metric']}"
    sensor_cache[cache_key] = event

    if rmq_exchange is None:
        logger.warning("RabbitMQ not connected, skipping publish")
        return

    try:
        routing_key = f"events.sensor.{event['sensor_id']}"
        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await rmq_exchange.publish(message, routing_key=routing_key)
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")


# --- REST poller ---

async def poll_rest_sensors(client: httpx.AsyncClient):
    """Poll all REST sensors from the simulator."""
    while True:
        try:
            # First get the list of available sensors
            resp = await client.get(f"{SIMULATOR_URL}/api/sensors")
            resp.raise_for_status()
            data = resp.json()
            sensor_ids = data.get("sensors", [])

            # Fetch each sensor's data individually
            for sensor_id in sensor_ids:
                try:
                    sensor_resp = await client.get(f"{SIMULATOR_URL}/api/sensors/{sensor_id}")
                    sensor_resp.raise_for_status()
                    sensor_data = sensor_resp.json()

                    schema = REST_SCHEMA_MAP.get(sensor_id)
                    if schema is None:
                        logger.debug(f"Unknown REST sensor: {sensor_id}, skipping")
                        continue

                    normalizer = NORMALIZER_MAP[schema]
                    sensor_data["sensor_id"] = sensor_id
                    events = normalizer(sensor_data)
                    for event in events:
                        await publish_event(event)

                except httpx.HTTPError as e:
                    logger.error(f"Error fetching sensor {sensor_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error for sensor {sensor_id}: {e}")

            logger.info(f"Polled {len(sensor_ids)} REST sensors")

        except httpx.HTTPError as e:
            logger.error(f"REST polling error: {e}")
        except Exception as e:
            logger.error(f"Unexpected polling error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


# --- SSE subscriber ---

async def subscribe_sse_topic(client: httpx.AsyncClient, topic: str):
    """Subscribe to a single SSE telemetry topic with auto-reconnect."""
    schema = TOPIC_SCHEMA_MAP.get(topic)
    if schema is None:
        logger.warning(f"No schema mapping for topic: {topic}")
        return

    normalizer = NORMALIZER_MAP[schema]
    url = f"{SIMULATOR_URL}/api/telemetry/stream/{topic}"

    while True:
        try:
            logger.info(f"Connecting to SSE topic: {topic}")
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                logger.info(f"Connected to SSE topic: {topic}")

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    json_str = line[len("data:"):].strip()
                    if not json_str:
                        continue

                    try:
                        data = json.loads(json_str)
                        data["sensor_id"] = data.get("sensor_id", data.get("topic", topic))
                        events = normalizer(data)
                        for event in events:
                            await publish_event(event)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in SSE ({topic}): {e}")

        except httpx.HTTPError as e:
            logger.error(f"SSE connection error for {topic}: {e}")
        except Exception as e:
            logger.error(f"SSE unexpected error for {topic}: {e}")

        logger.info(f"Reconnecting to SSE topic {topic} in 5 seconds...")
        await asyncio.sleep(5)


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: connect to RabbitMQ, start poller and SSE tasks."""
    await connect_rabbitmq()

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        # Start REST poller
        poller_task = asyncio.create_task(poll_rest_sensors(client))

        # Start one SSE subscriber per topic
        sse_tasks = []
        for topic in TELEMETRY_TOPICS:
            # Each SSE topic gets its own client to avoid stream conflicts
            sse_client = httpx.AsyncClient(timeout=httpx.Timeout(None))
            task = asyncio.create_task(subscribe_sse_topic(sse_client, topic))
            sse_tasks.append((task, sse_client))

        yield

        # Cleanup
        poller_task.cancel()
        for task, sse_client in sse_tasks:
            task.cancel()
            await sse_client.aclose()

        try:
            await poller_task
        except asyncio.CancelledError:
            pass
        for task, _ in sse_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

        if rmq_connection:
            await rmq_connection.close()


app = FastAPI(
    title="Mars Habitat Ingestion Service",
    description="Ingests sensor data from IoT simulator and publishes normalized events",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ingestion",
        "cached_sensors": len(sensor_cache),
        "rabbitmq_connected": rmq_exchange is not None,
    }


@app.get("/sensors/latest")
async def get_all_latest():
    """Return all latest sensor readings from the in-memory cache."""
    return {
        "count": len(sensor_cache),
        "sensors": sensor_cache,
    }


@app.get("/sensors/latest/{sensor_id}")
async def get_sensor_latest(sensor_id: str):
    """Return latest readings for a specific sensor."""
    matching = {k: v for k, v in sensor_cache.items() if v["sensor_id"] == sensor_id}
    if not matching:
        return {"count": 0, "sensors": {}}
    return {
        "count": len(matching),
        "sensors": matching,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
