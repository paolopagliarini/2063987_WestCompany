"""
Automation Engine - Mars Habitat Automation Platform

Subscribes to normalized sensor events from RabbitMQ, evaluates automation rules
loaded from PostgreSQL, and publishes actuator commands when conditions are met.
"""

import asyncio
import json
import logging
import operator as op
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@messagging:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "mars_events")
ROUTING_KEY = os.getenv("ROUTING_KEY", "events.sensor.#")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))
RULES_RELOAD_INTERVAL = int(os.getenv("RULES_RELOAD_INTERVAL", "30"))

# Operator mapping
OPERATORS = {
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
    ">": op.gt,
    ">=": op.ge,
}

# In-memory rules cache: list of active rule dicts
rules_cache: list[dict] = []
rules_lock = asyncio.Lock()

# Stats
stats = {
    "events_received": 0,
    "rules_evaluated": 0,
    "rules_triggered": 0,
    "commands_published": 0,
}

# Global references
db_engine = None
rmq_connection = None
rmq_exchange = None


async def load_rules():
    """Load active automation rules from the database into memory."""
    global rules_cache
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT id, name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active FROM automation_rules WHERE is_active = TRUE")
            )
            rows = result.fetchall()
            new_rules = []
            for row in rows:
                new_rules.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "sensor_id": row[3],
                    "operator": row[4],
                    "threshold_value": float(row[5]),
                    "threshold_unit": row[6],
                    "actuator_id": row[7],
                    "actuator_action": row[8],
                    "is_active": row[9],
                })
            async with rules_lock:
                rules_cache = new_rules
            logger.info(f"Loaded {len(new_rules)} active rules from database")
    except Exception as e:
        logger.error(f"Failed to load rules: {e}")


async def rules_reload_loop():
    """Periodically reload rules from the database."""
    while True:
        await asyncio.sleep(RULES_RELOAD_INTERVAL)
        await load_rules()


def evaluate_condition(value: float, rule_operator: str, threshold: float) -> bool:
    """Evaluate a rule condition: value <op> threshold."""
    op_func = OPERATORS.get(rule_operator)
    if op_func is None:
        logger.warning(f"Unknown operator: {rule_operator}")
        return False
    return op_func(value, threshold)


async def publish_actuator_command(rule: dict, event: dict):
    """Publish an actuator command to RabbitMQ when a rule triggers."""
    global rmq_exchange

    if rmq_exchange is None:
        logger.warning("RabbitMQ not connected, skipping command publish")
        return

    command = {
        "command_id": event.get("event_id", ""),
        "actuator_id": rule["actuator_id"],
        "action": rule["actuator_action"],
        "source": "automation-engine",
        "rule_id": rule["id"],
        "rule_name": rule["name"],
        "triggered_by": {
            "sensor_id": event.get("sensor_id"),
            "metric": event.get("metric"),
            "value": event.get("value"),
            "unit": event.get("unit"),
            "operator": rule["operator"],
            "threshold": rule["threshold_value"],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        routing_key = f"commands.actuator.{rule['actuator_id']}"
        message = aio_pika.Message(
            body=json.dumps(command).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await rmq_exchange.publish(message, routing_key=routing_key)
        stats["commands_published"] += 1
        logger.info(f"Rule '{rule['name']}' triggered: {event.get('sensor_id')} {event.get('metric')}={event.get('value')} {rule['operator']} {rule['threshold_value']} → {rule['actuator_id']}={rule['actuator_action']}")
    except Exception as e:
        logger.error(f"Failed to publish actuator command: {e}")


async def process_event(message: AbstractIncomingMessage):
    """Process an incoming normalized sensor event against all active rules."""
    try:
        event = json.loads(message.body.decode())
        stats["events_received"] += 1

        event_sensor_id = event.get("sensor_id")
        event_value = event.get("value")

        if event_sensor_id is None or event_value is None:
            await message.ack()
            return

        try:
            event_value = float(event_value)
        except (ValueError, TypeError):
            await message.ack()
            return

        # Evaluate matching rules
        async with rules_lock:
            matching_rules = [r for r in rules_cache if r["sensor_id"] == event_sensor_id]

        for rule in matching_rules:
            stats["rules_evaluated"] += 1
            if evaluate_condition(event_value, rule["operator"], rule["threshold_value"]):
                stats["rules_triggered"] += 1
                await publish_actuator_command(rule, event)

        await message.ack()

    except Exception as e:
        logger.error(f"Error processing event: {e}")
        await message.ack()


async def consume_events():
    """Connect to RabbitMQ and consume normalized sensor events."""
    global rmq_connection, rmq_exchange

    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
            rmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)

            async with rmq_connection:
                channel = await rmq_connection.channel()
                await channel.set_qos(prefetch_count=10)

                # Declare exchange (same as ingestion)
                rmq_exchange = await channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )

                # Declare queue for automation engine
                queue = await channel.declare_queue(
                    "automation_engine_queue",
                    durable=True,
                    arguments={
                        "x-message-ttl": 60000,  # 60s TTL - rules must evaluate promptly
                    }
                )

                # Bind to all sensor events
                await queue.bind(rmq_exchange, routing_key=ROUTING_KEY)
                logger.info(f"Listening for events with routing key: {ROUTING_KEY}")

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        await process_event(message)

        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}")
            logger.info("Retrying connection in 5 seconds...")
            await asyncio.sleep(5)


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global db_engine

    # Create database engine
    db_engine = create_async_engine(DATABASE_URL, echo=False)

    # Load rules initially
    await load_rules()

    # Start background tasks
    consumer_task = asyncio.create_task(consume_events())
    reload_task = asyncio.create_task(rules_reload_loop())

    yield

    # Cleanup
    consumer_task.cancel()
    reload_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    try:
        await reload_task
    except asyncio.CancelledError:
        pass

    await db_engine.dispose()


app = FastAPI(
    title="Mars Habitat Automation Engine",
    description="Evaluates automation rules against sensor events and dispatches actuator commands",
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
        "service": "automation-engine",
        "active_rules": len(rules_cache),
        "rabbitmq_connected": rmq_exchange is not None,
        "stats": stats,
    }


@app.get("/rules/active")
async def get_active_rules():
    """Return currently cached active rules."""
    async with rules_lock:
        return {
            "count": len(rules_cache),
            "rules": rules_cache,
        }


@app.post("/rules/reload")
async def reload_rules():
    """Force reload rules from the database."""
    await load_rules()
    async with rules_lock:
        return {
            "message": "Rules reloaded",
            "count": len(rules_cache),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
