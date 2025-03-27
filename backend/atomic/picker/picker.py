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

@app.route("/")
def home():
    return "Picker Microservice (Using Firebase Firestore)"

# Get all pickers WORKS
@app.route("/pickers", methods=['GET'])
def get_all_pickers():
    pickers_ref = db.collection('pickers')
    docs = pickers_ref.stream()
    pickers = [doc.to_dict() for doc in docs]

    if pickers:
        return jsonify({"code": 200, "data": pickers}), 200
    else:
        return jsonify({"code": 404, "message": "No pickers found."}), 404

# Add a bulk list of pickers (NEW ROUTE) WORKS
@app.route("/pickers/add_bulk", methods=['POST'])
def add_bulk_pickers():
    pickers = [
        {"pickerName": "John Doe", "pickerPhone": "9876-5432", "pickerStatus": "Available"},
        {"pickerName": "Jane Smith", "pickerPhone": "8765-4321", "pickerStatus": "Busy"},
        {"pickerName": "Robert Johnson", "pickerPhone": "9123-4567", "pickerStatus": "Available"},
        {"pickerName": "Sarah Williams", "pickerPhone": "8234-5678", "pickerStatus": "Offline"},
        {"pickerName": "Michael Brown", "pickerPhone": "9345-6789", "pickerStatus": "Available"}
    ]

    picker_collection = db.collection('pickers')

    for picker in pickers:
        picker_collection.add(picker)

    return jsonify({"code": 201, "message": "Pickers added successfully!"}), 201



# Get specific picker WORKS
@app.route("/pickers/<pickerID>", methods=['GET'])
def get_picker(pickerID):
    picker_ref = db.collection('pickers').document(pickerID)
    picker = picker_ref.get()
    
    if picker.exists:
        return jsonify({"code": 200, "data": picker.to_dict()}), 200
    else:
        return jsonify({"code": 404, "message": f"Picker {pickerID} not found."}), 404



# Add a new picker WORKS
@app.route("/pickers", methods=['POST'])
def add_picker():
    data = request.get_json()
    picker_ref = db.collection('pickers').document()  # Auto-generate ID
    picker_ref.set(data)

    return jsonify({"code": 201, "data": data}), 201



# Update picker status
@app.route("/pickers/<pickerID>/status", methods=['PUT'])
def update_picker_status(pickerID):
    data = request.get_json()
    new_status = data.get('pickerStatus')

    if not new_status:
        return jsonify({"code": 400, "message": "Picker status is required."}), 400

    picker_ref = db.collection('pickers').document(pickerID)
    picker_ref.update({"pickerStatus": new_status})

    return jsonify({"code": 200, "message": f"Picker {pickerID} status updated to {new_status}."}), 200



# Delete a picker -- when picker deletes account
@app.route("/pickers/<pickerID>", methods=['DELETE'])
def delete_picker(pickerID):
    picker_ref = db.collection('pickers').document(pickerID)
    picker_ref.delete()

    return jsonify({"code": 200, "message": f"Picker {pickerID} has been deleted."}), 200



# Get available pickers - will be called by assigned microservice 
@app.route("/pickers/available", methods=['GET'])
def get_available_pickers():
    pickers_ref = db.collection('pickers').where("pickerStatus", "==", "Available")
    docs = pickers_ref.stream()
    pickers = [doc.to_dict() for doc in docs]

    if pickers:
        return jsonify({"code": 200, "data": pickers}), 200
    else:
        return jsonify({"code": 404, "message": "No available pickers found."}), 404

if __name__ == '__main__':
    app.run(port=5001, debug=True)
