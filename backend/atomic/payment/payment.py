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
    
# Update payment status
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
        required_fields = ["log_id", "order_id", "event_type", "event_details", "payment_status", "timestamp"]
        payment_details = {field: payment_data.get(field, "Unknown") for field in required_fields}
        return jsonify({"code": 200, "payment_details": payment_details}), 200
    else:
        return jsonify({"code": 404, "message": f"Payment {payment_id} not found."}), 404

# Create a new payment
@app.route("/payment", methods=['POST'])
def create_payment():
    data = request.get_json()
    required_fields = ["log_id", "order_id", "event_type", "event_details", "payment_status", "timestamp"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400
    
    payment_ref = db.collection('payments').document()
    payment_id = payment_ref.id
    data["payment_id"] = payment_id
    
    payment_ref.set(data)
    
    return jsonify({"code": 201, "data": data}), 201

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
    app.run(port=5001, debug=True)
