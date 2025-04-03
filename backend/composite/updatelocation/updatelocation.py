import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
import requests
import pika

app = Flask(__name__)

try:
    cred = credentials.Certificate("../../firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# RabbitMQ Configuration
RABBITMQ_HOST = 'localhost'  # Change if RabbitMQ is hosted elsewhere
QUEUE_NAME = 'picker_location_updates'

# Google Distance Matrix API Configuration
GOOGLE_API_KEY = 'AIzaSyDjH28uAStkeoEpvlVqtgt3OJk4_w74iRA'
GOOGLE_DISTANCE_MATRIX_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json'

def send_to_picker_queue(picker_id, updated_location):
    """Safely send message to RabbitMQ with connection recovery"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST,
                                    heartbeat=600,
                                    blocked_connection_timeout=300))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)  # Persistent queue
        
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps({
                "pickerID": picker_id,
                "updatedLocation": updated_location
            }),
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            ))
        connection.close()
    except Exception as e:
        print(f"RabbitMQ error: {str(e)}")


# Function to get route details from Google Distance Matrix API
def get_route_details(origin, destination):
    params = {
        'origins': origin,
        'destinations': destination,
        'key': GOOGLE_API_KEY,
    }
    response = requests.get(GOOGLE_DISTANCE_MATRIX_URL, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data['rows'][0]['elements'][0]  # Return first route details
    else:
        print(f"Error fetching route details: {response.text}")
        return None


# Update Location Endpoint
@app.route('/update-location', methods=['POST'])
def update_location():
    try:
        # Parse request data
        data = request.json
        order_id = data.get('orderID')
        new_location = data.get('location')

        if not order_id or not new_location:
            return jsonify({"error": "orderID and location are required"}), 400

        # Fetch the order from Firestore
        order_ref = db.collection('orders').document(str(order_id))
        order_doc = order_ref.get()

        if not order_doc.exists:
            return jsonify({"error": "Order not found"}), 404

        # Update the location in Firestore
        order_ref.update({'location': new_location})
        
        # Get pickerID from the order document
        order_data = order_doc.to_dict()
        picker_id = order_data.get('pickerID')
        
        if not picker_id:
            return jsonify({"error": "Picker ID not found in order"}), 400

        # Calculate route using Google Distance Matrix API (optional)
        origin = new_location  # Assuming new location is the origin for simplicity
        destination = new_location  # You can modify this based on your use case (e.g., customer address)
        
        route_details = get_route_details(origin, destination)

        # Notify picker via RabbitMQ (AMQP)
        send_to_picker_queue(picker_id, new_location)

        return jsonify({
            "message": "Location updated successfully",
            "routeDetails": route_details,
            "pickerNotified": True,
            "orderID": order_id,
            "newLocation": new_location,
            "pickerID": picker_id,
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)