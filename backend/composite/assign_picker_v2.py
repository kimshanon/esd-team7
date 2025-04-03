from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import pika
import json
import threading
import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def options_handler(path=None):
    return make_response('', 200)

# Configuration
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "order_delivery_exchange"
EXCHANGE_TYPE = "fanout"
ORDER_SERVICE_URL = "http://localhost:5003"  # Order microservice URL
PICKER_SERVICE_URL = "http://localhost:5001"  # Picker microservice URL

# Track active pickers and their socket IDs
active_pickers = {}
# Track orders waiting for pickup
pending_orders = {}

def rabbitmq_listener():
    """Background thread that listens for messages from RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

        def callback(ch, method, properties, body):
            message = json.loads(body)
            msg_type = message.get("type")
            
            if msg_type == "picker_acceptance":
                handle_picker_acceptance(message)
            elif msg_type == "new_order":
                handle_new_order(message)
            elif msg_type == "order_cancelled":
                handle_order_cancelled(message)

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print("RabbitMQ listener started")
        channel.start_consuming()
    except Exception as e:
        print(f"RabbitMQ listener error: {str(e)}")
        # Consider implementing reconnection logic here

def handle_picker_acceptance(message):
    """Handle when a picker accepts an order"""
    order_id = message.get("order_id")
    picker_id = message.get("picker_id")
    
    if order_id in pending_orders:
        # Remove order from pending list
        del pending_orders[order_id]
        
        # Notify the customer
        socketio.emit(
            "picker_update",
            {
                "order_id": order_id,
                "picker_id": picker_id,
                "status": "Picker Accepted"
            },
            room=f"customer_{order_id}"
        )
        
        # Notify all pickers that the order is no longer available
        socketio.emit(
            "order_taken",
            {
                "order_id": order_id,
                "picker_id": picker_id
            },
            room="pickers"
        )
        
        # Update order status in order service
        try:
            requests.patch(
                f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
                json={"order_status": "assigned", "picker_id": picker_id}
            )
        except Exception as e:
            print(f"Failed to update order status: {str(e)}")

def handle_new_order(message):
    """Handle new order broadcast"""
    order_id = message.get("order_id")
    order_data = message.get("order_data", {})
    
    # Store in pending orders
    pending_orders[order_id] = order_data
    
    # Broadcast to all active pickers
    socketio.emit(
        "order_waiting",
        {
            "order_id": order_id,
            "status": "Order waiting for acceptance",
            "details": order_data
        },
        room="pickers"
    )

def handle_order_cancelled(message):
    """Handle order cancellation"""
    order_id = message.get("order_id")
    
    if order_id in pending_orders:
        del pending_orders[order_id]
        
        # Notify pickers to remove this order
        socketio.emit(
            "order_cancelled",
            {"order_id": order_id},
            room="pickers"
        )

def publish_to_rabbitmq(message):
    """Helper function to publish messages to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", body=json.dumps(message))
        connection.close()
        return True
    except Exception as e:
        print(f"RabbitMQ publish error: {str(e)}")
        return False

# Start the RabbitMQ listener in a background thread
threading.Thread(target=rabbitmq_listener, daemon=True).start()

@app.route("/orders", methods=["POST"])
def create_order():
    """Create a new order and broadcast it to pickers"""
    try:
        # Get order data from request
        order_data = request.get_json()
        if not order_data:
            return jsonify({"error": "Missing order data"}), 400
            
        # Create the order in the order service
        response = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
        if response.status_code != 201:
            return jsonify({"error": "Failed to create order"}), response.status_code
            
        new_order = response.json()
        order_id = new_order.get("id")
        
        # Broadcast the new order to pickers
        message = {
            "order_id": order_id,
            "order_data": new_order,
            "type": "new_order"
        }
        
        if publish_to_rabbitmq(message):
            return jsonify({
                "message": "Order created and broadcast to pickers",
                "order_id": order_id,
                "order_data": new_order
            }), 201
        else:
            return jsonify({"error": "Order created but failed to broadcast to pickers"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Failed to process order: {str(e)}"}), 500

@app.route("/picker_accept", methods=["POST"])
def picker_accept():
    """Endpoint for a picker to accept an order"""
    data = request.get_json()
    if not data or "order_id" not in data or "picker_id" not in data:
        return jsonify({"error": "Missing required fields: order_id and picker_id"}), 400

    order_id = data["order_id"]
    picker_id = data["picker_id"]
    
    # Check if order is still available (not already taken by another picker)
    if order_id not in pending_orders:
        return jsonify({"error": "This order is no longer available"}), 409
    
    # Publish the acceptance message
    message = {
        "order_id": order_id,
        "picker_id": picker_id,
        "type": "picker_acceptance"
    }
    
    if publish_to_rabbitmq(message):
        return jsonify({"message": "Order accepted successfully"}), 200
    else:
        return jsonify({"error": "Failed to process order acceptance"}), 500

@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        # Update order status in order service
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
            json={"order_status": "cancelled"}
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to cancel order"}), response.status_code
        
        # Publish cancellation message
        message = {
            "order_id": order_id,
            "type": "order_cancelled"
        }
        
        if publish_to_rabbitmq(message):
            return jsonify({"message": "Order cancelled successfully"}), 200
        else:
            return jsonify({"error": "Order marked as cancelled but failed to notify pickers"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Failed to cancel order: {str(e)}"}), 500

@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("register_picker")
def register_picker(data):
    """Register a picker for receiving order notifications"""
    picker_id = data.get("picker_id")
    if not picker_id:
        return
    
    # Add to active pickers
    active_pickers[picker_id] = request.sid
    join_room("pickers")
    
    # Send currently pending orders to this picker
    for order_id, order_data in pending_orders.items():
        emit("order_waiting", {
            "order_id": order_id,
            "status": "Order waiting for acceptance",
            "details": order_data
        })
    
    print(f"Picker {picker_id} registered")

@socketio.on("register_customer")
def register_customer(data):
    """Register a customer for updates on their order"""
    customer_id = data.get("customer_id")
    order_id = data.get("order_id")
    
    if customer_id and order_id:
        join_room(f"customer_{order_id}")
        print(f"Customer {customer_id} registered for updates on order {order_id}")

@socketio.on("disconnect")
def handle_disconnect():
    """Clean up when a client disconnects"""
    # Find and remove disconnected picker
    for picker_id, sid in list(active_pickers.items()):
        if sid == request.sid:
            del active_pickers[picker_id]
            print(f"Picker {picker_id} disconnected")
            break

if __name__ == "__main__":
    # Run the service with SocketIO
    socketio.run(app, host="0.0.0.0", port=5005, debug=True)