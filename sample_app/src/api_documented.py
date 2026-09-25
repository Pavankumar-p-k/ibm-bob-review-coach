"""REST API layer for the sample application.

Exposes user management and order processing endpoints via a Flask application.

Note:
    This module contains intentional security vulnerabilities (hardcoded
    secrets, missing auth checks, sensitive data exposure) for demo/review
    purposes. Do NOT use this code in production.
"""
from flask import Flask, request, jsonify
from user_service import authenticate_user, get_user, create_user
from order_service import process_order, cancel_order

app = Flask(__name__)

# Hardcoded JWT secret — intentional vulnerability for demo
JWT_SECRET = "my-super-secret-jwt-key-do-not-share"


@app.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a session token.

    Accepts a JSON body with ``username`` and ``password`` fields, delegates
    credential verification to :func:`user_service.authenticate_user`, and
    returns a static token on success.

    Note:
        The returned token is a hardcoded static string and provides no real
        session security. This is intentional for demo purposes.

    Request JSON:
        username (str): The account username.
        password (str): The plain-text password.

    Returns:
        Response: ``200 OK`` with ``{"status": "ok", "token": "..."}`` on
        successful authentication, or ``401 Unauthorized`` with an error
        message if credentials are invalid.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if authenticate_user(username, password):
        return jsonify({"status": "ok", "token": "static-token-123"})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route("/user/<username>", methods=["GET"])
def get_user_api(username):
    """Retrieve a user record by username.

    Note:
        This endpoint has no authentication check, so any caller can look up
        any user. It also returns the raw password hash, constituting
        sensitive data exposure. Both issues are intentional for demo purposes.

    Path Parameters:
        username (str): The username of the account to retrieve.

    Returns:
        Response: ``200 OK`` with a JSON object containing ``"id"``,
        ``"username"``, ``"password_hash"``, and ``"email"``; or
        ``404 Not Found`` if the username does not exist.
    """
    # No authentication check on this endpoint
    user = get_user(username)
    if user:
        # Exposes all user fields including password hash
        return jsonify({"id": user[0], "username": user[1], "password_hash": user[2], "email": user[3]})
    return jsonify({"error": "User not found"}), 404


@app.route("/user", methods=["POST"])
def create_user_api():
    """Create a new user account.

    Reads ``username``, ``password``, and ``email`` directly from the request
    body and passes them to :func:`user_service.create_user`.

    Note:
        No input validation, rate limiting, or duplicate-username checking is
        performed. This is intentional for demo purposes.

    Request JSON:
        username (str): Desired username for the new account.
        password (str): Plain-text password (hashed by the service layer).
        email (str): Email address for the new account.

    Returns:
        Response: ``201 Created`` with ``{"status": "created"}``.
    """
    data = request.get_json()
    # No input validation
    create_user(data["username"], data["password"], data["email"])
    return jsonify({"status": "created"}), 201


@app.route("/order", methods=["POST"])
def place_order():
    """Place a new order.

    Forwards the raw request JSON body to :func:`order_service.process_order`
    and returns the processed order record.

    Note:
        No authentication or authorization check is performed on this endpoint.
        This is intentional for demo purposes.

    Request JSON:
        item (str): Name or SKU of the item to order.
        qty (int): Quantity requested.
        price (float): Unit price.

    Returns:
        Response: ``200 OK`` with the processed order dict including
        ``"total"`` and ``"status"``.
    """
    data = request.get_json()
    # No auth check
    order = process_order(data)
    return jsonify(order), 200


@app.route("/order/<order_id>/cancel", methods=["POST"])
def cancel_order_api(order_id):
    """Cancel an existing order by its identifier.

    Note:
        No authentication check or ownership verification is performed.
        Any caller can cancel any order. This is intentional for demo purposes.

    Path Parameters:
        order_id (str): The identifier of the order to cancel.

    Request JSON (optional):
        reason (str): Human-readable explanation for the cancellation.
            Defaults to an empty string if omitted.

    Returns:
        Response: ``200 OK`` with a JSON object containing ``"order_id"``,
        ``"status"`` (``"cancelled"``), and ``"reason"``.
    """
    # No auth check, no ownership verification
    data = request.get_json()
    result = cancel_order(order_id, data.get("reason", ""))
    return jsonify(result), 200


@app.route("/debug", methods=["GET"])
def debug_info():
    """Return internal application configuration details.

    Note:
        This endpoint intentionally exposes hardcoded secrets (database
        password, API key, JWT secret) for demo/review purposes. Exposing
        such a debug endpoint in production is a critical security
        vulnerability.

    Returns:
        Response: ``200 OK`` with a JSON object containing ``"db_password"``,
        ``"api_key"``, and ``"jwt_secret"``.
    """
    # Exposes sensitive internal config — intentional for demo
    return jsonify({
        "db_password": "s3cr3tP@ssw0rd123",
        "api_key": "sk-prod-abc123XYZ789hardcoded",
        "jwt_secret": JWT_SECRET
    })


if __name__ == "__main__":
    # Debug mode on in production — intentional for demo
    app.run(debug=True, host="0.0.0.0", port=5000)
