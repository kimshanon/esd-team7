import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

from flask_cors import CORS
CORS(app)

# Initialize firebase
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

ORDER_SERVICE_URL = "http://localhost:5003"  # Order service URL

@app.route("/")
def home():
    return "Payment Microservice (Using Firebase Firestore)"

# Get all payments
@app.route("/payments", methods=['GET'])
def get_all_payments():
    payments_ref = db.collection('payments')
    docs = payments_ref.stream()
    payments = [doc.to_dict() for doc in docs]

    if payments:
        return jsonify({"code": 200, "data": payments}), 200
    else:
        return jsonify({"code": 404, "message": "No payments found."}), 404
    
# Update payment status (includes 'refunded')
@app.route("/payment/<payment_id>/status", methods=['PUT'])
def update_payment_status(payment_id):
    data = request.get_json()
    new_status = data.get('payment_status')

    if not new_status:
        return jsonify({"code": 400, "message": "Payment status is required."}), 400

    payment_ref = db.collection('payments').document(payment_id)
    payment_ref.update({"payment_status": new_status})

    return jsonify({"code": 200, "message": f"Payment {payment_id} status updated to {new_status}."}), 200

# Get specific payment with payment_status
@app.route("/payment/<payment_id>", methods=['GET'])
def get_payment(payment_id):
    payment_ref = db.collection('payments').document(payment_id)
    payment = payment_ref.get()
    
    if payment.exists:
        payment_data = payment.to_dict()
        payment_status = payment_data.get("payment_status", "Unknown")
        return jsonify({"code": 200, "payment_status": payment_status}), 200
    else:
        return jsonify({"code": 404, "message": f"Payment {payment_id} not found."}), 404

# Get transaction details as JSON string
@app.route("/payment/<payment_id>/transaction", methods=['GET'])
def get_payment_details(payment_id):
    payment_ref = db.collection('payments').document(payment_id)
    payment = payment_ref.get()
    
    if payment.exists:
        payment_data = payment.to_dict()
        # Extracting the relevant payment fields
        required_fields = ["log_id", "order_id", "customer_id", "event_type", "event_details", "payment_amount", "payment_status", "timestamp"]
        payment_details = {field: payment_data.get(field, "Unknown") for field in required_fields}
        return jsonify({"code": 200, "payment_details": payment_details}), 200
    else:
        return jsonify({"code": 404, "message": f"Payment {payment_id} not found."}), 404

# Create a new payment transaction
@app.route('/payment', methods=['POST'])
def create_payment_transaction():
    data = request.get_json()
    
    # Define common required fields for both scenarios.
    common_required = [
        "log_id", 
        "customer_id", 
        "event_type", 
        "event_details", 
        "payment_amount", 
        "payment_status", 
        "timestamp"
    ]
    
    # Check for missing common fields.
    missing_common = [field for field in common_required if field not in data]
    if missing_common:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing_common)}"}), 400

    event_type = data.get("event_type")
    
    # For order payments, require "order_id".
    if event_type == "Payment":
        if "order_id" not in data:
            return jsonify({"error": "Missing required field: order_id for Payment events"}), 400
    else:
        # For Credit Top-Up, remove the order_id if it exists, since it's not applicable.
        data.pop("order_id", None)
    
    # Validate payment_amount is a positive number.
    try:
        amount = float(data["payment_amount"])
        if amount <= 0:
            return jsonify({"error": "payment_amount must be greater than zero"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "payment_amount must be a valid number"}), 400

    # Build the payment transaction record.
    payment_data = {
        "log_id": data["log_id"],
        "customer_id": data["customer_id"],
        "event_type": event_type,
        "event_details": data["event_details"],
        "payment_amount": amount,
        "payment_status": data["payment_status"],
        "timestamp": data["timestamp"],
    }

    # Include order_id only if event_type is "Payment"
    if event_type == "Payment":
        payment_data["order_id"] = data["order_id"]

    # Create a new document in the 'payments' collection.
    payment_ref = db.collection('payments').document()
    # Add the Firestore document ID to the payment data as payment_id.
    payment_data["payment_id"] = payment_ref.id

    payment_ref.set(payment_data)

    return jsonify({
        "message": "Payment transaction created successfully.",
        "transaction_id": payment_ref.id,
        "payment_data": payment_data
    }), 201

# Delete a payment
@app.route("/payments/<paymentID>", methods=['DELETE'])
def delete_payment(paymentID):
    payment_ref = db.collection('payments').document(paymentID)
    payment = payment_ref.get()

    if not payment.exists:
        return jsonify({"code": 404, "message": f"Payment {paymentID} not found."}), 404

    payment_ref.delete()
    return jsonify({"code": 200, "message": f"Payment {paymentID} has been deleted."}), 200

# Get payments by customer ID
@app.route("/payments/customer/<customer_id>", methods=['GET'])
def get_payments_by_customer_id(customer_id):
    try:
        # Query payments by customer_id
        payments_ref = db.collection("payments")
        query = payments_ref.where("customer_id", "==", customer_id)
        payments = query.stream()
        
        # Collect payments from query and format them into a list
        payment_list = []
        for payment in payments:
            payment_list.append(payment.to_dict())

        return jsonify(payment_list), 200  # Return only the list of payments
    except Exception as e:
        print(f"Error fetching payments: {e}")
        return jsonify({"error": "Could not fetch payments"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004, threaded=True)
