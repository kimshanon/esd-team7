from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import ValidationError
from models.picker_model import PickerModel

# Add parent directory to path to resolve module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()  # Loads the .env file

# Initialize Firebase (if not already initialized)
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Set Firestore DB client.
db = firestore.client()

app = Flask(__name__)
CORS(app)

# GET all pickers.
@app.route('/pickers', methods=['GET'])
def get_pickers():
    pickers_ref = db.collection('pickers')
    docs = pickers_ref.stream()
    pickers = []
    for doc in docs:
        picker = doc.to_dict()
        picker['id'] = doc.id
        pickers.append(picker)
    return jsonify(pickers), 200

# GET all Available pickers.
@app.route('/pickers/available', methods=['GET'])
def get_pickers():
    pickers_ref = db.collection('pickers').where("is_available", "==", True)
    docs = pickers_ref.stream()
    pickers = []
    for doc in docs:
        picker = doc.to_dict()
        picker['id'] = doc.id
        pickers.append(picker)
    return jsonify(pickers), 200

# GET a specific picker by document ID.
@app.route('/pickers/<picker_id>', methods=['GET'])
def get_picker(picker_id):
    doc_ref = db.collection('pickers').document(picker_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Picker not found")
    picker = doc.to_dict()
    picker['id'] = doc.id
    return jsonify(picker), 200

# POST create a new picker.
@app.route('/pickers', methods=['POST'])
def create_picker():
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    try:
        # Validate picker data using Pydantic model
        picker_model = PickerModel(**data)
        
        # Add a new document to the "pickers" collection.
        doc_ref = db.collection('pickers').document()
        doc_ref.set(picker_model.to_dict())
        
        # Return the new picker with its ID
        new_picker = picker_model.to_dict()
        new_picker['id'] = doc_ref.id
        return jsonify(new_picker), 201
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PUT update an existing picker.
@app.route('/pickers/<picker_id>', methods=['PUT'])
def update_picker(picker_id):
    doc_ref = db.collection('pickers').document(picker_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Picker not found")
    
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    try:
        # Get current data and update with new data
        current_data = doc.to_dict()
        current_data.update(data)
        
        # Validate the updated data
        updated_picker = PickerModel(**current_data)
        
        # Update the document with validated data
        doc_ref.update(updated_picker.to_dict())
        
        # Return updated picker with ID
        response_data = updated_picker.to_dict()
        response_data['id'] = doc.id
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PATCH to update picker availability
@app.route('/pickers/<picker_id>/availability', methods=['PATCH'])
def update_availability(picker_id):
    doc_ref = db.collection('pickers').document(picker_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Picker not found")
    
    data = request.get_json()
    if not isinstance(data, dict) or 'is_available' not in data:
        abort(400, description="Request must include 'is_available' field")
    
    # Get the current picker data
    current_data = doc.to_dict()
    current_data.update({'is_available': data['is_available']})
    
    try:
        # Validate the updated data
        updated_picker = PickerModel(**current_data)
        
        # Update just the availability field
        doc_ref.update({'is_available': data['is_available']})
        
        # Return updated picker with ID
        response_data = updated_picker.to_dict()
        response_data['id'] = doc.id
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# DELETE a picker by document ID.
@app.route('/pickers/<picker_id>', methods=['DELETE'])
def delete_picker(picker_id):
    doc_ref = db.collection('pickers').document(picker_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Picker not found")
    doc_ref.delete()
    return jsonify({"message": f"Picker {picker_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)