import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import app.controllers.inventory_controller as inventory_controller
from app.core.schemas import InventorySchema
from app.models.product import Inventory


def _session_for(record):
    result = MagicMock()
    result.scalar_one_or_none.return_value = record

    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = AsyncMock()
    return db


def _product(seller_id):
    return Inventory(
        name="Chair",
        description="Wooden chair",
        unit_price=25.5,
        sku="CTD-0001",
        available_quantity=8,
        reserved_quantity=0,
        seller_id=seller_id,
        images=[],
    )


def test_seller_can_update_inventory_with_uuid_subject():
    seller_id = uuid4()
    record = _product(seller_id)
    db = _session_for(record)

    with patch.object(inventory_controller, "inventory_event_payload", return_value={}):
        asyncio.run(
            inventory_controller.InventoryCRUD.update_inventory_item(
                db,
                InventorySchema(sku=record.sku, name="Updated chair"),
                {"id": str(seller_id), "role": "seller"},
            )
        )

    db.commit.assert_awaited_once()
    assert record.name == "Updated chair"


def test_seller_can_delete_inventory_with_uuid_subject():
    seller_id = uuid4()
    record = _product(seller_id)
    db = _session_for(record)

    asyncio.run(
        inventory_controller.InventoryCRUD.delete_inventory_item(
            db,
            InventorySchema(sku=record.sku),
            {"id": str(seller_id), "role": "seller"},
        )
    )

    db.delete.assert_awaited_once_with(record)
    db.commit.assert_awaited_once()
