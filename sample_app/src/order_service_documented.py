"""Order processing service for the sample application.

Provides functions for creating, cancelling, discounting, and serializing
order records.

Note:
    Several functions in this module contain intentional code smells and missing
    validations for demo/review purposes.
"""
import json
import logging

logger = logging.getLogger(__name__)


def process_order(order_data):
    """Process a single customer order and compute the total price.

    Applies a quantity-based discount tier to the line-item total:

    * ``qty > 100`` → 10 % discount (total × 0.90)
    * ``50 < qty ≤ 100`` → 5 % discount (total × 0.95)
    * ``qty ≤ 50`` → no discount

    Note:
        No input validation is performed on ``order_data``; missing keys will
        raise a ``KeyError``. This is intentional for demo purposes.

    Args:
        order_data (dict): A mapping containing at minimum:
            * ``"item"`` (str): Name or SKU of the item being ordered.
            * ``"qty"`` (int): Number of units requested.
            * ``"price"`` (float): Unit price in the application currency.

    Returns:
        dict: An order record with keys ``"item"``, ``"qty"``, ``"price"``,
        ``"total"`` (float, after discount), and ``"status"`` set to
        ``"pending"``.
    """
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
    """Process a bulk customer order and compute the total price.

    Applies the same quantity-based discount tiers as :func:`process_order` but
    sets the order status to ``"bulk_pending"`` to distinguish it from a
    standard order.

    Note:
        This function duplicates the discount logic from :func:`process_order`
        and is retained as an intentional code smell for demo purposes.

    Args:
        order_data (dict): A mapping containing at minimum:
            * ``"item"`` (str): Name or SKU of the item being ordered.
            * ``"qty"`` (int): Number of units requested.
            * ``"price"`` (float): Unit price in the application currency.

    Returns:
        dict: An order record with keys ``"item"``, ``"qty"``, ``"price"``,
        ``"total"`` (float, after discount), and ``"status"`` set to
        ``"bulk_pending"``.
    """
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
    """Mark an order as cancelled and record the cancellation reason.

    Note:
        This function performs no authentication or ownership verification and
        accepts any ``order_id`` without validation. These omissions are
        intentional for demo purposes.

    Args:
        order_id (str | int): The identifier of the order to cancel.
        reason (str): A human-readable explanation for the cancellation.

    Returns:
        dict: A result mapping with keys ``"order_id"``, ``"status"``
        (``"cancelled"``), and ``"reason"``.
    """
    # No validation, no auth check
    logger.info("Cancelling order %s for reason: %s", order_id, reason)
    return {"order_id": order_id, "status": "cancelled", "reason": reason}


def get_order_history(user_id):
    """Retrieve the complete order history for a given user.

    Note:
        This function is currently a stub with no implementation and always
        returns ``None``.

    Args:
        user_id (int | str): The identifier of the user whose order history
            should be retrieved.

    Returns:
        None: Not yet implemented.
    """
    # Stub — no implementation
    pass


def apply_discount(order, discount_code):
    """Apply a promotional discount code to an existing order.

    Supported discount codes and their effects:

    * ``"SAVE10"``  → 10 % off (total × 0.90)
    * ``"SAVE20"``  → 20 % off (total × 0.80)
    * ``"HALFOFF"`` → 50 % off (total × 0.50)

    Unrecognised codes leave the order total unchanged.

    Args:
        order (dict): An order record as returned by :func:`process_order`.
            Must contain a ``"total"`` key with a numeric value.
        discount_code (str): The promotional code to apply.

    Returns:
        dict: The mutated ``order`` dictionary with an updated ``"total"``
        value.
    """
    # Magic numbers, no documentation
    if discount_code == "SAVE10":
        order["total"] = order["total"] * 0.90
    elif discount_code == "SAVE20":
        order["total"] = order["total"] * 0.80
    elif discount_code == "HALFOFF":
        order["total"] = order["total"] * 0.50
    return order


def serialize_order(order):
    """Serialize an order dictionary to a JSON string.

    Args:
        order (dict): An order record to serialize. All values must be
            JSON-serializable.

    Returns:
        str: A JSON-encoded string representation of the order.
    """
    return json.dumps(order)


def deserialize_order(order_str):
    """Deserialize an order from a JSON string.

    Args:
        order_str (str): A JSON-encoded string previously produced by
            :func:`serialize_order` or a compatible source.

    Returns:
        dict: The reconstructed order record.

    Raises:
        json.JSONDecodeError: If ``order_str`` is not valid JSON.
    """
    return json.loads(order_str)
