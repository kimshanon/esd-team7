from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import pika
import json
import threading
import requests
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "order_delivery_exchange"
EXCHANGE_TYPE = "fanout"
ORDER_SERVICE_URL = "http://localhost:5003"
PICKER_SERVICE_URL = "http://localhost:5001"
PAYMENT_SERVICE_URL = "http://localhost:5008"

# Track active pickers and their socket IDs
active_pickers = {}
# Track orders waiting for pickup
pending_orders = {}
# Track assigned orders
assigned_orders = {}

# =========================================================================
# RabbitMQ Setup
# =========================================================================
def rabbitmq_listener():
    try:
        print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

        result = channel.queue_declare(queue="order_service_queue", durable=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)
        print(f"RabbitMQ listener connected and bound to exchange {EXCHANGE_NAME}")

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"Received message from RabbitMQ: {message}")
                msg_type = message.get("type")
                
                if msg_type == "new_order":
                    handle_new_order(message)
                elif msg_type == "picker_acceptance":
                    handle_picker_acceptance(message)
                elif msg_type == "picker_cancelled":
                    handle_picker_cancelled(message)
                elif msg_type == "order_completed":
                    handle_order_completed(message)
                elif msg_type == "location_updated":
                    handle_location_update(message)
                else:
                    print(f"Unknown message type: {msg_type}")
            except Exception as e:
                print(f"Error processing RabbitMQ message: {str(e)}")

        print(f"Starting to consume messages from queue {queue_name}")
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    except Exception as e:
        print(f"RabbitMQ listener error: {str(e)}")
        time.sleep(5)
        threading.Thread(target=rabbitmq_listener).start()

# =========================================================================
# Order Management Endpoints
# =========================================================================
@app.route("/api/v1/orders", methods=["POST"])
def create_order():
    """Create a new order and process payment"""
    try:
        print("Creating new order...")
        order_data = request.get_json()
        
        if not order_data:
            return jsonify({
                "code": 400,
                "message": "Missing order data",
                "data": None
            }), 400
            
        # Create order
        response = requests.post(f"{ORDER_SERVICE_URL}/api/v1/orders", json=order_data)
        
        if response.status_code != 201:
            return jsonify({
                "code": response.status_code,
                "message": "Failed to create order",
                "data": None
            }), response.status_code
            
        new_order = response.json().get("data", {})
        order_id = new_order.get("order_id")

        # Process payment immediately
        payment_data = {
            "customer_id": order_data.get("customer_id"),
            "payment_amount": order_data.get("credit", 0.0),
            "order_id": order_id
        }

        payment_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/api/v1/payments/process",
            json=payment_data
        )
        
        if payment_response.status_code != 200:
            # If payment fails, cancel the order
            requests.patch(
                f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
                json={"order_status": "Cancelled"}
            )
            return jsonify({
                "code": payment_response.status_code,
                "message": "Payment processing failed",
                "data": None
            }), payment_response.status_code
        
        # Store order in pending orders
        pending_orders[order_id] = new_order
        
        # Broadcast to pickers
        message = {
            "order_id": order_id,
            "order_data": new_order,
            "type": "new_order"
        }
        
        socketio.emit(
            "order_waiting",
            {
                "order_id": order_id,
                "status": "Pending",
                "details": new_order
            },
            room="pickers"
        )
        
        publish_to_rabbitmq(message)
        
        return jsonify({
            "code": 201,
            "message": "Order created and broadcast to pickers",
            "data": {
                "order_id": order_id,
                "payment_id": payment_response.json().get("data", {}).get("payment_id")
            }
        }), 201
    
    except Exception as e:
        print(f"Error in create_order: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Failed to process order: {str(e)}",
            "data": None
        }), 500

@app.route("/api/v1/orders/<order_id>/complete", methods=["POST"])
def complete_order(order_id):
    """Mark order as completed and credit picker"""
    try:
        # Get order details
        order_response = requests.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}")
        if order_response.status_code != 200:
            return jsonify({
                "code": 404,
                "message": "Order not found",
                "data": None
            }), 404

        order_data = order_response.json().get("data", {})
        picker_id = order_data.get("picker_id")
        
        if not picker_id:
            return jsonify({
                "code": 400,
                "message": "Order has no assigned picker",
                "data": None
            }), 400

        # Update order status to completed
        update_response = requests.patch(
            f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
            json={"order_status": "Completed"}
        )

        if update_response.status_code != 200:
            return jsonify({
                "code": update_response.status_code,
                "message": "Failed to update order status",
                "data": None
            }), update_response.status_code

        # Credit picker with $2 flat fee
        credit_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/api/v1/orders/{order_id}/complete"
        )

        if credit_response.status_code != 200:
            return jsonify({
                "code": credit_response.status_code,
                "message": "Failed to credit picker",
                "data": None
            }), credit_response.status_code

        # Remove from assigned orders
        if order_id in assigned_orders:
            assigned_orders.pop(order_id)

        # Notify picker
        socketio.emit(
            "order_completed",
            {
                "order_id": order_id,
                "status": "Completed"
            },
            room=f"picker_{picker_id}"
        )

        return jsonify({
            "code": 200,
            "message": "Order completed and picker credited",
            "data": {
                "order_id": order_id,
                "picker_id": picker_id
            }
        }), 200

    except Exception as e:
        print(f"Error completing order: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Failed to complete order: {str(e)}",
            "data": None
        }), 500

# =========================================================================
# Message Handlers
# =========================================================================
def handle_new_order(message):
    """Handle new order creation and broadcast to pickers"""
    order_id = message.get("order_id")
    order_data = message.get("order_data")
    
    if not order_id or not order_data:
        print("Invalid new_order message format")
        return
    
    print(f"Adding order {order_id} to pending orders")
    pending_orders[order_id] = order_data
    
    # Broadcast to all active pickers
    socketio.emit("order_waiting", {
        "order_id": order_id,
        "status": "pending",
        "details": order_data
    }, room="pickers")
    
    print(f"Broadcasted new order {order_id} to pickers room")

def handle_picker_acceptance(message):
    """Handle picker accepting an order"""
    order_id = message.get("order_id")
    picker_id = message.get("picker_id")
    
    if not order_id or not picker_id:
        print("Invalid picker_acceptance message format")
        return
    
    print(f"Processing picker acceptance: Picker {picker_id} accepted Order {order_id}")
    
    # Update order status and assign picker
    try:
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
            json={
                "order_status": "Active",
                "picker_id": picker_id
            }
        )
        
        if response.status_code != 200:
            print(f"Failed to update order status: {response.text}")
            return
        
        # Remove from pending orders and add to assigned orders
        if order_id in pending_orders:
            pending_orders.pop(order_id)
        assigned_orders[order_id] = picker_id
        
        # Notify all pickers that order is taken
        socketio.emit("order_taken", {
            "order_id": order_id,
            "picker_id": picker_id,
            "status": "active"
        }, room="pickers")
        
        # Notify customer
        customer_room = f"customer_{order_id}"
        socketio.emit("picker_update", {
            "order_id": order_id,
            "picker_id": picker_id,
            "status": "active"
        }, room=customer_room)
        
    except Exception as e:
        print(f"Error updating order status: {str(e)}")

def handle_picker_cancelled(message):
    """Handle picker cancelling an order"""
    order_id = message.get("order_id")
    picker_id = message.get("picker_id")
    
    if not order_id or not picker_id:
        print("Invalid picker_cancelled message format")
        return
    
    # Remove from assigned orders and add back to pending orders
    if order_id in assigned_orders:
        assigned_orders.pop(order_id)
        order_data = requests.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}").json().get("data", {})
        pending_orders[order_id] = order_data
        
        # Notify customer about searching for new picker
        customer_room = f"customer_{order_id}"
        socketio.emit("picker_update", {
            "order_id": order_id,
            "status": "searching",
            "message": "Searching for a new picker..."
        }, room=customer_room)
        
        # Broadcast to all pickers again
        socketio.emit("order_waiting", {
            "order_id": order_id,
            "status": "pending",
            "details": order_data
        }, room="pickers")

def handle_location_update(message):
    """Handle order location updates - only notify picker"""
    order_id = message.get("order_id")
    new_location = message.get("new_location")
    
    if not order_id or not new_location:
        print("Invalid location_update message format")
        return
    
    try:
        # Get order details to find picker
        order_response = requests.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}")
        if order_response.status_code != 200:
            print(f"Failed to get order details: {order_response.text}")
            return
        
        order_data = order_response.json().get("data", {})
        picker_id = order_data.get("picker_id")
        
        if picker_id:
            # Notify picker of location change
            socketio.emit("location_updated", {
                "order_id": order_id,
                "new_location": new_location
            }, room=f"picker_{picker_id}")
            print(f"Notified picker {picker_id} of location update for order {order_id}")
            
    except Exception as e:
        print(f"Error handling location update notification: {str(e)}")

def handle_order_completed(message):
    """Handle order completion and notify relevant parties"""
    order_id = message.get("order_id")
    customer_id = message.get("customer_id")
    
    if not order_id or not customer_id:
        print("Invalid order_completed message format")
        return
    
    try:
        # Get order details
        order_response = requests.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}")
        if order_response.status_code != 200:
            print(f"Failed to get order details: {order_response.text}")
            return
            
        order_data = order_response.json().get("data", {})
        picker_id = order_data.get("picker_id")
        
        if not picker_id:
            print(f"Order {order_id} has no assigned picker")
            return
        
        # Update order status to completed
        update_response = requests.patch(
            f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}/status",
            json={"order_status": "Completed"}
        )
        
        if update_response.status_code != 200:
            print(f"Failed to update order status: {update_response.text}")
            return
        
        # Credit picker with $2 flat fee
        credit_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/api/v1/orders/{order_id}/complete"
        )
        
        if credit_response.status_code != 200:
            print(f"Failed to credit picker: {credit_response.text}")
            return
        
        # Remove from assigned orders
        if order_id in assigned_orders:
            assigned_orders.pop(order_id)
        
        # Notify picker
        socketio.emit(
            "order_completed",
            {
                "order_id": order_id,
                "status": "Completed"
            },
            room=f"picker_{picker_id}"
        )
        
        # Notify customer
        customer_room = f"customer_{order_id}"
        socketio.emit(
            "order_completed",
            {
                "order_id": order_id,
                "status": "Completed",
                "message": "Order has been delivered successfully"
            },
            room=customer_room
        )
        
        print(f"Order {order_id} completed and picker {picker_id} credited")
        
    except Exception as e:
        print(f"Error handling order completion: {str(e)}")

# =========================================================================
# WebSocket Handlers
# =========================================================================
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    for picker_id, sid in list(active_pickers.items()):
        if sid == request.sid:
            active_pickers.pop(picker_id)
            break

@socketio.on("register_picker")
def register_picker(data):
    picker_id = data.get("picker_id")
    if not picker_id:
        return
    
    print(f"Picker {picker_id} registering with socket ID {request.sid}")
    active_pickers[picker_id] = request.sid
    join_room("pickers")
    join_room(f"picker_{picker_id}")
    
    # Send pending orders to new picker
    if pending_orders:
        for order_id, order_data in pending_orders.items():
            emit("order_waiting", {
                "order_id": order_id,
                "status": "Pending",
                "details": order_data
            })

@socketio.on("register_customer")
def register_customer(data):
    customer_id = data.get("customer_id")
    order_id = data.get("order_id")
    
    if customer_id and order_id:
        customer_room = f"customer_{order_id}"
        join_room(customer_room)
        
        # Check if order is already assigned
        try:
            response = requests.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}")
            if response.status_code == 200:
                order_data = response.json().get("data", {})
                if order_data.get("order_status") == "active" and order_data.get("picker_id"):
                    emit("picker_update", {
                        "order_id": order_id,
                        "picker_id": order_data.get("picker_id"),
                        "status": "Active"
                    })
        except Exception as e:
            print(f"Error checking order status: {str(e)}")

# =========================================================================
# Helper Functions
# =========================================================================
def publish_to_rabbitmq(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)
        
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key="",
            body=json.dumps(message)
        )
        
        connection.close()
        print(f"Published message to RabbitMQ exchange '{EXCHANGE_NAME}'")
        return True
    except Exception as e:
        print(f"Error publishing to RabbitMQ: {str(e)}")
        return False

# Start RabbitMQ listener in background
rabbitmq_thread = threading.Thread(target=rabbitmq_listener)
rabbitmq_thread.daemon = True
rabbitmq_thread.start()

if __name__ == "__main__":
    print("Starting Order Service...")
    socketio.run(app, host="0.0.0.0", port=5005, debug=True) 