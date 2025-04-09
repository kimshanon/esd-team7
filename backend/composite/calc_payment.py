from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Service URLs
CUSTOMER_SERVICE_URL = "http://customer-service:5000"
PAYMENT_SERVICE_URL = "http://payment-service:5004"

@app.route("/")
def home():
    return "Credit Management Composite Microservice"

@app.route("/credits/add", methods=['POST'])
def add_credits():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["customer_id", "amount"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    customer_id = data["customer_id"]
    amount = data["amount"]
    
    # Validate amount is positive
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be a valid number"}), 400
    
    try:
        # Step 1: Add credits to customer account
        customer_response = requests.post(
            f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/add-credits",
            json={"amount": amount_value}
        )
        
        if customer_response.status_code != 200:
            return jsonify({
                "error": "Failed to add credits to customer account",
                "details": customer_response.json()
            }), customer_response.status_code
        
        # Step 2: Create payment transaction
        payment_data = {
            "log_id": "hello",
            "customer_id": customer_id,
            "event_type": "Credit Top-Up",
            "event_details": f"Credits added: ${amount_value}",
            "payment_amount": amount_value,
            "payment_status": "Paid",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            payment_response = requests.post(
                f"{PAYMENT_SERVICE_URL}/payment",
                json=payment_data
            )
        except Exception as payment_error:
            return jsonify({"error": "Error creating payment transaction", "details": str(payment_error)}), 500
        
        if payment_response.status_code != 201:
            # If payment transaction fails, we should ideally roll back the customer credit update
            # This is a simplified version without rollback
            return jsonify({
                "error": "Failed to create payment transaction",
                "details": payment_response.json()
            }), payment_response.status_code
        
        # Return combined response
        return jsonify({
            "message": "Credits added successfully",
            "customer_update": customer_response.json(),
            "payment_transaction": payment_response.json()
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

@app.route("/credits/use", methods=['POST'])
def use_credits():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["customer_id", "amount", "order_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    customer_id = data["customer_id"]
    amount = data["amount"]
    order_id = data["order_id"]
    
    # Validate amount is positive
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be a valid number"}), 400
    
    try:
        # Step 1: Check if customer has enough credits
        customer_response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}")
        
        if customer_response.status_code != 200:
            return jsonify({
                "error": "Failed to retrieve customer information",
                "details": customer_response.json()
            }), customer_response.status_code
        
        customer_data = customer_response.json()
        current_credits = customer_data.get("customer_credits", 0)
        
        if current_credits < amount_value:
            return jsonify({
                "error": "Insufficient credits",
                "current_credits": current_credits,
                "required_amount": amount_value
            }), 400
        
        # Step 2: Create payment transaction
        payment_data = {
            "log_id": f"payment_{uuid.uuid4()}",
            "order_id": order_id,
            "customer_id": customer_id,
            "event_type": "Payment",
            "event_details": f"Payment for order {order_id}",
            "payment_amount": amount_value,
            "payment_status": "Paid",
            "timestamp": datetime.now().isoformat()
        }
        
        payment_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payment",
            json=payment_data
        )
    
        
        if payment_response.status_code != 201:
            return jsonify({
                "error": "Failed to create payment transaction",
                "details": payment_response.json()
            }), payment_response.status_code
        
        # Step 3: Deduct credits from customer account
        # We'll create a dedicated endpoint for this in the customer service
        # For now, we'll simulate it by adding negative credits
        deduct_response = requests.post(
            f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/add-credits",
            json={"amount": -amount_value}
        )
        
        if deduct_response.status_code != 200:
            # If deducting credits fails, we should ideally roll back the payment transaction
            # This is a simplified version without rollback
            return jsonify({
                "error": "Failed to deduct credits from customer account",
                "details": deduct_response.json()
            }), deduct_response.status_code
        
        # Return combined response
        return jsonify({
            "message": "Payment processed successfully",
            "payment_transaction": payment_response.json(),
            "remaining_credits": current_credits - amount_value
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009, threaded=True)
