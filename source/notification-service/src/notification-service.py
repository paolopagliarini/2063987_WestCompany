"""
Notification Service - Mars Habitat Automation Platform

Receives events from RabbitMQ and pushes notifications to clients via SSE.
Stores recent notifications in-memory for new client connections.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@messagging:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "mars_events")
ROUTING_KEY = os.getenv("ROUTING_KEY", "events.#")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8004"))

# In-memory storage for recent notifications (last 100)
MAX_NOTIFICATIONS = 100
notifications_store: deque = deque(maxlen=MAX_NOTIFICATIONS)

# Connected SSE clients
sse_clients: list = []
sse_clients_lock = asyncio.Lock()


class Notification(BaseModel):
    """Notification model for rule triggers and alerts."""
    notification_id: str
    event_id: str
    sensor_id: str
    metric: str
    value: float
    unit: str
    status: str
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    actuator_id: Optional[str] = None
    actuator_action: Optional[str] = None
    message: str
    timestamp: str
    severity: str  # "info", "warning", "critical"


def parse_event_to_notification(event_data: dict) -> Optional[Notification]:
    """
    Parse a normalized event and create a notification if relevant.

    Creates notifications for:
    - Events with status='warning' (critical sensor readings)
    - Events that triggered a rule (actuator commands)
    """
    import uuid

    try:
        event_id = event_data.get("event_id", str(uuid.uuid4()))
        sensor_id = event_data.get("sensor_id", "unknown")
        metric = event_data.get("metric", "unknown")
        value = event_data.get("value", 0)
        unit = event_data.get("unit", "")
        status = event_data.get("status", "ok")
        source = event_data.get("source", "unknown")

        # Determine severity based on status
        if status == "warning":
            severity = "warning"
            message = f"⚠️ {sensor_id}: {metric} = {value} {unit} (WARNING)"
        elif status == "critical":
            severity = "critical"
            message = f"🚨 {sensor_id}: {metric} = {value} {unit} (CRITICAL)"
        else:
            severity = "info"
            message = f"📊 {sensor_id}: {metric} = {value} {unit}"

        # Check if this is a rule-triggered event
        rule_id = event_data.get("rule_id")
        rule_name = event_data.get("rule_name")
        actuator_id = event_data.get("actuator_id")
        actuator_action = event_data.get("actuator_action")

        if rule_id and actuator_id:
            severity = "warning"
            message = f"🔧 Rule '{rule_name}' triggered: {sensor_id} {metric}={value}{unit} → {actuator_id}={actuator_action}"

        if severity == "info":
            return None

        notification = Notification(
            notification_id=str(uuid.uuid4()),
            event_id=event_id,
            sensor_id=sensor_id,
            metric=metric,
            value=value,
            unit=unit,
            status=status,
            rule_id=rule_id,
            rule_name=rule_name,
            actuator_id=actuator_id,
            actuator_action=actuator_action,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity
        )

        return notification

    except Exception as e:
        logger.error(f"Error parsing event: {e}")
        return None


async def broadcast_notification(notification: Notification):
    """Send notification to all connected SSE clients."""
    async with sse_clients_lock:
        disconnected = []
        for queue in sse_clients:
            try:
                await queue.put(notification)
            except Exception as e:
                logger.warning(f"Error sending to client: {e}")
                disconnected.append(queue)

        # Remove disconnected clients
        for q in disconnected:
            if q in sse_clients:
                sse_clients.remove(q)


async def process_event(message: AbstractIncomingMessage):
    """Process incoming event from RabbitMQ."""
    try:
        event_data = json.loads(message.body.decode())
        logger.info(f"Received event: {event_data.get('sensor_id', 'unknown')}")

        notification = parse_event_to_notification(event_data)
        if notification:
            # Store notification
            notifications_store.append(notification.model_dump())
            logger.info(f"Created notification: {notification.message}")

            # Broadcast to SSE clients
            await broadcast_notification(notification)

        await message.ack()

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.ack()


async def consume_events():
    """Connect to RabbitMQ and consume events."""
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                # Declare exchange
                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True
                )

                # Declare queue
                queue = await channel.declare_queue(
                    "notification_queue",
                    durable=True,
                    arguments={
                        "x-message-ttl": 86400000,  # 24 hours TTL
                        "x-overflow": "reject-publish-dlx"
                    }
                )

                # Bind queue to exchange
                await queue.bind(exchange, routing_key=ROUTING_KEY)

                logger.info(f"Listening for events with routing key: {ROUTING_KEY}")

                # Consume messages
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        await process_event(message)

        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}")
            logger.info("Retrying connection in 5 seconds...")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Start event consumer in background
    consumer_task = asyncio.create_task(consume_events())

    yield

    # Cleanup
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Mars Habitat Notification Service",
    description="SSE-based notification service for real-time alerts",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "connected_clients": len(sse_clients),
        "stored_notifications": len(notifications_store)
    }


@app.get("/notifications")
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    severity: Optional[str] = Query(default=None, regex="^(info|warning|critical)$")
):
    """
    Get recent notifications.

    - **limit**: Maximum number of notifications to return (1-100)
    - **severity**: Filter by severity level (info, warning, critical)
    """
    notifications = list(notifications_store)

    if severity:
        notifications = [n for n in notifications if n.get("severity") == severity]

    # Return most recent first
    notifications = notifications[-limit:][::-1]

    return {
        "count": len(notifications),
        "notifications": notifications
    }


@app.get("/notifications/stream")
async def notification_stream():
    """
    SSE endpoint for real-time notifications.

    Clients connect here to receive live notifications as they occur.
    Also sends the last 10 notifications on connection for context.
    """
    async def event_generator():
        queue = asyncio.Queue()

        # Register client
        async with sse_clients_lock:
            sse_clients.append(queue)

        logger.info(f"New SSE client connected. Total clients: {len(sse_clients)}")

        try:
            # Send last 10 notifications for context
            for notification in list(notifications_store)[-10:]:
                yield f"data: {json.dumps(notification)}\n\n"

            # Send connection confirmation
            yield f"event: connected\ndata: {{\"status\": \"connected\", \"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"

            # Stream new notifications
            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(notification.model_dump())}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive every 30 seconds
                    yield f"event: keepalive\ndata: {{\"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"

        except asyncio.CancelledError:
            logger.info("Client disconnected")
        finally:
            # Unregister client
            async with sse_clients_lock:
                if queue in sse_clients:
                    sse_clients.remove(queue)
            logger.info(f"Client removed. Total clients: {len(sse_clients)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/notifications/stats")
async def get_notification_stats():
    """Get notification statistics."""
    notifications = list(notifications_store)

    severity_counts = {"info": 0, "warning": 0, "critical": 0}
    sensor_counts = {}

    for n in notifications:
        severity = n.get("severity", "info")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        sensor_id = n.get("sensor_id", "unknown")
        sensor_counts[sensor_id] = sensor_counts.get(sensor_id, 0) + 1

    return {
        "total_notifications": len(notifications),
        "by_severity": severity_counts,
        "by_sensor": sensor_counts,
        "connected_clients": len(sse_clients)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)