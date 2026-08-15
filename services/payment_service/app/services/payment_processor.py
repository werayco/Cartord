
async def process_payment(order_event: dict):
    """
    Handles an `order.created` event relayed from order_service's outbox.
    order_event = {order_id, sku, quantity, customer_id}

    This is a starting point — plug in the real charge call and persist a
    Payment row once payment_service's models/db session are built out.
    """
    order_id, sku, quantity, customer_id, unit_price = order_event.get("order_id"), order_event.get("sku"), order_event.get("quantity"), order_event.get("customer_id"),order_event.get("unit_price")
    subtotal= unit_price *  quantity
    
    # TODO: charge the customer, persist a Payment row, and optionally
    # write a payment.succeeded / payment.failed OutboxEvent here.