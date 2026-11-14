import re
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import logger, settings
from app.core.schemas import ProductImageUploadRequest
from app.models import Inventory, OutboxEvent, ProductImage
from app.services.inventory_events import image_response, inventory_event_payload
from app.services.product_image_validation import IMAGE_EXTENSIONS
from app.services.product_image_storage import (
    ImageStorageError,
    InvalidImageUpload,
    product_image_storage,
)

ALLOWED_ROLES = {"admin", "seller"}


async def _owned_product(
    db: AsyncSession, sku: str, current_user: dict
) -> Inventory:
    role = current_user.get("role")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied.")

    result = await db.execute(
        select(Inventory)
        .options(selectinload(Inventory.images))
        .where(Inventory.sku == sku)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    user_id = current_user.get("id")
    if role == "seller" and (
        not user_id or str(product.seller_id) != str(user_id)
    ):
        raise HTTPException(status_code=403, detail="Permission denied.")
    return product


def _validate_key(sku: str, object_key: str) -> None:
    pattern = rf"products/{re.escape(sku)}/[a-f0-9]{{32}}\.(jpg|png|webp)"
    if not re.fullmatch(pattern, object_key):
        raise HTTPException(status_code=400, detail="Invalid product image key")


async def create_upload(
    db: AsyncSession,
    sku: str,
    request: ProductImageUploadRequest,
    current_user: dict,
) -> dict:
    if request.content_type not in IMAGE_EXTENSIONS:
        logger.warning(
            "Rejected product image upload request sku=%s content_type=%s",
            sku,
            request.content_type,
        )
        raise HTTPException(
            status_code=415,
            detail="Use a JPEG, PNG, or WebP image.",
        )
    if request.file_size > settings.MINIO_MAX_IMAGE_SIZE_BYTES:
        logger.warning(
            "Rejected oversized product image upload sku=%s file_size=%s",
            sku,
            request.file_size,
        )
        raise HTTPException(
            status_code=413,
            detail="Product images must be 5 MB or smaller.",
        )

    product = await _owned_product(db, sku, current_user)
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    stale_uploads = [
        image
        for image in product.images
        if image.status == "pending" and image.created_at < cutoff
    ]
    for image in stale_uploads:
        try:
            await product_image_storage.delete_object(image.object_key)
        except ImageStorageError as error:
            raise HTTPException(
                status_code=503, detail="Could not clean up an expired image upload."
            ) from error
        product.images.remove(image)
        await db.delete(image)
    if stale_uploads:
        await db.flush()
        logger.info(
            "Removed expired product image uploads sku=%s count=%s",
            sku,
            len(stale_uploads),
        )

    ready_count = sum(1 for image in product.images if image.status == "ready")
    pending_count = sum(1 for image in product.images if image.status == "pending")
    if ready_count + pending_count >= settings.MINIO_MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=409,
            detail=f"A product can have at most {settings.MINIO_MAX_IMAGES_PER_PRODUCT} images.",
        )

    image_id = uuid4()
    object_key = (
        f"products/{sku}/{image_id.hex}.{IMAGE_EXTENSIONS[request.content_type]}"
    )
    try:
        upload_url = await product_image_storage.create_upload_url(
            object_key, request.content_type, request.file_size
        )
    except ImageStorageError as error:
        raise HTTPException(
            status_code=503, detail="Product image storage is unavailable."
        ) from error

    sort_order = max(
        (image.sort_order for image in product.images if image.status == "ready"),
        default=-1,
    ) + 1
    image = ProductImage(
        id=image_id,
        sku=product.sku,
        object_key=object_key,
        content_type=request.content_type,
        file_size=request.file_size,
        alt_text=request.alt_text.strip() if request.alt_text else None,
        sort_order=sort_order,
        status="pending",
    )
    db.add(image)
    try:
        await db.commit()
    except Exception as error:
        await db.rollback()
        logger.exception(
            "Failed to save product image upload intent sku=%s image_id=%s",
            sku,
            image_id,
        )
        raise HTTPException(
            status_code=500, detail="Could not prepare product image upload."
        ) from error

    logger.info(
        "Created product image upload URL sku=%s image_id=%s user_id=%s",
        sku,
        image_id,
        current_user.get("id"),
    )
    return {
        "image_id": image_id,
        "object_key": object_key,
        "upload_url": upload_url,
        "content_type": request.content_type,
    }


async def complete_upload(
    db: AsyncSession, sku: str, image_id: UUID, current_user: dict
) -> dict:
    product = await _owned_product(db, sku, current_user)
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=404, detail="Image upload not found")
    if image.status == "ready":
        return image_response(image)

    _validate_key(sku, image.object_key)
    ready_count = sum(1 for item in product.images if item.status == "ready")
    if ready_count >= settings.MINIO_MAX_IMAGES_PER_PRODUCT:
        try:
            await product_image_storage.delete_object(image.object_key)
        except ImageStorageError as error:
            raise HTTPException(
                status_code=503, detail="Product image storage is unavailable."
            ) from error
        await db.delete(image)
        await db.commit()
        raise HTTPException(
            status_code=409,
            detail=f"A product can have at most {settings.MINIO_MAX_IMAGES_PER_PRODUCT} images.",
        )

    try:
        await product_image_storage.verify_uploaded_image(
            image.object_key, image.content_type, image.file_size
        )
    except InvalidImageUpload as error:
        logger.warning(
            "Rejected uploaded product image sku=%s image_id=%s reason=%s",
            sku,
            image_id,
            error,
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ImageStorageError as error:
        raise HTTPException(
            status_code=503, detail="Product image storage is unavailable."
        ) from error

    next_sort_order = max(
        (
            item.sort_order
            for item in product.images
            if item.status == "ready" and item.id != image_id
        ),
        default=-1,
    ) + 1
    image.status = "ready"
    image.sort_order = next_sort_order
    try:
        await db.flush()
        db.add(
            OutboxEvent(
                event_type="inventory.updated",
                aggregate_id=str(product.id),
                payload=inventory_event_payload(product),
            )
        )
        await db.commit()
    except Exception as error:
        await db.rollback()
        logger.exception(
            "Failed to complete product image upload sku=%s image_id=%s",
            sku,
            image_id,
        )
        raise HTTPException(
            status_code=500, detail="Could not save product image."
        ) from error

    logger.info(
        "Completed product image upload sku=%s image_id=%s file_size=%s",
        sku,
        image_id,
        image.file_size,
    )
    return image_response(image)


async def delete_image(
    db: AsyncSession, sku: str, image_id: UUID, current_user: dict
) -> dict:
    product = await _owned_product(db, sku, current_user)
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=404, detail="Product image not found")

    try:
        await product_image_storage.delete_object(image.object_key)
    except ImageStorageError as error:
        raise HTTPException(
            status_code=503, detail="Product image storage is unavailable."
        ) from error

    was_ready = image.status == "ready"
    product.images.remove(image)
    await db.delete(image)
    try:
        if was_ready:
            await db.flush()
            db.add(
                OutboxEvent(
                    event_type="inventory.updated",
                    aggregate_id=str(product.id),
                    payload=inventory_event_payload(product),
                )
            )
        await db.commit()
    except Exception as error:
        await db.rollback()
        logger.exception(
            "Failed to remove product image metadata sku=%s image_id=%s",
            sku,
            image_id,
        )
        raise HTTPException(
            status_code=500, detail="Could not remove product image."
        ) from error

    logger.info(
        "Deleted product image sku=%s image_id=%s user_id=%s",
        sku,
        image_id,
        current_user.get("id"),
    )
    return {"message": "Product image deleted"}
