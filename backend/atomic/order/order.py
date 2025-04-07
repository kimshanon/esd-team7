#order.py
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)

# Allow all origins (For development only, restrict in production)
CORS(app, resources={r"/*": {"origins": "*"}})

PAYMENT_SERVICE_URL = "http://localhost:5007/payment"

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("./firebase-adminsdk.json")  # Replace with your Firebase JSON key file
    firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

@app.route("/")
def home():
    return "Order & Picker Microservice (Using Firebase Firestore)"

# ✅ Create a new order
@app.route("/orders", methods=['POST'])
def create_order():
    data = request.get_json()
    
    # Required fields
    item_id = data.get("item_id")
    item_name = data.get("item_name")
    customer_id = data.get("customer_id", "QbJTSeLiZsbL509BxpY8")  # Default customer ID
    stall_id = data.get("stall_id")
    stall_name = data.get("stall_name")
    location = data.get("location")
    credit = data.get("credit", 0.0)  # Default credit used is 0
    ordered_at = datetime.utcnow()

    print(f"Location received: {location}")
    
    # Set default values
    picker_id = ""  # Initially empty string
    order_status = "Active"  # Default status
    
    # Validate required fields
    if not customer_id or not stall_id or not location:
        return jsonify({"code": 400, "message": "customer_id, stall_id, and location are required"}), 400
    
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Construct the order data with properly formatted location
    order_data = {
        "item_id" : item_id,
        "item_name" : item_name,
        "customer_id": customer_id,
        "picker_id": picker_id,
        "stall_id": stall_id,
        "stall_name" : stall_name,
        "ordered_at" : ordered_at,
        "location": {
            "address": location.get("title", ""),  # Use title as address
            "coordinates": {
                "lat": location.get("coordinates", {}).get("lat", 0),
                "lng": location.get("coordinates", {}).get("lng", 0)
            },
            "postal": location.get("postal", "")
        },
        "credit": float(credit),  # Ensure credit is stored as a number
        "order_status": order_status
    }
    
    # Save to Firestore
    db.collection("orders").document(order_id).set(order_data)
    current_timestamp = current_timestamp = datetime.utcnow().isoformat()

    payment_data = {
        "log_id": str(uuid.uuid4()),  # Example log_id
        "customer_id" : customer_id,
        "order_id": order_id,
        "payment_amount" : credit,
        "event_type": "Payment",
        "event_details": f"Payment for order {order_id}",
        "payment_status": "Pending",  # Default status
        "timestamp": current_timestamp
    }

    print("Sending payment data:", payment_data)  # Log the payment data for debugging

    try:
        payment_response = requests.post(PAYMENT_SERVICE_URL, json=payment_data)
        print(f"Payment response status: {payment_response.status_code}")
        print(f"Payment response text: {payment_response.text}") 
        if payment_response.status_code == 201:
            payment_id = payment_response.json().get('data').get('payment_id')
            return jsonify({
                "code": 201,
                "message": "Order and payment created successfully",
                "order_id": order_id,
                "payment_id": payment_id
            }), 201
        else:
            return jsonify({
                "code": 500,
                "message": "Failed to create payment in Payment Microservice"
            }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({
            "code": 500,
            "message": f"Error calling Payment Microservice: {str(e)}"
        }), 500

# ✅ Get all orders of a speicifc picker 
@app.route("/orders", methods=['GET'])
def get_all_orders():
    customer_id = request.args.get('customer_id', default='QbJTSeLiZsbL509BxpY8')  # Default customer ID

    orders_ref = db.collection('orders').where('customer_id', '==', customer_id)
    docs = orders_ref.stream()
    orders = [{**doc.to_dict(), "order_id": doc.id} for doc in docs]

    if not orders:
        return jsonify({"code": 404, "message": "No orders found for the customer."}), 404

    return jsonify({"code": 200, "data": orders}), 200

# ✅ Get a specific order
@app.route("/orders/<order_id>", methods=['GET'])
def get_order(order_id):
    order_ref = db.collection('orders').document(order_id)
    order = order_ref.get()
    
    if order.exists:
        return jsonify({"code": 200, "data": order.to_dict()}), 200
    else:
        return jsonify({"code": 404, "message": "Order not found."}), 404

# ✅ Get a specific picker
# @app.route("/pickers/<picker_id>", methods=['GET'])
# def get_picker(picker_id):
#     picker_ref = db.collection('pickers').document(picker_id)
#     picker = picker_ref.get()
    
#     if picker.exists:
#         return jsonify({"code": 200, "data": picker.to_dict()}), 200
#     else:
#         return jsonify({"code": 404, "message": f"Picker {picker_id} not found."}), 404

# ✅ Update Order Location
    
@app.route("/orders/<order_id>/location", methods=['PATCH'])
def update_location(order_id):
    data = request.get_json()
    new_location = data.get("location")

    if not new_location:
        return jsonify({"code": 400, "message": "New location is required"}), 400

    # Ensure new_location follows the correct format
    required_fields = ["address", "coordinates", "postal"]
    if not all(field in new_location for field in required_fields):
        return jsonify({"code": 400, "message": "Location must include address, coordinates, and postal code"}), 400
    
    if "coordinates" in new_location:
        coordinates = new_location["coordinates"]
        if "lat" not in coordinates or "lng" not in coordinates:
            return jsonify({"code": 400, "message": "Coordinates must include both lat and lng"}), 400

    order_ref = db.collection("orders").document(order_id)
    order = order_ref.get()

    if not order.exists:
        return jsonify({"code": 404, "message": "Order not found"}), 404

    order_ref.update({"location": new_location})
    
    return jsonify({"code": 200, "message": f"Order {orderID} location updated successfully"}), 200


# #assign a picker
# @app.route("/orders/<orderID>/assign", methods=['PATCH'])
# def assign_picker(orderID):
#     data = request.get_json()
#     picker_id = data.get("pickerID")


#     if not picker_id:
#         return jsonify({"code": 400, "message": "pickerID is required"}), 400

#     order_ref = db.collection("orders").document(orderID)
#     order = order_ref.get()

#     if not order.exists:
#         return jsonify({"code": 404, "message": "Order not found"}), 404

#     order_ref.update({"pickerID": picker_id, "status": "Assigned"})
    
#     return jsonify({"code": 200, "message": f"Picker {picker_id} assigned to order {orderID}"}), 200

# Update order status
@app.route("/orders/<order_id>/status", methods=['PATCH'])
def update_order_status(order_id):
    data = request.get_json()
    if not data or 'order_status' not in data:
        return jsonify({"code": 400, "message": "Missing 'order_status' field"}), 400

    valid_statuses = ["Active", "Completed", "Cancelled"]
    if data['order_status'] not in valid_statuses:
        return jsonify({"code": 400, "message": "Invalid status"}), 400

    order_ref = db.collection('orders').document(order_id)
    order_ref.update({'order_status': data['order_status']})
    return jsonify({"code": 200, "message": "Order status updated"}), 200


# ✅ Start the Flask app
if __name__ == "__main__":
    app.run(port=5001, debug=True)