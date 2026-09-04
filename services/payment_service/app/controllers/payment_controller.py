from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import Roles, WalletCreate
from app.models import Payment, UserWallet, OutboxEvent
from app.core.config import settings
from fastapi import Request, status
from fastapi.exceptions import HTTPException
import secrets
from app.core.logging import logger
from app.core.schemas import PaymentStatus
from app.models import Payment, UserWallet, SellerWallet, OutboxEvent  # add SellerWallet to the import

class PaymentProcessorController:
    @staticmethod
    async def create_buyer_wallet_from_event(event: dict, db: AsyncSession):
        customer_id = event.get("customer_id")
        if not customer_id:
            logger.error(f"Malformed buyer.registered event, missing customer_id: {event}")
            return

        existing = (await db.execute(
            select(UserWallet).where(UserWallet.customer_id == customer_id)
        )).scalar_one_or_none()
        if existing:
            logger.info(f"Buyer wallet for {customer_id} already exists, skipping")
            return

        try:
            db.add(UserWallet(customer_id=customer_id))
            await db.commit()
            logger.info(f"Buyer wallet created for {customer_id}")
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def create_seller_wallet_from_event(event: dict, db: AsyncSession):
        seller_id = event.get("customer_id")
        if not seller_id:
            logger.error(f"Malformed seller.registered event, missing customer_id: {event}")
            return

        existing = (await db.execute(
            select(SellerWallet).where(SellerWallet.seller_id == seller_id)
        )).scalar_one_or_none()
        if existing:
            logger.info(f"Seller wallet for {seller_id} already exists, skipping")
            return

        try:
            db.add(SellerWallet(seller_id=seller_id))
            await db.commit()
            logger.info(f"Seller wallet created for {seller_id}")
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def process_payment(order_event: dict, db: AsyncSession):
        order_id = order_event.get("order_id")
        sku = order_event.get("sku")
        quantity = order_event.get("quantity")
        customer_id = order_event.get("customer_id")
        unit_price = order_event.get("unit_price")
        email = order_event.get("email")
        seller_id = order_event.get("seller_id")  # Get seller_id from the order event

        if None in (order_id, sku, quantity, customer_id, unit_price, email, seller_id):
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
                logger.info(f"Payment for order {order_id} is successful.")
                await PaymentProcessorController.increase_seller_wallet(seller_id, subtotal, db)
                logger.info(f"Seller wallet for {seller_id} increased by {subtotal}.")
            else:
                status = PaymentStatus.FAILED
                event_type = "payment.failed"
                logger.error(f"Payment for order {order_id} failed: insufficient balance.")

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
                    "seller_id": seller_id,
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
                    payload={"order_id": order_id, "customer_id": customer_id, "reason": str(e), "seller_id": seller_id},
                ))
                await db.commit()
                logger.info(f"Published order.failed for order {order_id}")
            except Exception as publish_err:
                await db.rollback()
                logger.critical(f"Failed to publish order.failed for order {order_id}: {publish_err}")
            raise

    @staticmethod
    async def get_seller_wallet(db: AsyncSession, current_user: dict):
        if current_user["role"] != Roles.SELLER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        try:
            result = await db.execute(select(SellerWallet).where(SellerWallet.seller_id == current_user["id"]))
            wallets = result.scalar_one_or_none()
            return wallets
        except Exception as e:
            logger.error(f"Error retrieving seller wallets: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving seller wallets")

    @staticmethod
    async def get_buyer_wallet(db: AsyncSession, current_user: dict):
        if current_user["role"] != Roles.BUYER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        try:
            result = await db.execute(select(UserWallet).where(UserWallet.customer_id == current_user["id"]))
            wallets = result.scalar_one_or_none()
            return wallets
        except Exception as e:
            logger.error(f"Error retrieving buyer wallets: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving buyer wallets")

@staticmethod
async def increase_seller_wallet(seller_id: str, amount, db: AsyncSession):
    wallet = (await db.execute(
        select(SellerWallet).where(SellerWallet.seller_id == seller_id).with_for_update()
    )).scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller wallet not found")
    wallet.current_balance += amount
    return wallet