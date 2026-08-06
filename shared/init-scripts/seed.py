import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timezone

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
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

RAW_DATABASE_URL = os.environ.get("INVENTORY_DATABASE_URL", os.environ["DATABASE_URL"])
DATABASE_URL = RAW_DATABASE_URL.replace("@postgres", "@localhost")
INVENTORY_JSON_PATH = Path(__file__).parent / "inventory.json"

metadata = MetaData()

inventory = Table(
    "inventory",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String),
    Column("price", Numeric, nullable=False),
    Column("sku", String, nullable=False, unique=True),
    Column("quantity", Integer, nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
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
    now = datetime.now(timezone.utc)

    try:
        async with engine.begin() as conn:
            for item in items:
                try:
                    sku = item["sku"]
                    name = item["name"]
                    price = item["price"]
                    quantity = item["quantity"]
                except KeyError as e:
                    print(f"Skipping item, missing required field {e}: {item}")
                    skipped += 1
                    continue

                description = item.get("description")
                is_active = item.get("is_active", True)

                stmt = pg_insert(inventory).values(
                    name=name,
                    description=description,
                    price=price,
                    sku=sku,
                    quantity=quantity,
                    is_active=is_active,
                    created_at=now,
                    updated_at=now,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["sku"],
                    set_={
                        "name": stmt.excluded.name,
                        "description": stmt.excluded.description,
                        "price": stmt.excluded.price,
                        "quantity": stmt.excluded.quantity,
                        "is_active": stmt.excluded.is_active,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )
                await conn.execute(stmt)
                inserted += 1

        print(f"Seed complete: {inserted} upserted, {skipped} skipped.")
    finally:
        await engine.dispose()


# if __name__ == "__main__":
#     asyncio.run(seed())