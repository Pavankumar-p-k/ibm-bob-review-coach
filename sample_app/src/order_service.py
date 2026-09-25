"""Order processing service for the sample application."""
import json
import logging

logger = logging.getLogger(__name__)

def process_order(order_data):
    # Missing input validation
    item = order_data["item"]
    qty = order_data["qty"]
    price = order_data["price"]

    total = qty * price
    if qty > 100:
        total = total * 0.9
    elif qty > 50:
        total = total * 0.95

    order = {
        "item": item,
        "qty": qty,
        "price": price,
        "total": total,
        "status": "pending"
    }
    logger.info("Order processed: %s", order)
    return order

def process_bulk_order(order_data):
    # Duplicated logic from process_order — intentional code smell
    item = order_data["item"]
    qty = order_data["qty"]
    price = order_data["price"]

    total = qty * price
    if qty > 100:
        total = total * 0.9
    elif qty > 50:
        total = total * 0.95

    order = {
        "item": item,
        "qty": qty,
        "price": price,
        "total": total,
        "status": "bulk_pending"
    }
    logger.info("Bulk order processed: %s", order)
    return order

def cancel_order(order_id, reason):
    # No validation, no auth check
    logger.info("Cancelling order %s for reason: %s", order_id, reason)
    return {"order_id": order_id, "status": "cancelled", "reason": reason}

def get_order_history(user_id):
    # Stub — no implementation
    pass

def apply_discount(order, discount_code):
    # Magic numbers, no documentation
    if discount_code == "SAVE10":
        order["total"] = order["total"] * 0.90
    elif discount_code == "SAVE20":
        order["total"] = order["total"] * 0.80
    elif discount_code == "HALFOFF":
        order["total"] = order["total"] * 0.50
    return order

def serialize_order(order):
    return json.dumps(order)

def deserialize_order(order_str):
    return json.loads(order_str)
