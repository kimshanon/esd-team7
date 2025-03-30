import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Base URL of Payment Microservice
PAYMENT_SERVICE_URL = "http://localhost:5001"

@app.route("/api/orders/<paymentID>/refund", methods=["POST"])
def process_refund(paymentID):
    data = request.get_json()
    customer_id = data.get("customerId")
    payment_amount = data.get("paymentAmount")
    
    if not customer_id or not payment_amount:
        return jsonify({"code": 400, "message": "Missing required fields."}), 400


    # Call Payment Microservice to update status to "refund"
    response = requests.put(
        f"{PAYMENT_SERVICE_URL}/payment/{paymentID}/status",
        json={"payment_status": "refund"}
    )

    if response.status_code == 200:
        return jsonify({"code": 200, "message": f"Refund processed for payment {paymentID}."}), 200
    else:
        return jsonify({"code": response.status_code, "message": "Failed to update payment status."}), response.status_code

if __name__ == "__main__":
    app.run(port=5002, debug=True)
