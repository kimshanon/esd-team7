import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import ValidationError

# Add parent directory to path to resolve module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Pydantic model
from models.order_model import OrderModel, OrderItemModel

load_dotenv()  # Loads the .env file

# Initialize Firebase (if not already initialized)
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Set Firestore DB client.
db = firestore.client()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# TEST
@app.route('/test', methods=['GET'])
def test():
    return "Order MS is running"

# GET all orders (including their order items)
@app.route('/orders', methods=['GET'])
def get_orders():
    orders_ref = db.collection('orders')
    docs = orders_ref.stream()
    orders = []
    for doc in docs:
        order = doc.to_dict()
        order['id'] = doc.id
        # Get order items from subcollection "order_items"
        items = []
        for item_doc in doc.reference.collection('order_items').stream():
            item = item_doc.to_dict()
            item['id'] = item_doc.id
            items.append(item)
        order['order_items'] = items
        orders.append(order)
    return jsonify(orders), 200

# GET a specific order by order_id.
@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    doc_ref = db.collection('orders').document(order_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Order not found")
    order = doc.to_dict()
    order['id'] = doc.id
    items = []
    for item_doc in doc_ref.collection('order_items').stream():
        item = item_doc.to_dict()
        item['id'] = item_doc.id
        items.append(item)
    order['order_items'] = items
    return jsonify(order), 200

# POST create a new order (with multiple order items) using Pydantic validation.
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data:
        abort(400, description="Missing JSON body")
    
    # Validate incoming data with the OrderModel
    try:
        order_model = OrderModel(**data)
        
        # Build order document data for Firestore
        order_data = order_model.to_dict()
        
        # Create order document
        doc_ref = db.collection('orders').document()
        doc_ref.set(order_data)
        
        # Process and add each order item to the "order_items" subcollection
        for item in order_model.order_items:
            doc_ref.collection('order_items').add(item.to_dict())
        
        # Return the new order with its ID and items
        new_order = order_data
        new_order['id'] = doc_ref.id
        
        # Include serialized order items in the response
        new_order['order_items'] = [
            {**item.to_dict(), 'id': i} 
            for i, item in enumerate(order_model.order_items)
        ]
        
        return jsonify(new_order), 201
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PUT update an existing order.
@app.route('/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    if not data:
        abort(400, description="Missing JSON body")
    
    order_doc_ref = db.collection('orders').document(order_id)
    order_doc = order_doc_ref.get()
    if not order_doc.exists:
        abort(404, description="Order not found")
    
    # Get current data and merge with update
    current_data = order_doc.to_dict()
    
    # Get current order items
    current_items = []
    for item_doc in order_doc_ref.collection('order_items').stream():
        item = item_doc.to_dict()
        item['id'] = item_doc.id
        current_items.append(item)
    
    # Extract order items from the update if present
    update_items = data.pop('order_items', None)
    
    # Update the main order data
    if data:
        current_data.update(data)
    
    try:
        # Validate the order data (without items for now)
        temp_items = current_items if update_items is None else update_items
        order_model = OrderModel.from_dict(current_data, temp_items)
        
        # Update the order document with validated data
        order_doc_ref.update(order_model.to_dict())
        
        # If new order items were provided, handle them
        if update_items is not None:
            # Delete existing order items
            for item_doc in order_doc_ref.collection('order_items').stream():
                item_doc.reference.delete()
            
            # Add new order items
            for item_data in update_items:
                # Remove any id field as it's not part of the model
                if 'id' in item_data:
                    item_data.pop('id')
                
                # Validate item data
                item_model = OrderItemModel(**item_data)
                
                # Add to Firestore
                order_doc_ref.collection('order_items').add(item_model.to_dict())
        
        # Return the updated order with its items
        updated_order = order_model.to_dict()
        updated_order['id'] = order_id
        
        # Get the updated items from Firestore
        items = []
        for item_doc in order_doc_ref.collection('order_items').stream():
            item = item_doc.to_dict()
            item['id'] = item_doc.id
            items.append(item)
        updated_order['order_items'] = items
        
        return jsonify(updated_order), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PATCH to update order status
@app.route('/orders/<order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    data = request.get_json()
    if not data or 'order_status' not in data:
        abort(400, description="Request must include 'order_status'")
    
    order_doc_ref = db.collection('orders').document(order_id)
    order_doc = order_doc_ref.get()
    if not order_doc.exists:
        abort(404, description="Order not found")
    
    # Get current data and update status
    current_data = order_doc.to_dict()
    current_data['order_status'] = data['order_status']
    
    # Only update picker_id if it's included in the request
    if 'picker_id' in data:
        current_data['picker_id'] = data['picker_id']
    
    # If status is completed, add completion timestamp
    if data['order_status'] == 'completed':
        current_data['order_completed'] = datetime.now().isoformat()
    
    try:
        # Validate with the current items
        items = []
        for item_doc in order_doc_ref.collection('order_items').stream():
            item = item_doc.to_dict()
            items.append(item)
        
        # Create model instance to validate
        order_model = OrderModel.from_dict(current_data, items)
        
        # Update only the status field
        update_data = {'order_status': data['order_status']}
        if 'picker_id' in data:
            update_data['picker_id'] = data['picker_id']
            
        if data['order_status'] == 'completed':
            update_data['order_completed'] = current_data['order_completed']
        
        order_doc_ref.update(update_data)
        
        # Return success response
        return jsonify({
            'id': order_id,
            'order_status': data['order_status'],
            'message': f"Order status updated to {data['order_status']}"
        }), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# DELETE an order by order_id.
@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    order_doc_ref = db.collection('orders').document(order_id)
    order_doc = order_doc_ref.get()
    if not order_doc.exists:
        abort(404, description="Order not found")
    
    # Delete all order items in the subcollection first
    for item_doc in order_doc_ref.collection('order_items').stream():
        item_doc.reference.delete()
    
    # Then delete the main order document
    order_doc_ref.delete()
    
    return jsonify({
        "message": f"Order {order_id} and all its items deleted successfully"
    }), 200

# Optional: Add an endpoint to get all orders for a specific customer
@app.route('/customers/<customer_id>/orders', methods=['GET'])
def get_customer_orders(customer_id):
    orders_ref = db.collection('orders').where('customer_id', '==', customer_id)
    docs = orders_ref.stream()
    
    orders = []
    for doc in docs:
        order = doc.to_dict()
        order['id'] = doc.id
        
        # Get order items
        items = []
        for item_doc in doc.reference.collection('order_items').stream():
            item = item_doc.to_dict()
            item['id'] = item_doc.id
            items.append(item)
        
        order['order_items'] = items
        orders.append(order)
    
    return jsonify(orders), 200

# Optional: Add an endpoint to get all orders assigned to a specific picker
@app.route('/pickers/<picker_id>/orders', methods=['GET'])
def get_picker_orders(picker_id):
    orders_ref = db.collection('orders').where('picker_id', '==', picker_id)
    docs = orders_ref.stream()
    
    orders = []
    for doc in docs:
        order = doc.to_dict()
        order['id'] = doc.id
        
        # Get order items
        items = []
        for item_doc in doc.reference.collection('order_items').stream():
            item = item_doc.to_dict()
            item['id'] = item_doc.id
            items.append(item)
        
        order['order_items'] = items
        orders.append(order)
    
    return jsonify(orders), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003, threaded=True)