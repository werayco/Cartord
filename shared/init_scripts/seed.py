import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    Sequence,
    String,
    Table,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv(dotenv_path="./shared/compose_files/.env")

DATABASE_URL = os.getenv("INVENTORY_DATABASE_URL")
INVENTORY_JSON_PATH = Path(__file__).parent.parent / "inventory.json"

metadata = MetaData()
sku_sequence = Sequence("inventory_sku_seq", metadata=metadata)

inventory = Table(
    "inventory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("description", String(255), nullable=True),
    Column("unit_price", Numeric(10, 2), nullable=False),
    Column("sku", String(50), primary_key=True, autoincrement=False, unique=True),
    Column("available_quantity", Integer, nullable=False, default=0),
    Column("reserved_quantity", Integer, nullable=False, default=0),
    Column("seller_id", PGUUID(as_uuid=True), nullable=True),
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
                    name = item["name"]
                    unit_price = item["price"]
                    available_quantity = item.get(
                        "available_quantity", item.get("quantity", 0)
                    )
                except KeyError:
                    skipped += 1
                    continue

                description = item.get("description")
                is_active = item.get("is_active", True)
                reserved_quantity = item.get("reserved_quantity", 0)

                existing_result = await conn.execute(
                    select(inventory.c.id, inventory.c.sku)
                    .where(
                        func.lower(func.trim(inventory.c.name)) == name.strip().lower()
                    )
                    .limit(1)
                )
                existing = existing_result.one_or_none()

                if existing is not None:
                    sku = existing.sku
                    updated_result = await conn.execute(
                        inventory.update()
                        .where(inventory.c.id == existing.id, inventory.c.sku == sku)
                        .values(
                            name=name,
                            description=description,
                            unit_price=unit_price,
                            available_quantity=available_quantity,
                            is_active=is_active,
                            updated_at=now,
                        )
                        .returning(inventory.c.reserved_quantity, inventory.c.seller_id)
                    )
                    reserved_quantity, seller_id = updated_result.one()
                    inventory_id = existing.id
                    event_type = "inventory.updated"
                else:
                    sequence_value = await conn.scalar(
                        select(sku_sequence.next_value())
                    )
                    sku = (
                        f"CTD-{sequence_value:04d}"
                        if sequence_value < 10000
                        else f"CTD-{sequence_value}"
                    )
                    result = await conn.execute(
                        inventory.insert()
                        .values(
                            name=name,
                            description=description,
                            unit_price=unit_price,
                            sku=sku,
                            available_quantity=available_quantity,
                            reserved_quantity=reserved_quantity,
                            seller_id=None,
                            is_active=is_active,
                            created_at=now,
                            updated_at=now,
                        )
                        .returning(inventory.c.id)
                    )
                    inventory_id = result.scalar_one()
                    seller_id = None
                    event_type = "inventory.created"

                payload = {
                    "id": inventory_id,
                    "name": name,
                    "description": description,
                    "unit_price": unit_price,
                    "sku": sku,
                    "available_quantity": available_quantity,
                    "reserved_quantity": reserved_quantity,
                    "seller_id": str(seller_id) if seller_id is not None else None,
                }
                await conn.execute(
                    inventory_outbox_events.insert().values(
                        id=uuid4(),
                        event_type=event_type,
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
