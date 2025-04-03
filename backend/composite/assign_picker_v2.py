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

# This is for the CORS Error where they need pre-flight check to see if it exists or something
@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def options_handler(path=None):
    return make_response('', 200)

# Configuration
RABBITMQ_HOST = "localhost"  # Use Docker service name
EXCHANGE_NAME = "order_delivery_exchange"
EXCHANGE_TYPE = "fanout"
ORDER_SERVICE_URL = "http://localhost:5003"  # Order microservice URL
PICKER_SERVICE_URL = "http://localhost:5001"  # Picker microservice URL

# Track active pickers and their socket IDs
active_pickers = {}
# Track orders waiting for pickup
pending_orders = {}

# =========================================================================
# Subscribe to RabbitMQ Exchange
# =========================================================================
def rabbitmq_listener():
    '''Setup RabbitMQ'''
    try:
        # Creates a RabbitMQ Exchange
        print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

        # Binds new queue to the Exchange
        result = channel.queue_declare(queue="assign_picker_queue", durable=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)
        print(f"RabbitMQ listener connected and bound to exchange {EXCHANGE_NAME}")

        # RabbitMQ Messaging Logic (when request is sent to rabbitMQ)
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"Received message from RabbitMQ: {message}")
                msg_type = message.get("type")
                
                # 3 types: Create new order, picker accepts order, order gets cancelled
                if msg_type == "new_order":
                    handle_new_order(message)
                elif msg_type == "picker_acceptance":
                    handle_picker_acceptance(message)
                elif msg_type == "order_cancelled":
                    handle_order_cancelled(message)
                else:
                    print(f"Unknown message type: {msg_type}")
            except Exception as e:
                print(f"Error processing RabbitMQ message: {str(e)}")

        # RabbitMQ Starts to run
        print(f"Starting to consume messages from queue {queue_name}")
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    # Error Handling for RabbitMQ
    except Exception as e:
        print(f"RabbitMQ listener error: {str(e)}")
        time.sleep(5) # Try to reconnect after a delay
        threading.Thread(target=rabbitmq_listener).start()

# =========================================================================
# 2. Picker Accepting Order
# Picker accept -> patch -> remove order -> notify picker and cust
# =========================================================================
def handle_picker_acceptance(message):
    order_id = message.get("order_id")
    picker_id = message.get("picker_id")
    
    # Check if there is order_id and picker_id
    if not order_id or not picker_id:
        print("Invalid picker_acceptance message format")
        return
    
    # Start the process
    print(f"Processing picker acceptance: Picker {picker_id} accepted Order {order_id}")
    
    # Send PATCH Request to update order status
    try:
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
            json={
                "order_status": "assigned",
                "picker_id": picker_id
            }
        )
        
        if response.status_code != 200:
            print(f"Failed to update order status: {response.text}")
            return
        
        order_data = response.json()
        print(f"Order {order_id} status updated: {order_data}")
    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        return
    
    # Remove from pending orders since it's been accepted
    if order_id in pending_orders:
        print(f"Removing order {order_id} from pending orders (accepted by picker {picker_id})")
        order_data = pending_orders.pop(order_id)
    else:
        print(f"Order {order_id} not found in pending orders")
    
    # Notify all pickers that this order is taken
    socketio.emit("order_taken", {
        "order_id": order_id,
        "picker_id": picker_id,
        "status": "assigned"
    }, room="pickers")
    print(f"Notified all pickers that order {order_id} was taken by picker {picker_id}")
    
    # Notify the customer if they're connected
    customer_room = f"customer_{order_id}"
    socketio.emit("picker_update", {
        "order_id": order_id,
        "picker_id": picker_id,
        "status": "assigned"
    }, room=customer_room)
    print(f"Notified customer in room '{customer_room}' about picker assignment")

# =========================================================================
# 3. Handle new order
# =========================================================================
def handle_new_order(message):
    order_id = message.get("order_id")
    order_data = message.get("order_data")
    
    # If no order_id or order_data then invalid
    if not order_id or not order_data:
        print("Invalid new_order message format")
        return
    
    print(f"Adding order {order_id} to pending orders")
    # Store in pending orders
    pending_orders[order_id] = order_data
    
    # Broadcast to all active pickers
    socketio.emit("order_waiting", {
        "order_id": order_id,
        "status": "pending",
        "details": order_data
    }, room="pickers")
    
    print(f"Broadcasted new order {order_id} to pickers room")

# =========================================================================
# 4. Handle Order Cancellation
# =========================================================================
def handle_order_cancelled(message):
    """Handle an order cancellation"""
    order_id = message.get("order_id")
    
    if not order_id:
        print("Invalid order_cancelled message format")
        return
    
    # Remove from pending orders
    if order_id in pending_orders:
        print(f"Removing order {order_id} from pending orders (cancelled)")
        pending_orders.pop(order_id)
    else:
        print(f"Order {order_id} not found in pending orders (for cancellation)")
    
    # Notify all pickers
    socketio.emit("order_cancelled", {
        "order_id": order_id
    }, room="pickers")
    print(f"Notified all pickers that order {order_id} was cancelled")

# =========================================================================
# 5. Publish to RabbitMQ Exchange the message
# =========================================================================
def publish_to_rabbitmq(message):
    """Publish a message to the RabbitMQ exchange"""
    try:
        # Connects to the rabbitMQ exchange
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)
        
        # publish the message
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key="",  # Fanout exchange ignores routing key
            body=json.dumps(message)
        )
        
        connection.close()
        print(f"Published message to RabbitMQ exchange '{EXCHANGE_NAME}'")
        return True
    except Exception as e:
        print(f"Error publishing to RabbitMQ: {str(e)}")
        return False

# =========================================================================
# 6. Start the RabbitMQ listener in a background thread
# =========================================================================
rabbitmq_thread = threading.Thread(target=rabbitmq_listener)
rabbitmq_thread.daemon = True
rabbitmq_thread.start()

# =========================================================================
# 7. create a new order endpoint
# =========================================================================
@app.route("/orders", methods=["POST"])
def create_order():
    """Create a new order and broadcast it to pickers"""
    try:
        print("Creating new order...")
        # Get order data from request
        order_data = request.get_json()
        print(f"Received order data: {order_data}")
        
        if not order_data:
            return jsonify({"error": "Missing order data"}), 400
            
        # Calls the ORDER MS to create a new order
        print(f"Sending to order service: {ORDER_SERVICE_URL}/orders")
        response = requests.post(f"{ORDER_SERVICE_URL}/orders", json=order_data)
        print(f"Order service response: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Failed to create order: {response.text}")
            return jsonify({"error": "Failed to create order"}), response.status_code
            
        new_order = response.json()
        order_id = new_order.get("id")
        print(f"Order created with ID: {order_id}")
        
        # Stores the order data in the pending order dict
        pending_orders[order_id] = new_order
        print(f"Added order {order_id} to pending orders")
        
        # Broadcast the new order to pickers
        message = {
            "order_id": order_id,
            "order_data": new_order,
            "type": "new_order"
        }
        
        # Directly emit to the pickers room via Socket.IO
        socketio.emit(
            "order_waiting",
            {
                "order_id": order_id,
                "status": "pending",
                "details": new_order
            },
            room="pickers"
        )
        print(f"Directly emitted order_waiting event to pickers room")
        
        print(f"Publishing to RabbitMQ: {message}")
        publish_to_rabbitmq(message)
        
        return jsonify({
            "message": "Order created and broadcast to pickers",
            "order_id": order_id
        }), 201
    
    except Exception as e:
        print(f"Error in create_order: {str(e)}")
        return jsonify({"error": f"Failed to process order: {str(e)}"}), 500

# =========================================================================
# 8. create a picker accept endpoint
# =========================================================================
@app.route("/picker_accept", methods=["POST"])
def picker_accept():
    """Handle a picker accepting an order"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request data"}), 400
            
        order_id = data.get("order_id")
        picker_id = data.get("picker_id")
        
        if not order_id or not picker_id:
            return jsonify({"error": "Missing order_id or picker_id"}), 400
            
        # Publish the acceptance to RabbitMQ
        message = {
            "order_id": order_id,
            "picker_id": picker_id,
            "type": "picker_acceptance"
        }
        
        if publish_to_rabbitmq(message):
            # Let all the picker and customer know order is accepted
            handle_picker_acceptance(message)
            
            return jsonify({
                "message": "Order acceptance processed",
                "order_id": order_id,
                "picker_id": picker_id
            }), 200
        else:
            return jsonify({"error": "Failed to process order acceptance"}), 500
            
    except Exception as e:
        print(f"Error in picker_accept: {str(e)}")
        return jsonify({"error": f"Failed to process acceptance: {str(e)}"}), 500

# =========================================================================
# 9. Customer cancel order endpoint
# =========================================================================
@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        # Update the order status in the order service
        response = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
            json={"order_status": "cancelled"}
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to update order status"}), response.status_code
            
        # Publish the cancellation to RabbitMQ
        message = {
            "order_id": order_id,
            "type": "order_cancelled"
        }
        
        if publish_to_rabbitmq(message):
            # Let the order be cancelled and notify customer and picker
            handle_order_cancelled(message)
            
            return jsonify({
                "message": "Order cancellation processed",
                "order_id": order_id
            }), 200
        else:
            return jsonify({"error": "Failed to process order cancellation"}), 500
            
    except Exception as e:
        print(f"Error in cancel_order: {str(e)}")
        return jsonify({"error": f"Failed to process cancellation: {str(e)}"}), 500

# =========================================================================
# 10. Endpoint to get pending orders for picker to see
# =========================================================================
@app.route("/debug/pending_orders", methods=["GET"])
def debug_pending_orders():
    """Return all pending orders (for debugging)"""
    return jsonify({
        "count": len(pending_orders),
        "orders": pending_orders
    })

# =========================================================================
# 11. Endpoint to get active pickers (Not that necessary)
# =========================================================================
@app.route("/debug/active_pickers", methods=["GET"])
def debug_active_pickers():
    """Return all active pickers (for debugging)"""
    return jsonify({
        "count": len(active_pickers),
        "pickers": active_pickers
    })


# =========================================================================
# 12. Websocket endpoints for UI to interact with
# =========================================================================
@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")
    
    # Remove from active pickers if this was a picker
    for picker_id, sid in list(active_pickers.items()):
        if sid == request.sid:
            print(f"Removing picker {picker_id} from active pickers")
            active_pickers.pop(picker_id)
            break

# =========================================================================
# 13. Register Picker and Customer and Test
# =========================================================================
@socketio.on("register_picker")
def register_picker(data):
    """Register a picker for receiving order notifications"""
    picker_id = data.get("picker_id")
    if not picker_id:
        return
    
    print(f"Picker {picker_id} registering with socket ID {request.sid}")
    
    # Add to active pickers
    active_pickers[picker_id] = request.sid
    
    # Join the pickers room to receive broadcasts
    join_room("pickers")
    print(f"Picker {picker_id} joined 'pickers' room")
    
    # Important: Send all currently pending orders to this newly connected picker
    print(f"Sending {len(pending_orders)} pending orders to picker {picker_id}")
    
    if pending_orders:
        for order_id, order_data in pending_orders.items():
            print(f"Sending pending order {order_id} to picker {picker_id}")
            # Send directly to this picker only (not broadcast to all)
            emit("order_waiting", {
                "order_id": order_id,
                "status": "pending",
                "details": order_data
            })
    else:
        print("No pending orders to send")
    
    print(f"Picker {picker_id} registration complete")

@socketio.on("register_customer")
def register_customer(data):
    """Register a customer for updates on their order"""
    customer_id = data.get("customer_id")
    order_id = data.get("order_id")
    
    if customer_id and order_id:
        customer_room = f"customer_{order_id}"
        join_room(customer_room)
        print(f"Customer {customer_id} joined room '{customer_room}' for order {order_id}")
        
        # Check if order is already assigned to a picker
        try:
            response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
            if response.status_code == 200:
                order_data = response.json()
                if order_data.get("order_status") == "assigned" and order_data.get("picker_id"):
                    # Send current picker information to the customer
                    emit("picker_update", {
                        "order_id": order_id,
                        "picker_id": order_data.get("picker_id"),
                        "status": "assigned"
                    })
                    print(f"Sent existing picker assignment to customer for order {order_id}")
        except Exception as e:
            print(f"Error checking order status: {str(e)}")

@socketio.on("test_event")
def handle_test_event(data):
    """Handle test event from client"""
    print(f"Received test event: {data}")
    emit("test_response", {"message": "Server received your test"})

# MAIN
if __name__ == "__main__":
    print("Starting Assign Picker service...")
    socketio.run(app, host="0.0.0.0", port=5005, debug=True)