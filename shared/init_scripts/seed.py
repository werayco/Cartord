import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    MetaData,
    Table,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv(dotenv_path="./shared/compose_files/.env")

RAW_DATABASE_URL = os.getenv("INVENTORY_DATABASE_URL")
DATABASE_URL = RAW_DATABASE_URL.replace("@postgres", "@localhost")
INVENTORY_JSON_PATH = Path(__file__).parent.parent / "inventory.json"

metadata = MetaData()

inventory = Table(
    "inventory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("description", String(255), nullable=True),
    Column("unit_price", Numeric(10, 2), nullable=False),
    Column("sku", String(50), nullable=False, unique=True),
    Column("available_quantity", Integer, nullable=False, default=0),
    Column("reserved_quantity", Integer, nullable=False, default=0),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

inventory_outbox_events = Table(
    "inventory_outbox_events",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True),
    Column("event_type", String(255), nullable=False),
    Column("aggregate_id", String(255), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("status", String(50), nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("last_error", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


async def seed() -> None:
    if not INVENTORY_JSON_PATH.exists():
        raise FileNotFoundError(f"Could not find {INVENTORY_JSON_PATH}")

    with open(INVENTORY_JSON_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError("inventory.json must contain a JSON array of inventory items")

    engine = create_async_engine(DATABASE_URL)
    inserted, skipped = 0, 0
    now = datetime.utcnow()

    try:
        async with engine.begin() as conn:
            for item in items:
                try:
                    sku = item["sku"]
                    name = item["name"]
                    unit_price = item["price"]
                    available_quantity = item.get("available_quantity", item.get("quantity", 0))
                except KeyError as e:
                    logger.info(f"Skipping item, missing required field {e}: {item}")
                    skipped += 1
                    continue

                description = item.get("description")
                is_active = item.get("is_active", True)
                reserved_quantity = item.get("reserved_quantity", 0)

                stmt = pg_insert(inventory).values(
                    name=name,
                    description=description,
                    unit_price=unit_price,
                    sku=sku,
                    available_quantity=available_quantity,
                    reserved_quantity=reserved_quantity,
                    is_active=is_active,
                    created_at=now,
                    updated_at=now,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["sku"],
                    set_={
                        "name": stmt.excluded.name,
                        "description": stmt.excluded.description,
                        "unit_price": stmt.excluded.unit_price,
                        "available_quantity": stmt.excluded.available_quantity,
                        "is_active": stmt.excluded.is_active,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )
                result = await conn.execute(stmt.returning(inventory.c.id))
                inventory_id = result.scalar_one()
                payload = {
                    "id": inventory_id,
                    "name": name,
                    "description": description,
                    "unit_price": unit_price,
                    "sku": sku,
                    "available_quantity": available_quantity,
                    "reserved_quantity": reserved_quantity,
                    "seller_id": None,
                }
                await conn.execute(
                    inventory_outbox_events.insert().values(
                        id=uuid4(),
                        event_type="inventory.created",
                        aggregate_id=str(inventory_id),
                        payload=payload,
                        status="pending",
                        attempts=0,
                        available_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )
                inserted += 1

        print(f"Seed complete: {inserted} upserted, {skipped} skipped.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())