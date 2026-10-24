import asyncio
import json
import logging

from confluent_kafka import Consumer, Producer
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from opentelemetry.trace import get_tracer_provider

from app.core.config import settings
from app.services.email_client import email_service
import html

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(self):
        inst = ConfluentKafkaInstrumentor()
        tracer_provider = get_tracer_provider()

        consumer = Consumer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": "notification-service",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self.consumer = inst.instrument_consumer(
            consumer, tracer_provider=tracer_provider
        )

        dlq_producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
        self.dlq_producer = inst.instrument_producer(dlq_producer, tracer_provider)

        self._running = False

    @staticmethod
    def _event_type(msg):
        headers = msg.headers()
        if not headers:
            return None
        for k, v in headers:
            if k == "eventType":
                return v.decode() if isinstance(v, bytes) else v
        return None


    async def _send_welcome_email(self, event_data: dict, role: str):
        try:
            email = event_data.get("email")
            if not email:
                logger.error(
                    "No email found in %s registration event", role
                )
                return

            email = email.strip()
            if not self._is_valid_email(email):
                logger.error("Invalid email address: %s", email)
                return

            name = html.escape(
                str(event_data.get("name") or "there").strip()
            )

            if role == "buyer":
                subject = "Welcome to Cartord!"
                heading = "Welcome to Cartord!"
                message = (
                    "Discover products, find what you need, "
                    "and enjoy a seamless shopping experience."
                )
                next_step = (
                    "Start exploring our marketplace and find "
                    "something you'll love."
                )
            elif role == "seller":
                subject = "Welcome to Cartord Seller Community!"
                heading = "Welcome to the Cartord Seller Community!"
                message = (
                    "We're excited to have you on board. "
                    "Cartord gives you a place to showcase your "
                    "products and connect with buyers."
                )
                next_step = (
                    "Get started by setting up your store, "
                    "adding your products, and preparing to "
                    "receive orders."
                )
            else:
                logger.error("Unsupported welcome email role: %s", role)
                return

            html_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport"
                      content="width=device-width, initial-scale=1.0">
                <title>{html.escape(subject)}</title>
            </head>
            <body style="margin:0; padding:24px;
                         font-family:Arial,sans-serif;
                         color:#333; background-color:#f5f5f5;">
                <div style="max-width:600px; margin:0 auto;
                            padding:32px; background:#ffffff;
                            border-radius:8px;">
                    <h1 style="color:#2563eb;">{heading}</h1>
                    <p>Hi {name},</p>
                    <p>{message}</p>
                    <p>{next_step}</p>
                    <p>We're glad you're here!</p>
                    <p>Best regards,<br>The Cartord Team</p>
                </div>
            </body>
            </html>
            """

            await email_service.send_email(
                to=email,
                subject=subject,
                html_body=html_body,
                from_email=settings.EMAIL_FROM.strip(),
                from_name="Cartord",
            )

            logger.info(
                "%s welcome email sent to %s",
                role.capitalize(),
                email,
            )

        except Exception:
            logger.exception(
                "Failed to send %s welcome email", role
            )
            raise


    async def _send_payment_email(self, event_data: dict, status: str):
        try:
            email = event_data.get("email")
            if not email:
                logger.error(f"No email found in payment data: {event_data}")
                customer_id = event_data.get("customer_id")
                if customer_id:
                    logger.info(
                        f"Attempting to fetch email for customer_id: {customer_id}"
                    )
                    return
                return

            payment_id = event_data.get("payment_id", "Unknown")
            order_id = event_data.get("order_id", "Unknown")
            subtotal = event_data.get("subtotal", 0.00)

            status = status.lower()

            email = email.strip()
            if not self._is_valid_email(email):
                logger.error(f"Invalid email address: {email}")
                return

            if status == "succeeded":
                subject = f"Payment Successful - Order #{order_id}"
                html_body = f"""
                <html>
                <body>
                    <h1>Payment Successful!</h1>
                    <p>Dear Customer,</p>
                    <p>Your payment has been successfully processed.</p>
                    <ul>
                        <li><strong>Payment ID:</strong> {payment_id}</li>
                        <li><strong>Order ID:</strong> {order_id}</li>
                        <li><strong>Amount:</strong> ${subtotal:.2f}</li>
                    </ul>
                    <p>Thank you for your purchase!</p>
                </body>
                </html>
                """
            else:
                subject = f"Payment Failed - Order #{order_id}"
                html_body = f"""
                <html>
                <body>
                    <h1>Payment Failed</h1>
                    <p>Dear Customer,</p>
                    <p>We were unable to process your payment.</p>
                    <ul>
                        <li><strong>Payment ID:</strong> {payment_id}</li>
                        <li><strong>Order ID:</strong> {order_id}</li>
                        <li><strong>Amount:</strong> ${subtotal:.2f}</li>
                    </ul>
                    <p>Please try again or contact support.</p>
                </body>
                </html>
                """

            from_email = settings.EMAIL_FROM.strip()

            logger.info(f"Sending {status} email to {email} for order {order_id}")

            await email_service.send_email(
                to=email,
                subject=subject,
                html_body=html_body,
                from_email=from_email,
                from_name="Payment Service",
            )
            logger.info(
                f"Payment {status} email sent to {email} for payment {payment_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send payment email: {e}")
            raise

    def _is_valid_email(self, email: str) -> bool:
        """Simple email validation"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    async def _process_message(self, msg):
        """Process a single message with proper context handling"""
        key_bytes = msg.key()
        value_bytes = msg.value()
        event_type = self._event_type(msg)

        try:
            value = json.loads(value_bytes.decode("utf-8")) if value_bytes else {}

            if event_type == "payment.succeeded":
                await self._send_payment_email(value, "succeeded")
            elif event_type == "payment.failed":
                await self._send_payment_email(value, "failed")
            elif event_type == "buyer.registered":
                await self._send_welcome_email(value, "buyer")
            elif event_type == "seller.registered":
                await self._send_welcome_email(value, "seller")

            return True, None
        except Exception as e:
            logger.error(f"Failed to process message at offset {msg.offset()}: {e}")
            return False, str(e)

    async def _send_to_dlq_async(self, key_bytes, value_bytes, error: str):
        """Async version of sending to DLQ"""
        try:
            original_value = None
            if value_bytes:
                try:
                    original_value = json.loads(value_bytes.decode("utf-8"))
                except:
                    original_value = value_bytes.decode(errors="replace")

            dlq_message = {
                "original_value": original_value,
                "error": error,
                "timestamp": asyncio.get_event_loop().time(),
            }

            self.dlq_producer.produce(
                topic="payment.dlq",
                key=key_bytes,
                value=json.dumps(dlq_message).encode("utf-8"),
            )
            self.dlq_producer.flush()
            logger.info("Message sent to DLQ successfully")
        except Exception as dlq_err:
            logger.critical(
                f"Failed to publish to DLQ, message permanently lost: {dlq_err}"
            )

    async def consume(self):
        self.consumer.subscribe(["payment", "auth"])
        self._running = True
        loop = asyncio.get_event_loop()

        try:
            while self._running:
                msg = await loop.run_in_executor(None, self.consumer.poll, 1.0)
                if msg is None:
                    continue

                if msg.error():
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                success, error = await self._process_message(msg)

                await loop.run_in_executor(None, self.consumer.commit, msg)

                if not success and error:
                    key_bytes = msg.key()
                    value_bytes = msg.value()
                    await self._send_to_dlq_async(key_bytes, value_bytes, error)

        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
        finally:
            self.consumer.close()

    def stop(self):
        self._running = False

    async def run(self):
        await self.consume()


kafka_manager = KafkaConsumer()
