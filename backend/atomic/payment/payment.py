import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("../../firebase-adminsdk.json")  # Replace with your Firebase JSON key file
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

ORDER_SERVICE_URL = "http://localhost:5003"
CUSTOMER_SERVICE_URL = "https://personal-dcwqxa6n.outsystemscloud.com"

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

# Create a new payment
@app.route("/payment", methods=['POST'])
def create_payment():
    data = request.get_json()
    required_fields = ["log_id", "order_id", "customer_id", "event_type", "event_details", "payment_amount", "payment_status", "timestamp"]
    
    # Validate required fields
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400
    
    try:
        # Create payment entry
        payment_ref = db.collection('payments').document()
        payment_id = payment_ref.id
        data["payment_id"] = payment_id

        # Update customer credits and handle order cancellation if necessary
        credit_update_response = update_customer_credits(data["customer_id"], data["payment_amount"], data["order_id"])

        # If credit update fails, return the error response
        if credit_update_response["code"] != 200:
            return jsonify(credit_update_response), credit_update_response["code"]

        # Save payment only if credits update was successful
        data["payment_status"] = "Paid"
        payment_ref.set(data)
        
        return jsonify({"code": 201, "data": data}), 201
    except Exception as e:
        # Log the error and return a failure response
        return jsonify({"code": 500, "message": f"Failed to create payment due to error: {str(e)}"}), 500


def update_customer_credits(customer_id, payment_amount, order_id):
    update_url = f"{CUSTOMER_SERVICE_URL}/SMUlivery/rest/CustomerAPI/customers/{customer_id}/UpdateCustomerCredits"
    print(f"\n=== Starting credit update for customer {customer_id} ===")
    
    try:
        # Fetch current customer data
        customer_url = f"{CUSTOMER_SERVICE_URL}/SMUlivery/rest/CustomerAPI/customers/id/{customer_id}"
        
        customer_response = requests.get(customer_url)

        if customer_response.status_code != 200:
            return {"code": 500, "message": "Failed to retrieve customer data."}

        # Parse response
        response_data = customer_response.json()
        result = response_data.get("Result", {})
        
        if not result.get("Success", False):
            return {"code": 500, "message": f"Error: {result.get('ErrorMessage', 'Unknown error')}"}

        customer_data = response_data.get("Customer", {})

        # Validate credits
        customer_credits = customer_data.get("customerCredits")
        if customer_credits is None:
            return {"code": 400, "message": "Customer credits data is missing."}
        
        # Check credit balance
        if customer_credits < payment_amount:
            cancel_response = requests.patch(
                f"{ORDER_SERVICE_URL}/orders/{order_id}/cancel", 
                json={"status": "Cancelled"}
            )
            return {"code": 400, "message": "Insufficient credits. Order cancelled."}

        # Calculate new credits
        new_credits = customer_credits - payment_amount

  
        # Send request
        update_data = {
            "customer": {
            "customerId": int(customer_id),
            "customerCredits": "{:.2f}".format(new_credits),
            }
        }

        headers = {"Content-Type": "application/json"}

        print("Sending PUT request with data:", json.dumps(update_data, indent=2))

        update_response = requests.put(update_url, json=update_data, headers=headers)

        print(f"Update Response Status: {update_response.status_code}")
        print(f"Update Response Text: {update_response.text}")

        if update_response.status_code != 200:
            return {"code": 500, "message": "Failed to update customer credits."}

        return {"code": 200, "message": "Customer credits updated successfully."}

    except Exception as e:
        return {"code": 500, "message": f"Error updating credits: {str(e)}"}



# Delete a payment
@app.route("/payments/<paymentID>", methods=['DELETE'])
def delete_payment(paymentID):
    payment_ref = db.collection('payments').document(paymentID)
    payment = payment_ref.get()

    if not payment.exists:
        return jsonify({"code": 404, "message": f"Payment {paymentID} not found."}), 404

    payment_ref.delete()
    return jsonify({"code": 200, "message": f"Payment {paymentID} has been deleted."}), 200


if __name__ == '__main__':
    app.run(port=5007, debug=True)