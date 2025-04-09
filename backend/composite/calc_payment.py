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
PICKER_SERVICE_URL = "http://picker-service:5001"

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
        # Step 1: Add credits to customer account using the PATCH endpoint
        customer_response = requests.patch(
            f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/credits",
            json={"amount": amount_value}
        )
        
        if customer_response.status_code != 200:
            return jsonify({
                "error": "Failed to add credits to customer account",
                "details": customer_response.json()
            }), customer_response.status_code
        
        # Step 2: Create payment transaction log
        payment_data = {
            "log_id": f"topup_{customer_id}",
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
            # If payment logging fails, consider rolling back the credit addition
            # or just log the error and continue since the credits were already added
            print(f"Warning: Failed to log payment transaction: {str(payment_error)}")
            return jsonify({
                "message": "Credits added successfully but transaction logging failed",
                "customer_update": customer_response.json()
            }), 201
        
        if payment_response.status_code != 201:
            # Credits were added but transaction logging failed
            print(f"Warning: Payment logging failed with status {payment_response.status_code}")
            return jsonify({
                "message": "Credits added successfully but transaction logging failed",
                "customer_update": customer_response.json()
            }), 201
        
        # Return combined response
        return jsonify({
            "message": "Credits added successfully",
            "customer_update": customer_response.json(),
            "payment_transaction": payment_response.json()
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

@app.route("/customer/pay", methods=['POST'])
def customer_pay_picker():
    """
    Handle payment from a customer.
    
    This endpoint:
    1. Checks if the customer has enough credits
    2. Deducts credits from the customer
    3. Logs the payment transaction
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["customer_id", "picker_id", "amount", "order_id"]
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields", 
                "required": required_fields
            }), 400
        
        customer_id = data["customer_id"]
        picker_id = data["picker_id"]  # We still need this for logging purposes
        order_id = data["order_id"]
        
        # Validate amount is positive
        try:
            amount = float(data["amount"])
        except (ValueError, TypeError):
            return jsonify({"error": "Amount must be a valid number"}), 400
            
        # Step 1: Check if customer has enough credits
        try:
            customer_response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/credits")
            
            if customer_response.status_code != 200:
                return jsonify({
                    "error": "Failed to retrieve customer credits",
                    "details": customer_response.json()
                }), customer_response.status_code
            
            customer_credits = customer_response.json().get("customer_credits", 0)
            
            if customer_credits < amount:
                return jsonify({
                    "error": "Insufficient credits",
                    "customer_credits": customer_credits,
                    "required_amount": amount
                }), 400
                
        except Exception as e:
            return jsonify({
                "error": f"Error checking customer credits: {str(e)}"
            }), 500
        
        # Step 2: Deduct credits from customer
        try:
            deduct_response = requests.patch(
                f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/credits",
                json={"amount": -amount}  # Negative amount for deduction
            )
            
            if deduct_response.status_code != 200:
                return jsonify({
                    "error": "Failed to deduct credits from customer",
                    "details": deduct_response.json()
                }), deduct_response.status_code
                
            # Get updated customer credits info
            customer_update = deduct_response.json()
                
        except Exception as e:
            return jsonify({
                "error": f"Error deducting customer credits: {str(e)}"
            }), 500
        
        # Step 3: Log the payment transaction
        try:
            payment_data = {
                "log_id": f"payment_{customer_id}",
                "order_id": order_id,
                "customer_id": customer_id,
                "event_type": "Payment",
                "event_details": f"Payment from customer {customer_id} for order {order_id} (picker: {picker_id})",
                "payment_amount": -amount,
                "payment_status": "Completed",
                "timestamp": datetime.now().isoformat()
            }
            
            payment_response = requests.post(
                f"{PAYMENT_SERVICE_URL}/payment",
                json=payment_data
            )
            
            if payment_response.status_code != 201:
                # Note: We don't rollback the transaction here as the money was deducted
                # We just log the failure to record the transaction
                print(f"Warning: Failed to log payment transaction: {payment_response.text}")
                
        except Exception as e:
            # Transaction was successful but logging failed
            print(f"Warning: Error logging payment transaction: {str(e)}")
        
        # Return success response with transaction details
        return jsonify({
            "status": "success",
            "message": "Payment processed successfully",
            "transaction": {
                "customer_id": customer_id,
                "picker_id": picker_id,  # Still included for reference
                "order_id": order_id,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            },
            "customer_update": customer_update
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error processing payment: {str(e)}"}), 500

@app.route("/customer/refund", methods=['POST'])
def customer_refund():
    """
    Handle refund to a customer for a completed order.
    
    This endpoint:
    1. Calculates the total amount in the completed order
    2. Adds credits back to the customer
    3. Logs the refund transaction
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["customer_id", "order_id", "refund_reason"]
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields", 
                "required": required_fields
            }), 400
        
        customer_id = data["customer_id"]
        order_id = data["order_id"]
        refund_reason = data["refund_reason"]
        refund_details = data.get("refund_details", "")
        
        # Step 1: Get the order details to calculate refund amount
        try:
            order_response = requests.get(f"http://order-service:5003/orders/{order_id}")
            
            if order_response.status_code != 200:
                return jsonify({
                    "error": "Failed to retrieve order details",
                    "details": order_response.text
                }), order_response.status_code
            
            order_data = order_response.json()
            
            # Verify the order belongs to this customer
            if order_data.get("customer_id") != customer_id:
                return jsonify({
                    "error": "Order does not belong to this customer"
                }), 403
                
            # Calculate total refund amount from order items
            order_items = order_data.get("order_items", [])
            refund_amount = sum(item["order_price"] * item["order_quantity"] for item in order_items)
            
            # Verify it's valid to refund (completed order)
            if order_data.get("order_status") != "completed":
                return jsonify({
                    "error": "Only completed orders can be refunded",
                    "current_status": order_data.get("order_status")
                }), 400
                
        except Exception as e:
            return jsonify({
                "error": f"Error retrieving order details: {str(e)}"
            }), 500
        
        # Step 2: Add refund amount to customer's credits
        try:
            # Using positive amount for credit addition
            credit_response = requests.patch(
                f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/credits",
                json={"amount": refund_amount}
            )
            
            if credit_response.status_code != 200:
                return jsonify({
                    "error": "Failed to add refund credits to customer",
                    "details": credit_response.text
                }), credit_response.status_code
                
            # Get updated customer credits info
            customer_update = credit_response.json()
                
        except Exception as e:
            return jsonify({
                "error": f"Error adding refund credits: {str(e)}"
            }), 500
        
        # Step 3: Log the refund transaction
        try:
            payment_data = {
                "log_id": f"refund_{order_id}",
                "order_id": order_id,
                "customer_id": customer_id,
                "event_type": "Refund",
                "event_details": f"Refund for order {order_id}. Reason: {refund_reason}. {refund_details}",
                "payment_amount": refund_amount,
                "payment_status": "Completed",
                "timestamp": datetime.now().isoformat()
            }
            
            payment_response = requests.post(
                f"{PAYMENT_SERVICE_URL}/payment",
                json=payment_data
            )
            
            if payment_response.status_code != 201:
                # Note: We don't rollback even if logging fails
                print(f"Warning: Failed to log refund transaction: {payment_response.text}")
                
        except Exception as e:
            # Refund was successful but logging failed
            print(f"Warning: Error logging refund transaction: {str(e)}")
        
        # Return success response with transaction details
        return jsonify({
            "status": "success",
            "message": "Refund processed successfully",
            "transaction": {
                "customer_id": customer_id,
                "order_id": order_id,
                "refund_amount": refund_amount,
                "reason": refund_reason,
                "timestamp": datetime.now().isoformat()
            },
            "customer_update": customer_update
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error processing refund: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009, threaded=True)
