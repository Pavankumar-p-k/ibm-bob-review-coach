"""REST API layer for the sample application."""
from flask import Flask, request, jsonify
from user_service import authenticate_user, get_user, create_user
from order_service import process_order, cancel_order

app = Flask(__name__)

# Hardcoded JWT secret — intentional vulnerability for demo
JWT_SECRET = "my-super-secret-jwt-key-do-not-share"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if authenticate_user(username, password):
        return jsonify({"status": "ok", "token": "static-token-123"})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route("/user/<username>", methods=["GET"])
def get_user_api(username):
    # No authentication check on this endpoint
    user = get_user(username)
    if user:
        # Exposes all user fields including password hash
        return jsonify({"id": user[0], "username": user[1], "password_hash": user[2], "email": user[3]})
    return jsonify({"error": "User not found"}), 404

@app.route("/user", methods=["POST"])
def create_user_api():
    data = request.get_json()
    # No input validation
    create_user(data["username"], data["password"], data["email"])
    return jsonify({"status": "created"}), 201

@app.route("/order", methods=["POST"])
def place_order():
    data = request.get_json()
    # No auth check
    order = process_order(data)
    return jsonify(order), 200

@app.route("/order/<order_id>/cancel", methods=["POST"])
def cancel_order_api(order_id):
    # No auth check, no ownership verification
    data = request.get_json()
    result = cancel_order(order_id, data.get("reason", ""))
    return jsonify(result), 200

@app.route("/debug", methods=["GET"])
def debug_info():
    # Exposes sensitive internal config — intentional for demo
    return jsonify({
        "db_password": "s3cr3tP@ssw0rd123",
        "api_key": "sk-prod-abc123XYZ789hardcoded",
        "jwt_secret": JWT_SECRET
    })

if __name__ == "__main__":
    # Debug mode on in production — intentional for demo
    app.run(debug=True, host="0.0.0.0", port=5000)
