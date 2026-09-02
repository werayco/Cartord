from sqlalchemy import or_, select
from app.kafka.producer import kafka_manager
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import WalletCreate
from app.models import Payment, UserWallet, OutboxEvent
from app.core.config import settings
from fastapi import Request, status
from fastapi.exceptions import HTTPException
import secrets
from app.core.logging import logger
from app.core.schemas import PaymentStatus

class PaymentProcessorController:
    @staticmethod
    async def create_wallet(payload: WalletCreate, db: AsyncSession, req: Request):
        incoming_key = req.headers.get("SHARED_API_KEY")
        logger.info(f"incoming header key is {incoming_key}")

        if not incoming_key or not secrets.compare_digest(
            incoming_key, settings.SERVICE_SHARED_KEY
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing shared API key",)

        try:
            result = UserWallet(customer_id=payload.customer_id)
            db.add(result)
            await db.commit()
            await db.refresh(result)
            return result
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def process_payment(order_event: dict, db: AsyncSession):
        order_id = order_event.get("order_id")
        sku = order_event.get("sku")
        quantity = order_event.get("quantity")
        customer_id = order_event.get("customer_id")
        unit_price = order_event.get("unit_price")
        email = order_event.get("email")

        if None in (order_id, sku, quantity, customer_id, unit_price, email):
            logger.error(f"Malformed order event, missing required fields: {order_event}")
            return

        existing = (await db.execute(select(Payment).where(Payment.order_id == order_id))).scalar_one_or_none()
        if existing:
            logger.info(f"Payment for order {order_id} already processed, skipping")
            return

        try:
            subtotal = unit_price * quantity
            wallet = (await db.execute(select(UserWallet).where(UserWallet.customer_id == customer_id).with_for_update())).scalar_one_or_none()

            if wallet and wallet.current_balance >= subtotal:
                wallet.current_balance -= subtotal
                status = PaymentStatus.SUCCEEDED
                event_type = "payment.succeeded"
                logger.info("Payment for order is successful.")
            else:
                status = PaymentStatus.FAILED
                event_type = "payment.failed"
                logger.error("Payment for order failed: insufficient balance.")

            payment = Payment(customer_id=customer_id, order_id=order_id, sku=sku, subtotal=subtotal, status=status)
            db.add(payment)
            await db.flush()

            db.add(OutboxEvent(
                event_type=event_type,
                aggregate_id=str(payment.id),
                payload={
                    "payment_id": str(payment.id),
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "subtotal": float(subtotal),
                    "status": status.value,
                    "email": email,
                },
            ))
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error processing payment for order {order_id}: {e}")
            try:
                db.add(OutboxEvent(
                    event_type="order.failed",
                    aggregate_id=order_id,
                    payload={"order_id": order_id, "customer_id": customer_id, "reason": str(e)},
                ))
                await db.commit()
                logger.info(f"Published order.failed for order {order_id}")
            except Exception as publish_err:
                await db.rollback()
                logger.critical(f"Failed to publish order.failed for order {order_id}: {publish_err}")
            raise