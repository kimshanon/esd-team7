from flask import Flask, request, jsonify
import requests
import os
import logging
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CompositeService")

# Environment variables (set these before running)
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:5001")  # Order Microservice URL
# PICKER_UI_URL = os.getenv("PICKER_UI_URL", "XX NOT YET ADDED")             # Picker UI URL

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

@app.route('/composite/orders/<string:order_id>/location', methods=['PATCH'])
def update_order_location(order_id):
    """Composite workflow: Update order location if status is not 'Completed'"""
    try:
        # 1. Validate request payload
        data = request.get_json()
        if not data or 'location' not in data or 'position' not in data['location']:
            return jsonify({"code": 400, "message": "Invalid request, missing location or position"}), 400
        
        location_data = data['location']
        position = location_data.get('position', {})
        
        # Validate SMU location boundaries (ensure within campus bounds)
        if not validate_smu_location(position):
            return jsonify({"code": 400, "message": "Location outside SMU"}), 400

        # 2. Check order status from Order Microservice
        order_status_response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
        if order_status_response.status_code != 200:
            return jsonify(order_status_response.json()), order_status_response.status_code
        
        order_data = order_status_response.json().get("data", {})
        if not order_data:
            return jsonify({"code": 404, "message": "Order not found"}), 404
        
        # Check if the order status is 'Completed'
        if order_data.get("order_status") == "completed":
            return jsonify({"code": 400, "message": "Cannot update location for completed orders"}), 400

        # 3. Call Order Microservice to update location
        order_response = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/location",
            json={"location": location_data}
        )

        if order_response.status_code != 200:
            return jsonify(order_response.json()), order_response.status_code

        # Return success response
        return jsonify({
            "code": 200,
            "message": "Order location updated successfully",
            "data": {
                "order_update_status": order_response.json()
            }
        }), 200

    except Exception as e:
        logger.error(f"Composite service error: {str(e)}")
        return jsonify({"code": 500, "message": "Server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
