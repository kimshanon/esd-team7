import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, json, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK (assuming firebase-adminsdk.json is in the correct location)
try:
    cred = credentials.Certificate("../../firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# Connect to Firestore
db = firestore.client()

@app.route("/")
def home():
    return "Refund Microservice (Using Firebase Firestore)"

# POST /api/orders/{orderId}/refund
@app.route("/api/orders/<orderId>/refund", methods=['POST'])
async def create_refund(orderId):
    data = request.get_json()

    # Required fields
    required_fields = ["customerId", "paymentAmount", "refundReason", "photos"]

    # Check if all required fields are present in the request
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    # Create a new refund document in Firestore
    refund_ref = db.collection('refunds').document()
    refund_id = refund_ref.id
    refund_data = {
        "orderId": orderId,
        "customerId": data["customerId"],
        "paymentAmount": data["paymentAmount"],
        "refundReason": data["refundReason"],
        "photos": json.dumps(data["photos"]),  # Store photos as a JSON string
        "status": "pending"  # Can add status to track refund state (optional)
    }

    # Set the refund data to Firestore
    refund_ref.set(refund_data)

    # Return the created refund details
    return jsonify({"code": 201, "data": refund_data}), 201

# PUT /api/payments/refund
@app.route("/api/payments/refund", methods=['PUT'])
async def update_refund():
    data = request.get_json()

    # Required fields
    required_fields = ["orderId", "customerId", "paymentAmount"]

    # Check if all required fields are present in the request
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    # Find the refund document by orderId and customerId
    refund_ref = db.collection('refunds') \
                  .where('orderId', '==', data["orderId"]) \
                  .where('customerId', '==', data["customerId"]) \
                  .limit(1)  # Assuming there is only one refund per order and customer
    docs = refund_ref.stream()

    # Update refund details
    for refund in docs:
        refund_ref = db.collection('refunds').document(refund.id)
        refund_ref.update({"paymentAmount": data["paymentAmount"]})

        return jsonify({"code": 200, "message": "Refund updated successfully."}), 200

    return jsonify({"code": 404, "message": "Refund not found."}), 404


if __name__ == '__main__':
    app.run(port=5001, debug=True)
