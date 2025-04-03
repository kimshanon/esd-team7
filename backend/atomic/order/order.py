import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
import uuid
from datetime import datetime, timezone 

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("../../firebase-adminsdk.json")  # Replace with your Firebase JSON key file
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
    
    order_id = str(uuid.uuid4())
    order_data = {
        "customerID": customer_id,
        "pickerID": None,  
        "stallID": stall_id,
        "additionalRequest": additional_request,
        "timestamp": datetime.utcnow().isoformat(),
        "location": location,
        "credit": credit,
        "payment": payment,
        "status": "Pending",
        # Initialize change tracking fields
        "location_change_count": 0,
        "location_history": [{
            **location,
            "changed_at": datetime.utcnow().isoformat()
        }]
    }

    db.collection("orders").document(order_id).set(order_data)
    return jsonify({"code": 201, "message": "Order created", "orderID": order_id}), 201

@app.route("/orders/<orderID>/location", methods=['PATCH'])
def update_location(orderID):
    data = request.get_json()
    new_location = data.get("location")

    required_fields = ["title", "position", "address", "postal"]
    if not new_location or not all(key in new_location for key in required_fields):
        return jsonify({"code": 400, "message": "Invalid location format"}), 400

    position = new_location.get("position")
    if not isinstance(position, dict) or "lat" not in position or "lng" not in position:
        return jsonify({"code": 400, "message": "Invalid position"}), 400

    order_ref = db.collection("orders").document(orderID)
    order = order_ref.get()

    if not order.exists:
        return jsonify({"code": 404, "message": "Order not found"}), 404

    order_data = order.to_dict()

    if order_data.get("order_status") == "completed":
        return jsonify({"code": 400, "message": "Cannot update location for completed orders"}), 400

    location_change_count = order_data.get("location_change_count", 0)
    if location_change_count >= 1:
        return jsonify({"code": 400, "message": "Location can only be updated once"}), 400

    order_ref.update({
        "order_location": new_location.get("title"),  
        "location_change_count": location_change_count + 1,
        "location_history": firestore.ArrayUnion([{
            "location": new_location,
            "changed_at": datetime.now(timezone.utc).isoformat()
        }])
    })

    # Return success response
    updated_order = order_ref.get().to_dict()
    return jsonify({
        "code": 200,
        "message": "Location updated successfully",
        "data": updated_order
    }), 200


# ✅ Get all orders of a speicifc picker 
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
