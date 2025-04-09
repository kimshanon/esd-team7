from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import pika
import json
import threading
import requests
import time
from dotenv import load_dotenv
import os
import sys
import eventlet

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Test
@app.route('/test', methods=['GET'])
def test():
    return "Assign Picker is running"

# This is for the CORS Error where they need pre-flight check to see if it exists or something
@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def options_handler(path=None):
    return make_response('', 200)

# Configuration - Use environment variables instead of hardcoded values
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
EXCHANGE_NAME = "order_delivery_exchange"
EXCHANGE_TYPE = "fanout"
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:5003")
PICKER_SERVICE_URL = os.getenv("PICKER_SERVICE_URL", "http://localhost:5001")
CALC_PAYMENT_SERVICE_URL = os.getenv("CALC_PAYMENT_SERVICE_URL", "http://calc-payment-service:5009")

# Track active pickers and their socket IDs
active_pickers = {}
# Track orders waiting for pickup
pending_orders = {}

# URLs for the other microservices
ORDER_URL = f"{ORDER_SERVICE_URL}/orders"
PICKER_URL = f"{PICKER_SERVICE_URL}/pickers"

# WebSocket event names
WS_ORDER_WAITING = "order_waiting"
WS_ORDER_TAKEN = "order_taken"
WS_PICKER_UPDATE = "picker_update"
WS_REGISTER_PICKER = "register_picker"
WS_REGISTER_CUSTOMER = "register_customer"
WS_TEST_EVENT = "test_event"
WS_TEST_RESPONSE = "test_response"

# Keep track of connected pickers and customers
connected_pickers = {}  # picker_id -> sid
customer_orders = {}    # customer_id -> list of order_ids
order_customers = {}    # order_id -> customer_id

# Helper function to get order details
def get_order_details(order_id):
    try:
        response = requests.get(f"{ORDER_URL}/{order_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting order details: {e}")
        return None

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
            f"{ORDER_URL}/{order_id}/status",
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
    socketio.emit(WS_ORDER_TAKEN, {
        "order_id": order_id,
        "picker_id": picker_id,
        "status": "assigned"
    })  # Changed from room="pickers" t for compatibility
    print(f"Notified all pickers that order {order_id} was taken by picker {picker_id}")
    
    # Notify the customer if they're connected
    if order_id in order_customers:
        customer_id = order_customers[order_id]
        
        # Get the full order details to include in notification
        order_details = get_order_details(order_id)
        
        # Emit the picker update event
        socketio.emit(WS_PICKER_UPDATE, {
            "order_id": order_id,
            "customer_id": customer_id,
            "picker_id": picker_id,
            "status": "assigned",
            "details": order_details
        })  # This ensures all clients get the update
        
        print(f"Notified customer {customer_id} that order {order_id} was accepted")

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
    socketio.emit(WS_ORDER_WAITING, {
        "order_id": order_id,
        "status": "pending",
        "details": order_data
    })  # Changed from room="pickers" t
    
    print(f"Broadcasted new order {order_id} to all connected clients")
    
    # If this is an order returned to pending, use the message type to differentiate
    if message.get("type") == "order_returned_to_pending":
        print(f"Order {order_id} returned to pending state")

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
    })  # Changed from room="pickers" t
    print(f"Notified all clients that order {order_id} was cancelled")

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
# 7. create a new order endpoint - MERGED THE TWO FUNCTIONS
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
        print(f"Sending to order service: {ORDER_URL}")
        response = requests.post(ORDER_URL, json=order_data)
        print(f"Order service response: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Failed to create order: {response.text}")
            return jsonify({"error": "Failed to create order"}), response.status_code
            
        new_order = response.json()
        order_id = new_order.get("id")
        print(f"Order created with ID: {order_id}")
        
        # Process payment for the order
        try:
            # Calculate total amount from order items
            order_items = order_data.get("order_items", [])
            total_amount = 0
            
            for item in order_items:
                # Make sure item_price and quantity can be properly converted to numbers
                try:
                    item_price = float(item.get("order_price"))
                    item_quantity = int(item.get("order_quantity"))
                    item_total = item_price * item_quantity
                    print(f"Item: {item.get('order_item', 'unknown')} - Price: {item_price} x Quantity: {item_quantity} = {item_total}")
                    total_amount += item_total
                except (ValueError, TypeError) as e:
                    print(f"Error parsing item values: {e}, using defaults")
            
            print(f"Calculated total amount for order {order_id}: {total_amount}")
            
            # Make sure the total amount is greater than zero
            if total_amount <= 0:
                print(f"Warning: Order total is {total_amount}, setting minimum amount of 0.01")
            
            # Prepare payment data
            payment_data = {
                "customer_id": order_data.get("customer_id"),
                "picker_id": new_order.get("picker_id", "none"),  # May be pending so no picker yet
                "order_id": order_id,
                "amount": total_amount
            }
            
            # Call the payment service to process payment
            print(f"Processing payment for order {order_id}, amount: {total_amount}")
            payment_response = requests.post(
                f"{CALC_PAYMENT_SERVICE_URL}/customer/pay",
                json=payment_data
            )
            
            if payment_response.status_code != 200:
                print(f"Payment failed: {payment_response.text}")
                # If payment fails, we should cancel the order
                cancel_response = requests.patch(
                    f"{ORDER_URL}/{order_id}/status",
                    json={"order_status": "cancelled"}
                )
                return jsonify({
                    "error": "Payment failed, order cancelled",
                    "payment_error": payment_response.json()
                }), payment_response.status_code
            
            print(f"Payment successful for order {order_id}")
            
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            # Cancel the order if payment processing failed
            cancel_response = requests.patch(
                f"{ORDER_URL}/{order_id}/status",
                json={"order_status": "cancelled"}
            )
            return jsonify({"error": f"Failed to process payment: {str(e)}, order cancelled"}), 500
        
        # Stores the order data in the pending order dict
        pending_orders[order_id] = new_order
        print(f"Added order {order_id} to pending orders")
        
        # Get customer ID for WebSocket notifications
        customer_id = order_data.get("customer_id")
        if customer_id:
            order_customers[order_id] = customer_id
        
        # Broadcast the new order to pickers
        message = {
            "order_id": order_id,
            "order_data": new_order,
            "type": "new_order"
        }
        
        # Directly emit to all clients via Socket.IO
        socketio.emit(
            WS_ORDER_WAITING,
            {
                "order_id": order_id,
                "status": "pending",
                "details": new_order
            },
            
        )
        print(f"Directly emitted order_waiting event to all clients")
        
        print(f"Publishing to RabbitMQ: {message}")
        publish_to_rabbitmq(message)
        
        # Include payment information in the response
        new_order["payment_processed"] = True
        new_order["amount_paid"] = total_amount
        
        return jsonify(new_order), 201
    
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
        
        # Directly update order via the ORDER API
        order_update = {
            "picker_id": picker_id,
            "order_status": "assigned"
        }
        
        update_response = requests.put(f"{ORDER_URL}/{order_id}", json=order_update)
        
        if update_response.status_code != 200:
            return jsonify({"error": "Failed to update order"}), update_response.status_code
        
        updated_order = update_response.json()
        
        # Publish the acceptance to RabbitMQ
        message = {
            "order_id": order_id,
            "picker_id": picker_id,
            "type": "picker_acceptance"
        }
        
        # Publish to RabbitMQ and handle the event
        if publish_to_rabbitmq(message):
            # Let all the pickers and customer know order is accepted
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
# 9. Order status update endpoint
# =========================================================================
@app.route("/order_status", methods=["POST"])
def update_order_status():
    """Update an order's status and notify relevant parties"""
    try:
        data = request.json
        
        if not data or 'order_id' not in data or 'status' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        order_id = data['order_id']
        new_status = data['status']
        
        # Update the order status in the orders microservice
        status_update = {"order_status": new_status}
        
        if new_status == "completed":
            status_update["order_completed"] = True
            
        status_response = requests.patch(f"{ORDER_URL}/{order_id}/status", json=status_update)
        
        if status_response.status_code != 200:
            return jsonify({"error": "Failed to update order status"}), status_response.status_code
        
        updated_order = status_response.json()
        
        # Notify the customer about the status update
        if order_id in order_customers:
            customer_id = order_customers[order_id]
            
            # Get the full order details
            order_details = get_order_details(order_id)
            
            # Emit the picker update event
            socketio.emit(WS_PICKER_UPDATE, {
                "order_id": order_id,
                "customer_id": customer_id,
                "status": new_status,
                "details": order_details
            })
            
            print(f"Notified clients that order {order_id} status is now {new_status}")
        
        return jsonify({"status": "success", "message": f"Order status updated to {new_status}"}), 200
    
    except Exception as e:
        print(f"Error in update_order_status: {e}")
        return jsonify({"error": str(e)}), 500

# =========================================================================
# 10. Customer cancel order endpoint
# =========================================================================
@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        # Update the order status in the order service
        response = requests.patch(
            f"{ORDER_URL}/{order_id}/status",
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
# 11. Endpoint to get pending orders for picker to see
# =========================================================================
@app.route("/debug/pending_orders", methods=["GET"])
def debug_pending_orders():
    """Return all pending orders (for debugging)"""
    return jsonify({
        "count": len(pending_orders),
        "orders": pending_orders
    })

# =========================================================================
# 12. Endpoint to get active pickers (Not that necessary)
# =========================================================================
@app.route("/debug/active_pickers", methods=["GET"])
def debug_active_pickers():
    """Return all active pickers (for debugging)"""
    return jsonify({
        "count": len(active_pickers),
        "pickers": active_pickers
    })

# =========================================================================
# 13. Websocket endpoints for UI to interact with
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
    
    # Also check for connected_pickers from the WebSocket approach
    for picker_id, sid in list(connected_pickers.items()):
        if sid == request.sid:
            print(f"Removing picker {picker_id} from connected pickers")
            del connected_pickers[picker_id]
            break

# =========================================================================
# 14. Register Picker and Customer and Test via WebSocket
# =========================================================================
@socketio.on(WS_REGISTER_PICKER)
def handle_register_picker(data):
    """Register a picker for receiving order notifications"""
    picker_id = data.get("picker_id")
    if not picker_id:
        return
    
    print(f"Picker {picker_id} registering with socket ID {request.sid}")
    
    # Store in both picker tracking dictionaries for compatibility
    active_pickers[picker_id] = request.sid
    connected_pickers[picker_id] = request.sid
    
    # Send all currently pending orders to this newly connected picker
    print(f"Sending {len(pending_orders)} pending orders to picker {picker_id}")
    
    if pending_orders:
        for order_id, order_data in pending_orders.items():
            print(f"Sending pending order {order_id} to picker {picker_id}")
            # Send directly to this picker only (not broadcast to all)
            socketio.emit(WS_ORDER_WAITING, {
                "order_id": order_id,
                "status": "pending",
                "details": order_data
            }, room=request.sid)
    else:
        print("No pending orders to send")
    
    print(f"Picker {picker_id} registration complete")

@socketio.on(WS_REGISTER_CUSTOMER)
def handle_register_customer(data):
    """Register a customer for updates on their order"""
    customer_id = data.get("customer_id")
    order_id = data.get("order_id")
    
    if customer_id and order_id:
        # Store the customer's session ID for this order
        if customer_id not in customer_orders:
            customer_orders[customer_id] = []
        
        if order_id not in customer_orders[customer_id]:
            customer_orders[customer_id].append(order_id)
        
        # Map order to customer for easier lookup
        order_customers[order_id] = customer_id
        
        print(f"Registered customer {customer_id} for order {order_id}")
        print(f"Customer orders: {customer_orders}")
        print(f"Order customers: {order_customers}")
        
        # Check if order is already assigned to a picker
        try:
            response = requests.get(f"{ORDER_URL}/{order_id}")
            if response.status_code == 200:
                order_data = response.json()
                if order_data.get("order_status") != "pending" and order_data.get("picker_id"):
                    # Send current order information to the customer
                    socketio.emit(WS_PICKER_UPDATE, {
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "picker_id": order_data.get("picker_id"),
                        "status": order_data.get("order_status"),
                        "details": order_data
                    }, room=request.sid)
                    print(f"Sent existing order status to customer for order {order_id}")
        except Exception as e:
            print(f"Error checking order status: {str(e)}")

@socketio.on(WS_TEST_EVENT)
def handle_test_event(data):
    """Handle test event from client"""
    print(f"Received test event: {data}")
    socketio.emit(WS_TEST_RESPONSE, {"message": "Server received your test"}, room=request.sid)

# =========================================================================
# Add a new endpoint to handle order cancellation by a picker
# =========================================================================
@app.route("/order_cancel", methods=["POST"])
def cancel_order_assignment():
    """Cancel a picker's assignment to an order and revert to pending status"""
    try:
        data = request.json
        
        if not data or 'order_id' not in data or 'picker_id' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        order_id = data['order_id']
        picker_id = data['picker_id']
        
        # Check if the order exists and is assigned to this picker
        order_response = requests.get(f"{ORDER_URL}/{order_id}")
        if order_response.status_code != 200:
            return jsonify({"error": "Order not found"}), 404
        
        order_data = order_response.json()
        if str(order_data.get("picker_id")) != str(picker_id):
            return jsonify({"error": "Order not assigned to this picker"}), 403
        
        if order_data.get("order_status") != "assigned":
            return jsonify({"error": "Order cannot be cancelled in its current status"}), 400
        
        # Update the order: set status to pending and remove picker_id
        # Use PATCH to update status and picker_id
        update_data = {
            "order_status": "pending",
            "picker_id": None  # Remove picker assignment
        }
        
        update_response = requests.patch(f"{ORDER_URL}/{order_id}/status", json=update_data)
        if update_response.status_code != 200:
            return jsonify({"error": f"Failed to update order: {update_response.text}"}), 500
        
        # After successful update, fetch the complete order details to ensure all fields are present
        complete_order_response = requests.get(f"{ORDER_URL}/{order_id}")
        if complete_order_response.status_code != 200:
            return jsonify({"error": "Failed to get complete order details"}), 500
            
        updated_order = complete_order_response.json()
        
        # Add this order back to pending orders
        pending_orders[order_id] = updated_order
        
        # Create a message for RabbitMQ
        message = {
            "order_id": order_id,
            "picker_id": picker_id,
            "type": "order_returned_to_pending",
            "order_data": updated_order
        }
        
        # Publish to RabbitMQ
        publish_to_rabbitmq(message)
        
        # Emit multiple events to ensure all components update properly
        
        # 1. Notify all pickers that this order is available again - use order_waiting event
        socketio.emit(WS_ORDER_WAITING, {
            "order_id": order_id,
            "status": "pending",
            "details": updated_order
        })
        
        # 2. Notify customer about the status change
        if order_id in order_customers:
            customer_id = order_customers[order_id]
            
            # Emit customer update with the updated order details
            socketio.emit(WS_PICKER_UPDATE, {
                "order_id": order_id,
                "customer_id": customer_id,
                "status": "pending",  # Make sure this matches the new status
                "details": updated_order
            })
            
            print(f"Notified customer {customer_id} that order {order_id} is now pending again")
        
        print(f"Order {order_id} assignment cancelled by picker {picker_id}, returned to pending status")
        
        return jsonify({
            "status": "success", 
            "message": "Order assignment cancelled",
            "order": updated_order
        }), 200
        
    except Exception as e:
        print(f"Error in cancel_order_assignment: {e}")
        return jsonify({"error": str(e)}), 500

# Test route
@app.route('/test', methods=['GET'])
def test_route():
    return jsonify({"status": "success", "message": "Composite service is running"})

# MAIN
if __name__ == "__main__":
    print("Starting Assign Picker service...")
    # Get port from environment variable or use default 5005
    port = int(os.getenv("PORT", 5005))
    socketio.run(app, debug=True, host="0.0.0.0", port=port)