import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Base URL of Payment Microservice
PAYMENT_SERVICE_URL = "http://localhost:5001"
ORDER_SERVICE_URL = "http://localhost:5003"
CUSTOMER_SERVICE_URL = "https://personal-dcwqxa6n.outsystemscloud.com"

@app.route("/api/orders/<paymentID>/refund", methods=["POST"])
def process_refund(paymentID):

    # Call Payment Microservice to update status to "refund"
    refund_response = requests.put(
        f"{PAYMENT_SERVICE_URL}/payment/{paymentID}/status",
        json={"payment_status": "refund"}
    )

    if refund_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to update payment status."}), 500

    # Call Payment Microservice to get payment information
    payment_response = requests.get(
        f"{PAYMENT_SERVICE_URL}/payment/{paymentID}/transaction"
    )

    # Get order ID 
    payment_data = payment_response.json().get("payment_details", {})
    order_id = payment_data.get("order_id")

    if not order_id:
        return jsonify({"code": 400, "message": "Order ID missing from payment details."}), 400




    # Call Order Microservice to get order
    order_response = requests.get(
        f"{ORDER_SERVICE_URL}/orders/{order_id}"
    )

    if order_response.status_code != 200:
        return jsonify({"code": 404, "message": "Order not found."}), 404
    
    # Call Order Microservice to update order status to "cancelled"
    cancel_response = requests.patch(
        f"{ORDER_SERVICE_URL}/orders/{order_id}/cancel",
        json={"status": "Cancelled"}
    )

    if cancel_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to cancel order."}), 500

    # Get credits for order + customerID
    order_data = order_response.json().get("data", {})
    order_credits = order_data.get("credit")
    order_customerID = order_data.get("customerID")

    if not order_customerID:
        return jsonify({"code": 400, "message": "Customer ID missing from order details."}), 400

    # Call customer microservice to get customer credits
    customer_response = requests.get(
        f"{CUSTOMER_SERVICE_URL}/SMUlivery/rest/CustomerAPI/customers/id/{order_customerID}"
    )

    if customer_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to retrieve customer data."}), 500

    customer_data = customer_response.json().get("Customer", {})
    customer_credits = customer_data.get("customerCredits")

    # Convert string to integer
    customer_credits = int(customer_credits)
    order_credits = int(order_credits)

    # add up customer credits with order credits
    new_credits = customer_credits + order_credits

    # Convert string to integer
    new_credits = int(new_credits)

    # update customer credits
    update_response = requests.put(
        f"{CUSTOMER_SERVICE_URL}/SMUlivery/rest/CustomerAPI/customers/{order_customerID}/UpdateCustomerCredits",
        json={"customerCredits":new_credits}
    )

    if update_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to update customer credits."}), 500

    return jsonify({"code": 200, "message": f"Refund processed for payment {paymentID}."}), 200

if __name__ == "__main__":
    app.run(port=5002, debug=True)
