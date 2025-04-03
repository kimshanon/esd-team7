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
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5001')

# SMU Campus Boundaries (for validation)
SMU_BOUNDS = {
    'north': 1.299,
    'south': 1.293,
    'east': 103.852,
    'west': 103.846
}

def validate_smu_location(coordinates):
    """Ensure location is within SMU campus"""
    lat = coordinates.get('lat', 0)
    lng = coordinates.get('lng', 0)
    return (SMU_BOUNDS['south'] <= lat <= SMU_BOUNDS['north'] and
            SMU_BOUNDS['west'] <= lng <= SMU_BOUNDS['east'])

# Route to check service health
@app.route("/health", methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "location-updater-composite"})

# Route to update order location
@app.route("/api/location/update", methods=['PUT'])
def update_location():
    try:
        data = request.get_json()
        logger.info(f"Received location update request: {data}")
        
        # Extract necessary data from the request
        order_id = data.get('order_id')
        new_location = data.get('location')
        
        # Validate input
        if not order_id:
            return jsonify({"code": 400, "message": "Order ID is required"}), 400
        if not new_location:
            return jsonify({"code": 400, "message": "Location is required"}), 400
        
        # Validate coordinates are within SMU campus
        coordinates = new_location.get('coordinates', {})
        if not validate_smu_location(coordinates):
            logger.warning(f"Location outside SMU boundaries: {coordinates}")
            return jsonify({"code": 400, "message": "Location outside SMU campus boundaries"}), 400
        
        logger.info(f"Forwarding location update for order {order_id}")
        
        # Call the order microservice to update the location
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/location",
            json={"location": new_location},
            timeout=5  # 5 second timeout
        )
        
        # Check response from order service
        if response.status_code != 200:
            error_msg = f"Order service returned status {response.status_code}"
            logger.error(f"{error_msg}: {response.text}")
            return jsonify({"code": response.status_code, "message": error_msg}), response.status_code
        
        # Parse the response from the order service
        order_response = response.json()
        logger.info(f"Order service response: {order_response}")
        
        # Return successful response with the updated order data
        return jsonify({
            "code": 200,
            "message": "Order location updated successfully",
            "data": order_response
        }), 200
        
    except requests.RequestException as e:
        error_msg = f"Error connecting to order service: {str(e)}"
        logger.error(error_msg)
        return jsonify({"code": 503, "message": error_msg}), 503
        
    except Exception as e:
        error_msg = f"Error updating location: {str(e)}"
        logger.error(error_msg)
        return jsonify({"code": 500, "message": error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)