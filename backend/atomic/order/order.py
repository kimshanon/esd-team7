import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)

# Allow all origins (For development only, restrict in production)
CORS(app, resources={r"/*": {"origins": "*"}})

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
    customer_id = data.get("customerID")
    stall_id = data.get("stallID")
    location = data.get("location")
    payment = data.get("payment")

    # Optional fields
    additional_request = data.get("additionalRequest", "")
    credit = data.get("credit", 0.0)  # Default credit used is 0
    picker_id = None  # Initially, no picker is assigned
    order_status = "Active"  # Default order status

    if not customer_id or not stall_id or not location or not payment:
        return jsonify({"code": 400, "message": "customerID, stallID, location, and payment are required"}), 400

    order_id = str(uuid.uuid4())  # Generate a unique order ID

    # Construct the order data (no 'title', 'position' replaced with 'coordinates')
    order_data = {
        "customerID": customer_id,
        "pickerID": picker_id,  
        "stallID": stall_id,
        "additionalRequest": additional_request,
        "timestamp": datetime.utcnow().isoformat(),
        "location": location,
        "credit": credit,
        "payment": payment,
        "status": "Pending"
    }

    # Save to Firestore
    db.collection("orders").document(order_id).set(order_data)

    return jsonify({"code": 201, "message": "Order created successfully", "orderID": order_id}), 201

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


# ✅ Start the Flask app
if __name__ == "__main__":
    app.run(port=5001, debug=True)