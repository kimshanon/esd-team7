from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import ValidationError
from models.stall_model import StallModel, MenuItemModel

load_dotenv()  # Loads the .env file

# Initialize Firebase (if not already initialized)
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Set the Firestore DB client.
db = firestore.client()

app = Flask(__name__)
CORS(app)

# GET all food stalls with their menus.
@app.route('/stalls', methods=['GET'])
def get_stalls():
    stalls_ref = db.collection('stalls')
    docs = stalls_ref.stream()
    stalls = []
    for doc in docs:
        stall_data = doc.to_dict()
        stall_data['id'] = doc.id
        # Retrieve menu items as documents in the subcollection "menu".
        menu_docs = doc.reference.collection('menu').stream()
        menu_items = []
        for menu_doc in menu_docs:
            menu_item = menu_doc.to_dict()
            menu_item['id'] = menu_doc.id
            menu_items.append(menu_item)
        stall_data['menu'] = menu_items
        stalls.append(stall_data)
    return jsonify(stalls), 200

# GET a specific food stall by stall_id.
@app.route('/stalls/<stall_id>', methods=['GET'])
def get_stall(stall_id):
    doc_ref = db.collection('stalls').document(stall_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Food stall not found")
    stall_data = doc.to_dict()
    stall_data['id'] = doc.id
    # Get the stall's menu (from the "menu" subcollection)
    menu_docs = doc_ref.collection('menu').stream()
    menu_items = []
    for menu_doc in menu_docs:
        menu_item = menu_doc.to_dict()
        menu_item['id'] = menu_doc.id
        menu_items.append(menu_item)
    stall_data['menu'] = menu_items
    return jsonify(stall_data), 200

# POST to create a new food stall.
@app.route('/stalls', methods=['POST'])
def create_stall():
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    try:
        # Validate stall data using Pydantic model (excluding menu items)
        menu_items = data.pop('menu', [])
        stall_model = StallModel(**data)
        
        # Add the new stall document to Firestore
        doc_ref = db.collection('stalls').document()
        doc_ref.set(stall_model.to_dict())
        
        # Return the new stall with its ID
        new_stall = stall_model.to_dict()
        new_stall['id'] = doc_ref.id
        new_stall['menu'] = []
        
        # Add menu items if provided
        if menu_items:
            return add_menu_items(doc_ref.id, menu_items)
        
        return jsonify(new_stall), 201
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PUT to update an existing food stall.
@app.route('/stalls/<stall_id>', methods=['PUT'])
def update_stall(stall_id):
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    doc_ref = db.collection('stalls').document(stall_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        abort(404, description="Food stall not found")
    
    try:
        # If menu is included, handle it separately
        menu_items = data.pop('menu', None)
        
        # Get current data and update with new data
        current_data = doc.to_dict()
        current_data.update(data)
        
        # Validate the updated data
        stall_model = StallModel.from_dict(current_data)
        
        # Update the document with validated data
        doc_ref.update(stall_model.to_dict())
        
        # Re-read the updated document
        updated_doc = doc_ref.get()
        stall_data = updated_doc.to_dict()
        stall_data['id'] = updated_doc.id
        
        # Also fetch updated menu items.
        menu_docs = doc_ref.collection('menu').stream()
        menu_list = []
        for menu_doc in menu_docs:
            item = menu_doc.to_dict()
            item['id'] = menu_doc.id
            menu_list.append(item)
        stall_data['menu'] = menu_list
        
        # If menu items were provided, update them
        if menu_items is not None:
            # Delete existing menu items
            for menu_doc in doc_ref.collection('menu').stream():
                menu_doc.reference.delete()
            
            # Add new menu items
            if menu_items:
                add_menu_items(stall_id, menu_items)
                stall_data['menu'] = menu_items
        
        return jsonify(stall_data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# DELETE a food stall (and its associated menu items).
@app.route('/stalls/<stall_id>', methods=['DELETE'])
def delete_stall(stall_id):
    doc_ref = db.collection('stalls').document(stall_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Food stall not found")
    # Delete all menu items in the "menu" subcollection.
    menu_collection = doc_ref.collection('menu')
    for menu_doc in menu_collection.stream():
        menu_doc.reference.delete()
    # Delete the stall document.
    doc_ref.delete()
    return jsonify({"message": f"Food stall {stall_id} deleted"}), 200

# GET all food items for a specific stall (its menu).
@app.route('/stalls/<stall_id>/menu', methods=['GET'])
def get_menu(stall_id):
    doc_ref = db.collection('stalls').document(stall_id)
    if not doc_ref.get().exists:
        abort(404, description="Food stall not found")
    menu_docs = doc_ref.collection('menu').stream()
    menu_items = []
    for menu_doc in menu_docs:
        item = menu_doc.to_dict()
        item['id'] = menu_doc.id
        menu_items.append(item)
    return jsonify(menu_items), 200

# Helper function to add menu items
def add_menu_items(stall_id, items):
    doc_ref = db.collection('stalls').document(stall_id)
    if not doc_ref.get().exists:
        abort(404, description="Food stall not found")
    
    new_items = []
    for item in items:
        try:
            # Validate menu item using Pydantic model
            menu_item = MenuItemModel(**item)
            item_dict = menu_item.to_dict()
            
            # Add the food item to the "menu" subcollection
            menu_doc_ref = doc_ref.collection('menu').document()
            menu_doc_ref.set(item_dict)
            
            # Add ID to the item
            item_dict['id'] = menu_doc_ref.id
            new_items.append(item_dict)
            
        except ValidationError as e:
            return jsonify({"error": f"Invalid menu item: {str(e)}"}), 400
    
    # Get updated stall data
    stall_doc = doc_ref.get()
    stall_data = stall_doc.to_dict()
    stall_data['id'] = stall_doc.id
    stall_data['menu'] = new_items
    
    return jsonify(stall_data), 201

# POST to add multiple food items to a stall's menu.
@app.route('/stalls/<stall_id>/menu', methods=['POST'])
def add_multiple_menu_items(stall_id):
    items = request.get_json()
    if not items or not isinstance(items, list):
        abort(400, description="Expected a JSON list of food items")
    
    return add_menu_items(stall_id, items)

# PUT to update an existing food item for a stall.
@app.route('/stalls/<stall_id>/menu/<food_id>', methods=['PUT'])
def update_menu_item(stall_id, food_id):
    doc_ref = db.collection('stalls').document(stall_id)
    menu_doc_ref = doc_ref.collection('menu').document(food_id)
    
    if not menu_doc_ref.get().exists:
        abort(404, description="Menu item not found for this stall")
    
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    try:
        # Get current data and update with new data
        current_data = menu_doc_ref.get().to_dict()
        current_data.update(data)
        
        # Validate the updated data
        menu_item = MenuItemModel(**current_data)
        
        # Update the document with validated data
        menu_doc_ref.update(menu_item.to_dict())
        
        # Return updated menu item with ID
        updated_data = menu_item.to_dict()
        updated_data['id'] = food_id
        return jsonify(updated_data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# DELETE a food item from a stall's menu.
@app.route('/stalls/<stall_id>/menu/<food_id>', methods=['DELETE'])
def delete_menu_item(stall_id, food_id):
    doc_ref = db.collection('stalls').document(stall_id)
    menu_doc_ref = doc_ref.collection('menu').document(food_id)
    if not menu_doc_ref.get().exists:
        abort(404, description="Menu item not found for this stall")
    menu_doc_ref.delete()
    return jsonify({"message": f"Menu item {food_id} deleted from stall {stall_id}"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, threaded=True)