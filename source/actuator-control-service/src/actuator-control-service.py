"""
Actuator Control Service - Mars Habitat Automation Platform

Subscribes to actuator commands from RabbitMQ (published by the automation engine),
calls the IoT simulator actuator API, and logs all commands to PostgreSQL.
Also exposes a REST API for manual actuator control and status inspection.
"""

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import aio_pika
import httpx
from aio_pika.abc import AbstractIncomingMessage
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SIMULATOR_URL = os.getenv("SIMULATOR_URL", "http://localhost:8080")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@messagging:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "mars_events")
COMMAND_ROUTING_KEY = os.getenv("COMMAND_ROUTING_KEY", "commands.actuator.#")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))

# In-memory cache of latest actuator states
actuator_states: dict[str, dict] = {}

# Stats
stats = {
    "commands_received": 0,
    "commands_executed": 0,
    "commands_failed": 0,
}

# Global references
db_engine = None
http_client: httpx.AsyncClient | None = None


class ManualCommand(BaseModel):
    """Request body for manual actuator control."""
    state: str

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        v_upper = v.upper()
        if v_upper not in ("ON", "OFF"):
            raise ValueError("state must be ON or OFF")
        return v_upper


async def fetch_actuator_states():
    """Fetch current actuator states from the simulator and populate cache."""
    try:
        resp = await http_client.get(f"{SIMULATOR_URL}/api/actuators")
        resp.raise_for_status()
        data = resp.json()
        # Simulator returns {"actuators": {"id": "STATE", ...}}
        actuators_dict = data.get("actuators", {}) if isinstance(data, dict) else {}
        for act_id, state in actuators_dict.items():
            actuator_states[act_id] = {
                "actuator_id": act_id,
                "state": state,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        logger.info(f"Fetched {len(actuators_dict)} actuator states from simulator")
    except Exception as e:
        logger.error(f"Failed to fetch actuator states: {e}")


async def call_actuator_api(actuator_id: str, state: str) -> bool:
    """Call the IoT simulator to change an actuator's state. Returns True on success."""
    try:
        resp = await http_client.post(
            f"{SIMULATOR_URL}/api/actuators/{actuator_id}",
            json={"state": state},
        )
        resp.raise_for_status()
        logger.info(f"Actuator API call successful: {actuator_id} -> {state}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"Actuator API HTTP error for {actuator_id}: {e.response.status_code} {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Actuator API call failed for {actuator_id}: {e}")
        return False


async def log_command(actuator_id: str, previous_state: str | None, new_state: str,
                      source: str, reason: str | None, rule_id: int | None):
    """Log an actuator command to the database."""
    try:
        async with db_engine.connect() as conn:
            await conn.execute(
                text("""
                    INSERT INTO actuator_commands (actuator_id, previous_state, new_state, source, reason, rule_id, executed_at)
                    VALUES (:actuator_id, :previous_state, :new_state, :source, :reason, :rule_id, NOW())
                """),
                {
                    "actuator_id": actuator_id,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "source": source,
                    "reason": reason,
                    "rule_id": rule_id,
                }
            )
            await conn.commit()
    except Exception as e:
        logger.error(f"Failed to log command to DB: {e}")


async def execute_command(actuator_id: str, action: str, source: str,
                          rule_id: int | None = None, rule_name: str | None = None,
                          reason: str | None = None):
    """Execute an actuator command: call the API, update cache, log to DB."""
    previous_state = actuator_states.get(actuator_id, {}).get("state")

    # Skip if the state is already the requested action
    if previous_state == action:
        logger.info(f"Actuator {actuator_id} is already in state '{action}'. Skipping command.")
        return True

    success = await call_actuator_api(actuator_id, action)

    if success:
        stats["commands_executed"] += 1
        actuator_states[actuator_id] = {
            "actuator_id": actuator_id,
            "state": action,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if reason is None and rule_name:
            reason = f"Rule '{rule_name}' triggered"
        await log_command(actuator_id, previous_state, action, source, reason, rule_id)
    else:
        stats["commands_failed"] += 1

    return success


async def process_command(message: AbstractIncomingMessage):
    """Process an actuator command message from RabbitMQ."""
    try:
        command = json.loads(message.body.decode())
        stats["commands_received"] += 1

        actuator_id = command.get("actuator_id")
        action = command.get("action")

        if not actuator_id or not action:
            logger.warning(f"Invalid command (missing actuator_id or action): {command}")
            await message.ack()
            return

        rule_id = command.get("rule_id")
        rule_name = command.get("rule_name")
        source = command.get("source", "automation-engine")

        triggered_by = command.get("triggered_by", {})
        reason = None
        if triggered_by:
            reason = (
                f"Rule '{rule_name}': {triggered_by.get('sensor_id')} "
                f"{triggered_by.get('metric')}={triggered_by.get('value')} "
                f"{triggered_by.get('operator')} {triggered_by.get('threshold')}"
            )

        await execute_command(actuator_id, action, source, rule_id, rule_name, reason)
        await message.ack()

    except Exception as e:
        logger.error(f"Error processing command: {e}")
        await message.ack()


async def consume_commands():
    """Connect to RabbitMQ and consume actuator commands."""
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )

                queue = await channel.declare_queue(
                    "actuator_control_queue",
                    durable=True,
                    arguments={"x-message-ttl": 30000},
                )

                await queue.bind(exchange, routing_key=COMMAND_ROUTING_KEY)
                logger.info(f"Listening for commands with routing key: {COMMAND_ROUTING_KEY}")

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        await process_command(message)

        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}")
            logger.info("Retrying connection in 5 seconds...")
            await asyncio.sleep(5)


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global db_engine, http_client

    db_engine = create_async_engine(DATABASE_URL, echo=False)
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

    # Fetch initial actuator states from simulator
    await fetch_actuator_states()

    # Start RabbitMQ consumer
    consumer_task = asyncio.create_task(consume_commands())

    yield

    # Cleanup
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await http_client.aclose()
    await db_engine.dispose()


app = FastAPI(
    title="Mars Habitat Actuator Control Service",
    description="Controls actuators via the IoT simulator and logs commands",
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
        "service": "actuator-control-service",
        "actuators_tracked": len(actuator_states),
        "stats": stats,
    }


@app.get("/actuators")
async def get_actuators():
    """Return cached actuator states. Also refreshes from simulator."""
    await fetch_actuator_states()
    return {
        "count": len(actuator_states),
        "actuators": actuator_states,
    }


@app.get("/actuators/{actuator_id}")
async def get_actuator(actuator_id: str):
    """Return the cached state of a specific actuator."""
    state = actuator_states.get(actuator_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Actuator '{actuator_id}' not found")
    return state


@app.post("/actuators/{actuator_id}")
async def control_actuator(actuator_id: str, cmd: ManualCommand):
    """Manually control an actuator."""
    success = await execute_command(
        actuator_id=actuator_id,
        action=cmd.state,
        source="manual",
        reason="Manual control via API",
    )
    if not success:
        raise HTTPException(status_code=502, detail="Failed to control actuator via simulator")

    return {
        "actuator_id": actuator_id,
        "state": cmd.state,
        "message": f"Actuator {actuator_id} set to {cmd.state}",
    }


@app.get("/actuators/{actuator_id}/history")
async def get_actuator_history(actuator_id: str, limit: int = 50):
    """Return command history for a specific actuator from the database."""
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT id, actuator_id, previous_state, new_state, source, reason, rule_id, executed_at
                    FROM actuator_commands
                    WHERE actuator_id = :actuator_id
                    ORDER BY executed_at DESC
                    LIMIT :limit
                """),
                {"actuator_id": actuator_id, "limit": limit}
            )
            rows = result.fetchall()
            commands = []
            for row in rows:
                commands.append({
                    "id": row[0],
                    "actuator_id": row[1],
                    "previous_state": row[2],
                    "new_state": row[3],
                    "source": row[4],
                    "reason": row[5],
                    "rule_id": row[6],
                    "executed_at": row[7].isoformat() if row[7] else None,
                })
            return {"count": len(commands), "commands": commands}
    except Exception as e:
        logger.error(f"Failed to query command history: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
