"""
Data History Service - Mars Habitat Automation Platform

Subscribes to normalized sensor events from RabbitMQ and persists them
to the sensor_readings table in PostgreSQL. Exposes a REST API for querying
historical readings with filtering, pagination, and aggregation.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from fastapi import FastAPI, HTTPException, Query
from collections import deque
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
PORT = int(os.getenv("PORT", "8006"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "5.0"))

# Stats
stats = {
    "events_received": 0,
    "events_stored": 0,
    "events_failed": 0,
}

# Global references
db_engine = None

# Write buffer for batched inserts
write_buffer: list[dict] = []
buffer_lock = asyncio.Lock()

sensor_cache = deque(maxlen=50)
cache_lock = asyncio.Lock()
cache_id_counter = 0


async def flush_buffer():
    """Flush the write buffer to the database in a single batch insert."""
    global write_buffer
    async with buffer_lock:
        if not write_buffer:
            return
        batch = write_buffer[:]
        write_buffer = []

    try:
        async with db_engine.connect() as conn:
            await conn.execute(
                text("""
                    INSERT INTO sensor_readings (sensor_id, value, unit, source, recorded_at)
                    VALUES (:sensor_id, :value, :unit, :source, :recorded_at)
                """),
                batch,
            )
            await conn.commit()
        stats["events_stored"] += len(batch)
        logger.debug(f"Flushed {len(batch)} readings to database")
    except Exception as e:
        stats["events_failed"] += len(batch)
        logger.error(f"Failed to flush batch to database: {e}")


async def periodic_flush():
    """Periodically flush the write buffer."""
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        await flush_buffer()


async def store_event(event: dict):
    """Buffer a sensor event for batched database insertion."""
    timestamp_str = event.get("timestamp")
    try:
        recorded_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else datetime.now(timezone.utc)
    except (ValueError, AttributeError):
        recorded_at = datetime.now(timezone.utc)

    # Strip timezone info: DB column is TIMESTAMP (no timezone), value is always UTC
    recorded_at = recorded_at.replace(tzinfo=None)

    reading = {
        "sensor_id": event.get("sensor_id", "unknown"),
        "value": event.get("value", 0),
        "unit": event.get("unit", ""),
        "source": event.get("source", "unknown"),
        "recorded_at": recorded_at,
    }

    should_flush = False
    async with buffer_lock:
        write_buffer.append(reading)
        if len(write_buffer) >= BATCH_SIZE:
            should_flush = True

    if should_flush:
        await flush_buffer()

    stats["events_received"] += 1


async def process_event(message: AbstractIncomingMessage):
    """Process an incoming sensor event from RabbitMQ."""
    global cache_id_counter
    try:
        event = json.loads(message.body.decode())
        
        async with cache_lock:
            cache_id_counter += 1
            event["_cache_id"] = cache_id_counter
            sensor_cache.append(event)
            
        await store_event(event)
        await message.ack()
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        await message.ack()


async def consume_events():
    """Connect to RabbitMQ and consume normalized sensor events."""
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=50)

                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )

                queue = await channel.declare_queue(
                    "data_history_queue",
                    durable=True,
                    arguments={"x-message-ttl": 86400000},
                )

                await queue.bind(exchange, routing_key=ROUTING_KEY)
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

    db_engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

    # Start background tasks
    consumer_task = asyncio.create_task(consume_events())
    flush_task = asyncio.create_task(periodic_flush())

    yield

    # Flush remaining data
    await flush_buffer()

    # Cleanup
    consumer_task.cancel()
    flush_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    try:
        await flush_task
    except asyncio.CancelledError:
        pass

    await db_engine.dispose()


app = FastAPI(
    title="Mars Habitat Data History Service",
    description="Stores and queries historical sensor readings",
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
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "service": "data-history-service",
        "database": db_status,
        "stats": stats,
    }


@app.get("/sensors/latest")
async def get_latest_sensors(last_id: int = Query(default=0)):
    new_events = []
    current_last_id = last_id
    
    async with cache_lock:
        for ev in sensor_cache:
            if ev.get("_cache_id", 0) > last_id:
                new_events.append(ev)
                current_last_id = max(current_last_id, ev.get("_cache_id", 0))

    return {
        "count": len(new_events),
        "last_id": current_last_id,
        "events": new_events,
    }


@app.get("/history")
async def get_history(
    sensor_id: Optional[str] = Query(default=None, description="Filter by sensor ID"),
    source: Optional[str] = Query(default=None, description="Filter by source (rest/stream)"),
    start: Optional[str] = Query(default=None, description="Start time (ISO 8601)"),
    end: Optional[str] = Query(default=None, description="End time (ISO 8601)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """
        Query historical sensor readings with optional filters.
    
        This route takes in input some parameters, every parameter is optional.
        It returns a list of sensor readings with the specified filters applied.
    """
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if sensor_id:
        conditions.append("sensor_id = :sensor_id")
        params["sensor_id"] = sensor_id
    if source:
        conditions.append("source = :source")
        params["source"] = source
    if start:
        conditions.append("recorded_at >= :start")
        params["start"] = start
    if end:
        conditions.append("recorded_at <= :end")
        params["end"] = end

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                    SELECT id, sensor_id, value, unit, source, recorded_at, created_at
                    FROM sensor_readings
                    WHERE {where_clause}
                    ORDER BY recorded_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                params,
            )
            rows = result.fetchall()

            count_result = await conn.execute(
                text(f"SELECT COUNT(*) FROM sensor_readings WHERE {where_clause}"),
                params,
            )
            total = count_result.scalar()

        readings = []
        for row in rows:
            readings.append({
                "id": row[0],
                "sensor_id": row[1],
                "value": float(row[2]),
                "unit": row[3],
                "source": row[4],
                "recorded_at": row[5].isoformat() if row[5] else None,
                "created_at": row[6].isoformat() if row[6] else None,
            })

        return {
            "total": total,
            "count": len(readings),
            "offset": offset,
            "limit": limit,
            "readings": readings,
        }
    except Exception as e:
        logger.error(f"Failed to query history: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/history/{sensor_id}")
async def get_sensor_history(
    sensor_id: str,
    start: Optional[str] = Query(default=None, description="Start time (ISO 8601)"),
    end: Optional[str] = Query(default=None, description="End time (ISO 8601)"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get historical readings for a specific sensor."""
    conditions = ["sensor_id = :sensor_id"]
    params: dict = {"sensor_id": sensor_id, "limit": limit}

    if start:
        conditions.append("recorded_at >= :start")
        params["start"] = start
    if end:
        conditions.append("recorded_at <= :end")
        params["end"] = end

    where_clause = " AND ".join(conditions)

    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                    SELECT id, sensor_id, value, unit, source, recorded_at
                    FROM sensor_readings
                    WHERE {where_clause}
                    ORDER BY recorded_at DESC
                    LIMIT :limit
                """),
                params,
            )
            rows = result.fetchall()

        readings = []
        for row in rows:
            readings.append({
                "id": row[0],
                "sensor_id": row[1],
                "value": float(row[2]),
                "unit": row[3],
                "source": row[4],
                "recorded_at": row[5].isoformat() if row[5] else None,
            })

        return {"sensor_id": sensor_id, "count": len(readings), "readings": readings}
    except Exception as e:
        logger.error(f"Failed to query sensor history: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/history/{sensor_id}/aggregate")
async def get_sensor_aggregate(
    sensor_id: str,
    interval: str = Query(default="1h", description="Aggregation interval: 5m, 15m, 1h, 6h, 1d"),
    start: Optional[str] = Query(default=None, description="Start time (ISO 8601)"),
    end: Optional[str] = Query(default=None, description="End time (ISO 8601)"),
):
    """Get aggregated (avg, min, max) readings for a sensor grouped by time interval."""
    # Map user-friendly intervals to date_trunc precision
    trunc_map = {
        "5m": ("minute", 5),
        "15m": ("minute", 15),
        "1h": ("hour", 1),
        "6h": ("hour", 6),
        "1d": ("day", 1),
    }
    trunc_info = trunc_map.get(interval)
    if trunc_info is None:
        raise HTTPException(status_code=400, detail=f"Invalid interval. Use one of: {list(trunc_map.keys())}")

    trunc_precision, trunc_step = trunc_info

    conditions = ["sensor_id = :sensor_id"]
    params: dict = {"sensor_id": sensor_id}

    if start:
        conditions.append("recorded_at >= :start")
        params["start"] = start
    if end:
        conditions.append("recorded_at <= :end")
        params["end"] = end

    where_clause = " AND ".join(conditions)

    # For minute-based intervals use epoch rounding; for hour/day use date_trunc
    if trunc_precision == "minute":
        bucket_expr = f"to_timestamp(floor(extract(epoch from recorded_at) / ({trunc_step} * 60)) * ({trunc_step} * 60))"
    elif trunc_precision == "hour" and trunc_step > 1:
        bucket_expr = f"to_timestamp(floor(extract(epoch from recorded_at) / ({trunc_step} * 3600)) * ({trunc_step} * 3600))"
    else:
        bucket_expr = f"date_trunc('{trunc_precision}', recorded_at)"

    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                    SELECT
                        {bucket_expr} AS bucket,
                        AVG(value) AS avg_value,
                        MIN(value) AS min_value,
                        MAX(value) AS max_value,
                        COUNT(*) AS sample_count,
                        MIN(unit) AS unit
                    FROM sensor_readings
                    WHERE {where_clause}
                    GROUP BY bucket
                    ORDER BY bucket DESC
                    LIMIT 200
                """),
                params,
            )
            rows = result.fetchall()

        buckets = []
        for row in rows:
            buckets.append({
                "timestamp": row[0].isoformat() if row[0] else None,
                "avg": float(row[1]) if row[1] is not None else None,
                "min": float(row[2]) if row[2] is not None else None,
                "max": float(row[3]) if row[3] is not None else None,
                "count": row[4],
                "unit": row[5],
            })

        return {
            "sensor_id": sensor_id,
            "interval": interval,
            "buckets": buckets,
        }
    except Exception as e:
        logger.error(f"Failed to aggregate sensor data: {e}")
        raise HTTPException(status_code=500, detail="Aggregation query failed")


@app.get("/sensors")
async def list_sensors():
    """List all sensors that have historical data, with their latest reading."""
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT DISTINCT ON (sensor_id)
                        sensor_id, value, unit, source, recorded_at
                    FROM sensor_readings
                    ORDER BY sensor_id, recorded_at DESC
                """)
            )
            rows = result.fetchall()

        sensors = []
        for row in rows:
            sensors.append({
                "sensor_id": row[0],
                "latest_value": float(row[1]),
                "unit": row[2],
                "source": row[3],
                "last_recorded_at": row[4].isoformat() if row[4] else None,
            })

        return {"count": len(sensors), "sensors": sensors}
    except Exception as e:
        logger.error(f"Failed to list sensors: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
