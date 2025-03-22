import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Firebase Admin SDK (assuming firebase-adminsdk.json is in the correct location)
try:
    cred = credentials.Certificate("../../firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")


# Route to check service health
@app.route("/health", methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "picker-status-updater"})


# Route to handle cancellations
@app.route("/cancellations", methods=['POST'])
def cancellations():
    try:
        data = request.get_json()
        
        # Extract necessary data from the request
        # order_id = data.get('order_id')
        # picker_id = data.get('picker_id')
        # set default order_id
        order_id = "6eOgo89MFZsfx7RCzXV5"

        # set defualt picker_id
        picker_id = "BDDla3MO5SBOdLG9Bju5"

        if not order_id or not picker_id:
            return jsonify({"error": "Order ID and Picker ID are required"}), 400
        
        # Update order status to 'Cancelled' by picker
        order_ref = db.collection('orders').document(order_id)
        order_ref.update({
            'status': 'Cancelled by Picker'
        })
        
        # Update picker status to 'Cancelled'
        picker_ref = db.collection('pickers').document(picker_id)
        picker_ref.update({
            'status': 'Available'
        })
        
        return jsonify({"message": "Order and Picker status updated successfully"}), 200

    except Exception as e:
        print(f"Error processing cancellation: {e}")
        return jsonify({"error": "Failed to process cancellation"}), 500


if __name__ == '__main__':
    app.run(port=5003, debug=True)
