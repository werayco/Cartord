from sqlalchemy import inspect

from app.models.product import Inventory
from app.services.inventory_events import inventory_event_payload


def test_new_inventory_event_serializes_initialized_images():
    product = Inventory(
        name="Chair",
        description="Wooden chair",
        sku="CTD-0001",
        unit_price=25.5,
        available_quantity=8,
        reserved_quantity=0,
        images=[],
    )

    assert inspect(product).attrs.images.loaded_value == []
    assert inventory_event_payload(product)["images"] == []
