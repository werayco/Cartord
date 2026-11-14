from datetime import datetime
from uuid import uuid4

from app.core.schemas import InventoryResponse


def test_inventory_response_preserves_product_details_and_images():
    image_id = uuid4()
    response = InventoryResponse(
        name="Chair",
        description="Wooden chair",
        sku="CTD-0001",
        unit_price=25.5,
        available_quantity=8,
        reserved_quantity=2,
        created_at=datetime(2026, 1, 1),
        images=[
            {
                "id": image_id,
                "url": "http://localhost:9100/product-images/products/CTD-0001/image.jpg",
                "alt_text": "Front view",
                "sort_order": 0,
            }
        ],
    )

    assert response.description == "Wooden chair"
    assert response.reserved_quantity == 2
    assert response.images[0].id == image_id
