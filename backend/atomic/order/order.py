#order.py
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

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
    customer_id = data.get("customer_id")
    stall_id = data.get("stall_id")
    location = data.get("location")

    # Optional fields
    credit = data.get("credit", 0.0)  # Default credit used is 0
    picker_id = None  # Initially, no picker is assigned

    if not customer_id or not stall_id or not location:
        return jsonify({"code": 400, "message": "customer_id, stall_id and location are required"}), 400

    order_id = str(uuid.uuid4())  # Generate a unique order ID
    order_data = {
        "customer_id": customer_id,
        "picker_id": picker_id,  
        # "order_id": order_id,
        "stall_id": stall_id,
        # "additionalRequest": additional_request,
        # "timestamp": datetime.utcnow().isoformat(),
        "location": location,
        "credit": credit,
        "order_status": "Pending"
    }

    db.collection("orders").document(order_id).set(order_data)

    return jsonify({"code": 201, "message": "Order created successfully", "order_id": order_id}), 201

# ✅ Get all orders of a specifc picker 
@app.route("/orders", methods=['GET'])
def get_all_orders():
    picker_id = request.args.get('pickerID')  # Get pickerID from query parameters

    orders_ref = db.collection('orders')
    
    if picker_id:
        # If pickerID is provided, filter orders by pickerID
        orders_ref = orders_ref.where('pickerID', '==', picker_id)
    
    docs = orders_ref.stream()
    
    orders = [{**doc.to_dict(), "orderID": doc.id} for doc in docs]
    
    if orders:
        return jsonify({"code": 200, "data": orders}), 200
    else:
        return jsonify({"code": 404, "message": "No orders found."}), 404

# ✅ Get a specific order
@app.route("/orders/<orderID>", methods=['GET'])
def get_order(orderID):
    order_ref = db.collection('orders').document(orderID)
    order = order_ref.get()
    
    if order.exists:
        return jsonify({"code": 200, "data": order.to_dict()}), 200
    else:
        return jsonify({"code": 404, "message": "Order not found."}), 404

# ✅ Get a specific picker
@app.route("/pickers/<pickerID>", methods=['GET'])
def get_picker(pickerID):
    picker_ref = db.collection('pickers').document(pickerID)
    picker = picker_ref.get()
    
    if picker.exists:
        return jsonify({"code": 200, "data": picker.to_dict()}), 200
    else:
        return jsonify({"code": 404, "message": f"Picker {pickerID} not found."}), 404
    

# ✅ Update Order Location
@app.route("/orders/<orderID>/location", methods=['PATCH'])
def update_location(orderID):
    data = request.get_json()
    new_location = data.get("location")

    if not new_location:
        return jsonify({"code": 400, "message": "New location is required"}), 400

    order_ref = db.collection("orders").document(orderID)
    order = order_ref.get()

    if not order.exists:
        return jsonify({"code": 404, "message": "Order not found"}), 404

    order_ref.update({"location": new_location})
    
    return jsonify({"code": 200, "message": f"Order {orderID} location updated successfully"}), 200


# ✅ Update an order status to "Cancelled"
@app.route("/orders/<orderID>/cancel", methods=['PATCH'])
def cancel_order(orderID):
    order_ref = db.collection("orders").document(orderID)
    order = order_ref.get()

    if not order.exists:
        return jsonify({"code": 404, "message": "Order not found"}), 404

    order_ref.update({"status": "Cancelled"})
    
    return jsonify({"code": 200, "message": f"Order {orderID} has been cancelled successfully"}), 200



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
    app.run(port=5003, debug=True)