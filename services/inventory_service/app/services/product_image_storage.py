import asyncio
import json
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core import logger, settings
from app.services.product_image_validation import has_image_signature


class ImageStorageError(Exception):
    pass


class InvalidImageUpload(Exception):
    pass


class ProductImageStorage:
    def __init__(self):
        self._internal_client = None
        self._public_client = None
        self._ready = False
        self._lock = asyncio.Lock()

    def _client(self, endpoint: str):
        if not settings.MINIO_ACCESS_KEY or not settings.MINIO_SECRET_KEY:
            raise ImageStorageError("Product image storage credentials are not configured")
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                # MinIO does not implement the CRC checksum headers boto3 sends by default.
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def _internal(self):
        if not settings.MINIO_ENDPOINT:
            raise ImageStorageError("Product image storage endpoint is not configured")
        if self._internal_client is None:
            self._internal_client = self._client(settings.MINIO_ENDPOINT)
        return self._internal_client

    def _public(self):
        if not settings.MINIO_PUBLIC_ENDPOINT:
            raise ImageStorageError("Public product image endpoint is not configured")
        if self._public_client is None:
            self._public_client = self._client(settings.MINIO_PUBLIC_ENDPOINT)
        return self._public_client

    async def ensure_bucket(self) -> None:
        if self._ready:
            return
        async with self._lock:
            if self._ready:
                return
            try:
                await asyncio.to_thread(self._ensure_bucket_sync)
                self._ready = True
                logger.info("Product image bucket is ready: %s", settings.MINIO_BUCKET)
            except (BotoCoreError, ClientError, ImageStorageError):
                logger.exception(
                    "Failed to prepare product image bucket: %s", settings.MINIO_BUCKET
                )
                raise ImageStorageError("Product image storage is unavailable") from None

    def _ensure_bucket_sync(self) -> None:
        client = self._internal()
        try:
            client.head_bucket(Bucket=settings.MINIO_BUCKET)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            client.create_bucket(Bucket=settings.MINIO_BUCKET)

        self._allow_browser_uploads(client)
        client.put_bucket_policy(
            Bucket=settings.MINIO_BUCKET,
            Policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"],
                        }
                    ],
                }
            ),
        )

    def _allow_browser_uploads(self, client) -> None:
        origins = [
            origin.strip()
            for origin in settings.MINIO_CORS_ORIGINS.split(",")
            if origin.strip()
        ]
        if not origins:
            return
        try:
            client.put_bucket_cors(
                Bucket=settings.MINIO_BUCKET,
                CORSConfiguration={
                    "CORSRules": [
                        {
                            "AllowedOrigins": origins,
                            "AllowedMethods": ["GET", "PUT", "HEAD"],
                            "AllowedHeaders": ["*"],
                            "ExposeHeaders": ["ETag"],
                            "MaxAgeSeconds": 3600,
                        }
                    ]
                },
            )
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            # Community MinIO does not implement bucket CORS. Local Compose sets
            # MINIO_API_CORS_ALLOW_ORIGIN on the MinIO server instead.
            if code != "NotImplemented":
                raise
            logger.info(
                "Storage server does not support bucket CORS for %s",
                settings.MINIO_BUCKET,
            )

    async def create_upload_url(
        self, object_key: str, content_type: str, file_size: int
    ) -> str:
        await self.ensure_bucket()
        try:
            return await asyncio.to_thread(
                self._public().generate_presigned_url,
                "put_object",
                Params={
                    "Bucket": settings.MINIO_BUCKET,
                    "Key": object_key,
                    "ContentType": content_type,
                    "ContentLength": file_size,
                },
                ExpiresIn=settings.MINIO_UPLOAD_URL_TTL_SECONDS,
            )
        except (BotoCoreError, ClientError, ImageStorageError) as error:
            logger.exception("Failed to create a product image upload URL")
            raise ImageStorageError("Could not prepare image upload") from error

    async def verify_uploaded_image(
        self, object_key: str, content_type: str, expected_size: int
    ) -> None:
        await self.ensure_bucket()
        try:
            await asyncio.to_thread(
                self._verify_uploaded_image_sync,
                object_key,
                content_type,
                expected_size,
            )
        except InvalidImageUpload:
            raise
        except (BotoCoreError, ClientError, ImageStorageError) as error:
            logger.exception("Failed to verify uploaded product image")
            raise ImageStorageError("Could not verify uploaded image") from error

    def _verify_uploaded_image_sync(
        self, object_key: str, content_type: str, expected_size: int
    ) -> None:
        client = self._internal()
        try:
            metadata = client.head_object(Bucket=settings.MINIO_BUCKET, Key=object_key)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise InvalidImageUpload("Upload the image before completing it") from error
            raise

        file_size = int(metadata.get("ContentLength", 0))
        if file_size != expected_size or file_size > settings.MINIO_MAX_IMAGE_SIZE_BYTES:
            raise InvalidImageUpload("Uploaded image size does not match the request")
        if metadata.get("ContentType") != content_type:
            raise InvalidImageUpload("Uploaded image content type does not match")

        response = client.get_object(
            Bucket=settings.MINIO_BUCKET,
            Key=object_key,
            Range="bytes=0-11",
        )
        body = response["Body"]
        try:
            signature = body.read(12)
        finally:
            body.close()
        if not has_image_signature(content_type, signature):
            raise InvalidImageUpload("Uploaded file is not a supported image")

    async def delete_object(self, object_key: str) -> None:
        await self.ensure_bucket()
        try:
            await asyncio.to_thread(
                self._internal().delete_object,
                Bucket=settings.MINIO_BUCKET,
                Key=object_key,
            )
        except (BotoCoreError, ClientError, ImageStorageError) as error:
            logger.exception("Failed to delete product image object")
            raise ImageStorageError("Could not delete product image") from error

    def public_url(self, object_key: str) -> str:
        if not settings.MINIO_PUBLIC_ENDPOINT:
            raise ImageStorageError("Public product image endpoint is not configured")
        endpoint = settings.MINIO_PUBLIC_ENDPOINT.rstrip("/")
        bucket = quote(settings.MINIO_BUCKET, safe="")
        key = quote(object_key, safe="/")
        return f"{endpoint}/{bucket}/{key}"


product_image_storage = ProductImageStorage()
