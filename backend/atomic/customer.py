from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import ValidationError
from models.customer_model import CustomerModel

load_dotenv()  # Loads the .env file

# Initialize firebase
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Set DB
db = firestore.client()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# GET all customers.
@app.route('/customers', methods=['GET'])
def get_customers():
    customers_ref = db.collection('customers')
    docs = customers_ref.stream()
    customers = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        customers.append(data)
    return jsonify(customers), 200

# GET a specific customer by document ID.
@app.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    doc_ref = db.collection('customers').document(customer_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Customer not found")
    customer = doc.to_dict()
    customer['id'] = doc.id
    return jsonify(customer), 200

# POST a new customer.
@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")
    
    try:
        # Validate data using Pydantic model
        customer_data = CustomerModel(**data)
        
        # Add a new document; Firestore will generate a unique document ID.
        doc_ref = db.collection('customers').document()
        doc_ref.set(customer_data.to_dict())
        
        # Return the new customer with its ID
        new_customer = customer_data.to_dict()
        new_customer['id'] = doc_ref.id
        return jsonify(new_customer), 201
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# PUT update an existing customer.
@app.route('/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.json
    if not data:
        abort(400, description="Missing request body")
    
    doc_ref = db.collection('customers').document(customer_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Customer not found")
    
    # Get current data and update with new data
    current_data = doc.to_dict()
    current_data.update(data)
    
    try:
        # Validate the updated data
        updated_customer = CustomerModel(**current_data)
        
        # Update the document with validated data
        doc_ref.update(updated_customer.to_dict())
        
        # Return updated customer with ID
        response_data = updated_customer.to_dict()
        response_data['id'] = doc.id
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# DELETE a customer by document ID.
@app.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    doc_ref = db.collection('customers').document(customer_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Customer not found")
    
    doc_ref.delete()
    return jsonify({"message": f"Customer {customer_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)