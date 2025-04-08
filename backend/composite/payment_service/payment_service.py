from flask import Flask, request, jsonify
from datetime import datetime
import os
import uuid
import requests

app = Flask(__name__)

# Base URL of Microservices
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:5007")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:5003")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://localhost:5000")
PICKER_SERVICE_URL = os.getenv("PICKER_SERVICE_URL", "http://localhost:5001")

@app.route("/api/v1/payments/process", methods=["POST"])
def process_payment_endpoint():
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({
            "code": 400,
            "message": "Request body is required.",
            "data": None
        }), 400
        
    customer_id = data.get("customer_id")
    payment_amount = data.get("payment_amount")
    order_id = data.get("order_id")
    
    if not all([customer_id, payment_amount, order_id]):
        return jsonify({
            "code": 400,
            "message": "Missing required fields: customer_id, payment_amount, and order_id are required.",
            "data": None
        }), 400
    
    try:
        payment_amount = float(payment_amount)
    except (ValueError, TypeError):
        return jsonify({
            "code": 400,
            "message": "Payment amount must be a valid number.",
            "data": None
        }), 400
    
    # 1. Check and deduct customer credits
    credit_result = process_customer_payment(customer_id, payment_amount, order_id=order_id)
    
    if credit_result.get("code") != 200:
        return jsonify(credit_result), credit_result.get("code")
    
    # 2. Create payment record
    current_timestamp = datetime.utcnow().isoformat()
    payment_data = {
        "log_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "order_id": order_id,
        "payment_amount": payment_amount,
        "event_type": "Payment",
        "event_details": f"Payment for order {order_id}",
        "payment_status": "Paid",
        "timestamp": current_timestamp
    }
    
    payment_response = requests.post(f"{PAYMENT_SERVICE_URL}/api/v1/payments", json=payment_data)

    if payment_response.status_code != 201:
        # Rollback credit deduction if payment creation fails
        process_customer_refund(customer_id, payment_amount)
        
        # Update order status to Cancelled
        requests.patch(
            f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
            json={"order_status": "Cancelled"}
        )

        return jsonify({
            "code": 500,
            "message": "Failed to create payment record.",
            "data": None
        }), 500
    
    payment_id = payment_response.json().get("data", {}).get("payment_id")
    
    return jsonify({
        "code": 200, 
        "message": "Payment processed successfully.",
        "data": {
            "payment_id": payment_id,
            "status": "Paid"
        }
    }), 200

@app.route("/api/v1/orders/<order_id>/complete", methods=["POST"])
def complete_order_endpoint(order_id):
    # 1. Get order details
    order_response = requests.get(
        f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}"
    )

    if order_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": "Order not found.",
            "data": None
        }), 404
    
    order_data = order_response.json().get("data", {})
    order_status = order_data.get("order_status")
    picker_id = order_data.get("picker_id", "")
    payment_amount = float(order_data.get("credit", 0))
    
    # 2. Verify order can be completed
    if order_status != "Active":
        return jsonify({
            "code": 400,
            "message": "Only active orders can be completed.",
            "data": None
        }), 400
    
    if not picker_id:
        return jsonify({
            "code": 400,
            "message": "Order has no assigned picker.",
            "data": None
        }), 400
    
    # 3. Update order status to completed
    complete_response = requests.patch(
        f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
        json={"order_status": "Completed"}
    )
    
    if complete_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to update order status.",
            "data": None
        }), 500
    
    # 4. Add credits to picker account
    picker_result = process_picker_payment(picker_id, payment_amount)
    
    if picker_result.get("code") != 200:
        return jsonify(picker_result), picker_result.get("code")
    
    return jsonify({
        "code": 200,
        "message": f"Order {order_id} completed and picker credited successfully.",
        "data": {
            "order_id": order_id,
            "picker_id": picker_id,
            "status": "Completed"
        }
    }), 200

@app.route("/api/v1/orders/<payment_id>/refund", methods=["POST"])
def process_refund_endpoint(payment_id):
    # 1. Get payment information
    payment_response = requests.get(
        f"{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_id}/transaction"
    )

    if payment_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to retrieve payment details.",
            "data": None
        }), 500

    payment_data = payment_response.json().get("data", {})
    order_id = payment_data.get("order_id")
    customer_id = payment_data.get("customer_id")
    payment_amount = float(payment_data.get("payment_amount", 0))

    if not order_id:
        return jsonify({
            "code": 400,
            "message": "Order ID missing from payment details.",
            "data": None
        }), 400

    # 2. Get order details
    order_response = requests.get(
        f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}"
    )

    if order_response.status_code != 200:
        return jsonify({
            "code": 404,
            "message": "Order not found.",
            "data": None
        }), 404
    
    order_data = order_response.json().get("data", {})
    order_status = order_data.get("order_status")

    # 3. Only process refund if order is Active or Completed
    if order_status not in ["Active", "Completed"]:
        return jsonify({
            "code": 400,
            "message": "Refund can only be processed for Active or Completed orders.",
            "data": None
        }), 400
    
    # 4. Update payment status to "Refunded"
    refund_response = requests.put(
        f"{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_id}/status",
        json={"payment_status": "Refunded"}
    )

    if refund_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to update payment status.",
            "data": None
        }), 500

    # 5. Update order status to "Cancelled"
    cancel_response = requests.patch(
        f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
        json={"order_status": "Cancelled"}
    )

    if cancel_response.status_code != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to cancel order.",
            "data": None
        }), 500

    # 6. Add credits back to customer account
    credit_result = process_customer_refund(customer_id, payment_amount)
    
    if credit_result.get("code") != 200:
        return jsonify(credit_result), credit_result.get("code")

    return jsonify({
        "code": 200,
        "message": f"Refund processed for payment {payment_id}.",
        "data": {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "Refunded"
        }
    }), 200

def process_customer_payment(customer_id, amount, order_id=None):
    """
    Deduct credits from customer account for payment
    """
    try:
        # Validate inputs
        if not customer_id:
            return {"code": 400, "message": "Customer ID is required."}
        
        if amount <= 0:
            return {"code": 400, "message": "Payment amount must be greater than zero."}
            
        # 1. Get current customer credits
        customer_url = f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}"
        customer_response = requests.get(customer_url)

        if customer_response.status_code != 200:
            return {"code": 500, "message": "Failed to retrieve customer data."}

        response_data = customer_response.json()
        customer_data = response_data.get("Customer", {})
        customer_credits = float(customer_data.get("customerCredits", 0))
        
        # 2. Check if customer has enough credits
        if customer_credits < amount:
            # If turns out an order is made and the customer has insufficient credits
            if order_id:
                # Cancel the order using the dedicated cancel endpoint
                requests.patch(
                    f"{ORDER_SERVICE_URL}/orders/{order_id}/cancel"
                )
            return {"code": 400, "message": "Insufficient credits. Order cancelled."}
            
        # 3. Deduct credits
        new_credits = customer_credits - amount

        # 4. Update customer credits using the existing PUT endpoint
        update_data = {
            "customerCredits": new_credits
        }
        
        # Use the existing PUT endpoint to update customer data, including credits
        update_url = f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}"
        update_response = requests.put(update_url, json=update_data)

        if update_response.status_code != 200:
            return {"code": 500, "message": "Failed to update customer credits."}

        return {"code": 200, "message": "Payment processed successfully."}

    except Exception as e:
        return {"code": 500, "message": f"Error processing payment: {str(e)}"}

def process_customer_refund(customer_id, amount):
    """
    Add credits back to customer account for refund
    """
    try:
        # Validate inputs
        if not customer_id:
            return {"code": 400, "message": "Customer ID is required."}
        
        if amount <= 0:
            return {"code": 400, "message": "Refund amount must be greater than zero."}
            
        # 1. Get current customer credits
        customer_url = f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}"
        customer_response = requests.get(customer_url)

        if customer_response.status_code != 200:
            return {"code": 500, "message": "Failed to retrieve customer data."}

        response_data = customer_response.json()
        customer_data = response_data.get("Customer", {})
        customer_credits = float(customer_data.get("customerCredits", 0))
        
        # 2. Add refund amount to customer's credits
        new_credits = customer_credits + amount

        # 3. Update customer credits using the existing PUT endpoint
        update_data = {
            "customerCredits": new_credits
        }
        
        update_url = f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}"
        update_response = requests.put(update_url, json=update_data)

        if update_response.status_code != 200:
            return {"code": 500, "message": "Failed to update customer credits."}

        return {"code": 200, "message": f"Refund of ${amount} successfully processed for customer {customer_id}."}

    except Exception as e:
        return {"code": 500, "message": f"Error processing refund: {str(e)}"}

def process_picker_payment(picker_id, amount):
    """
    Add credits to picker account after order completion
    Always adds a flat fee of $2 regardless of order amount
    """
    try:
        # Validate inputs
        if not picker_id:
            return {"code": 400, "message": "Picker ID is required."}
        
        # Set flat fee of $2 for each delivery
        flat_fee = 2.0
            
        # 1. Get current picker credits
        picker_url = f"{PICKER_SERVICE_URL}/pickers/{picker_id}/credits"
        picker_response = requests.get(picker_url)

        if picker_response.status_code != 200:
            return {"code": 500, "message": "Failed to retrieve picker data."}

        picker_data = picker_response.json().get("data", {})
        picker_credits = float(picker_data.get("pickerCredits", 0))
        
        # 2. Add flat fee to picker account
        new_credits = picker_credits + flat_fee

        # 3. Update picker credits
        update_data = {
            "pickerCredits": new_credits
        }
        
        update_url = f"{PICKER_SERVICE_URL}/pickers/{picker_id}/credits"
        update_response = requests.put(update_url, json=update_data)

        if update_response.status_code != 200:
            return {"code": 500, "message": "Failed to update picker credits."}

        return {"code": 200, "message": f"Picker credited with flat fee of ${flat_fee}."}

    except Exception as e:
        return {"code": 500, "message": f"Error updating picker credits: {str(e)}"}

if __name__ == "__main__":
    app.run(port=5008, debug=True) 