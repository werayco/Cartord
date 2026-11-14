from app.core.utils import to_json_safe
from app.services.product_image_storage import product_image_storage


def image_response(image) -> dict:
    return {
        "id": str(image.id),
        "url": product_image_storage.public_url(image.object_key),
        "alt_text": image.alt_text,
        "sort_order": image.sort_order,
    }


def inventory_event_payload(record) -> dict:
    payload = {
        column.key: getattr(record, column.key)
        for column in record.__mapper__.column_attrs
    }
    payload["images"] = [
        image_response(image)
        for image in sorted(record.images, key=lambda item: item.sort_order)
        if image.status == "ready"
    ]
    return to_json_safe(payload)
