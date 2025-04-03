import requests
from flask import Flask, request, jsonify
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Order microservice URL - change to your actual URL
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://order-service:5001/orders')

# Route to check service health
@app.route("/health", methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "location-updater-composite"})

# Route to update order location
@app.route("/api/location/update", methods=['PUT'])
def update_location():
    try:
        data = request.get_json()
        
        # Extract necessary data from the request
        order_id = data.get('order_id')
        new_location = data.get('location')
        
        # Validate input
        if not order_id:
            return jsonify({"error": "Order ID is required"}), 400
        if not new_location:
            return jsonify({"error": "Location is required"}), 400
        
        logger.info(f"Forwarding location update for order {order_id} to {new_location}")
        
        # Call the order microservice to update the location
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/{order_id}/location",
            json={"location": new_location},
            timeout=5  # 5 second timeout
        )
        
        # Check response from order service
        if response.status_code != 200:
            error_msg = f"Order service returned status {response.status_code}"
            logger.error(f"{error_msg}: {response.text}")
            return jsonify({"error": error_msg}), 500
        
        # Return successful response with the updated order data
        return jsonify({
            "message": "Order location updated successfully",
            "order": response.json()
        }), 200
        
    except requests.RequestException as e:
        error_msg = f"Error connecting to order service: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 503
        
    except Exception as e:
        error_msg = f"Error updating location: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port)