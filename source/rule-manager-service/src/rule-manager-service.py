"""
Rule Manager Service - Mars Habitat Automation Platform

CRUD API for automation rules stored in PostgreSQL.
Provides endpoints to create, read, update, delete, and toggle rules.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://mars_user:mars_password@database:5432/mars_habitat")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8003"))

VALID_OPERATORS = ("<", "<=", "=", ">", ">=")


# --- SQLAlchemy models ---

class Base(DeclarativeBase):
    pass


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sensor_id = Column(String(100), nullable=False)
    operator = Column(String(10), nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=False)
    threshold_unit = Column(String(20), nullable=True)
    actuator_id = Column(String(100), nullable=False)
    actuator_action = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sensor_id": self.sensor_id,
            "operator": self.operator,
            "threshold_value": float(self.threshold_value),
            "threshold_unit": self.threshold_unit,
            "actuator_id": self.actuator_id,
            "actuator_action": self.actuator_action,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# --- Pydantic schemas ---

class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sensor_id: str
    operator: str
    threshold_value: float
    threshold_unit: Optional[str] = None
    actuator_id: str
    actuator_action: str

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("actuator_action")
    @classmethod
    def validate_action(cls, v):
        v_upper = v.upper()
        if v_upper not in ("ON", "OFF"):
            raise ValueError("actuator_action must be ON or OFF")
        return v_upper


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sensor_id: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_unit: Optional[str] = None
    actuator_id: Optional[str] = None
    actuator_action: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v is not None and v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("actuator_action")
    @classmethod
    def validate_action(cls, v):
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ("ON", "OFF"):
                raise ValueError("actuator_action must be ON or OFF")
            return v_upper
        return v


# --- Database setup ---

engine = None
async_session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, async_session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Database engine created")
    yield
    await engine.dispose()
    logger.info("Database engine disposed")


# --- FastAPI app ---

app = FastAPI(
    title="Mars Habitat Rule Manager Service",
    description="CRUD API for automation rules",
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
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "service": "rule-manager-service",
        "database": db_status,
    }


@app.get("/rules")
async def get_rules():
    """Get all automation rules."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at FROM automation_rules ORDER BY id")
        )
        rows = result.fetchall()
        rules = []
        for row in rows:
            rules.append({
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
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            })
        return {"count": len(rules), "rules": rules}


@app.get("/rules/{rule_id}")
async def get_rule(rule_id: int):
    """Get a specific automation rule by ID."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {
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
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None,
        }


@app.post("/rules", status_code=201)
async def create_rule(rule: RuleCreate):
    """Create a new automation rule."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO automation_rules (name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at)
                VALUES (:name, :description, :sensor_id, :operator, :threshold_value, :threshold_unit, :actuator_id, :actuator_action, TRUE, NOW(), NOW())
                RETURNING id, name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at
            """),
            {
                "name": rule.name,
                "description": rule.description,
                "sensor_id": rule.sensor_id,
                "operator": rule.operator,
                "threshold_value": rule.threshold_value,
                "threshold_unit": rule.threshold_unit,
                "actuator_id": rule.actuator_id,
                "actuator_action": rule.actuator_action,
            }
        )
        await session.commit()
        row = result.fetchone()
        logger.info(f"Created rule: {row[1]} (id={row[0]})")
        return {
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
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None,
        }


@app.put("/rules/{rule_id}")
async def update_rule(rule_id: int, rule: RuleUpdate):
    """Update an existing automation rule (partial update)."""
    # Build dynamic update
    updates = {}
    if rule.name is not None:
        updates["name"] = rule.name
    if rule.description is not None:
        updates["description"] = rule.description
    if rule.sensor_id is not None:
        updates["sensor_id"] = rule.sensor_id
    if rule.operator is not None:
        updates["operator"] = rule.operator
    if rule.threshold_value is not None:
        updates["threshold_value"] = rule.threshold_value
    if rule.threshold_unit is not None:
        updates["threshold_unit"] = rule.threshold_unit
    if rule.actuator_id is not None:
        updates["actuator_id"] = rule.actuator_id
    if rule.actuator_action is not None:
        updates["actuator_action"] = rule.actuator_action
    if rule.is_active is not None:
        updates["is_active"] = rule.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = rule_id

    async with async_session() as session:
        # Check existence
        check = await session.execute(
            text("SELECT id FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        if check.fetchone() is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        await session.execute(
            text(f"UPDATE automation_rules SET {set_clauses}, updated_at = NOW() WHERE id = :id"),
            updates
        )
        await session.commit()

        # Return updated rule
        result = await session.execute(
            text("SELECT id, name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action, is_active, created_at, updated_at FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        row = result.fetchone()
        logger.info(f"Updated rule id={rule_id}")
        return {
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
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None,
        }


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete an automation rule."""
    async with async_session() as session:
        check = await session.execute(
            text("SELECT id FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        if check.fetchone() is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        await session.execute(
            text("DELETE FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        await session.commit()
        logger.info(f"Deleted rule id={rule_id}")
        return {"message": "Rule deleted", "id": rule_id}


@app.patch("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: int):
    """Toggle a rule's is_active status."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, is_active FROM automation_rules WHERE id = :id"),
            {"id": rule_id}
        )
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        new_status = not row[1]
        await session.execute(
            text("UPDATE automation_rules SET is_active = :active, updated_at = NOW() WHERE id = :id"),
            {"active": new_status, "id": rule_id}
        )
        await session.commit()
        logger.info(f"Toggled rule id={rule_id} → is_active={new_status}")
        return {"id": rule_id, "is_active": new_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
