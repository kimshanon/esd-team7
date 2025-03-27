from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import pika
import json
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# RabbitMQ settings
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "order_assignment_exchange"
EXCHANGE_TYPE = "fanout"


def rabbitmq_listener():
    """
    Background thread that listens for messages from RabbitMQ.
    It specifically looks for 'picker_acceptance' messages and then emits a WebSocket event.
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

    # Declare a temporary queue for this listener
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        msg_type = message.get("type")
        if msg_type == "picker_acceptance":
            order_id = message.get("order_id")
            picker_id = message.get("picker_id")
            # Emit an event to notify the customer UI
            socketio.emit(
                "picker_update",
                {
                    "order_id": order_id,
                    "picker_id": picker_id,
                    "status": "Picker Accepted",
                },
                broadcast=True,
            )
        elif msg_type == "new_order":
            order_id = message.get("order_id")
            # Emit an event to notify the picker UI that an order is waiting
            socketio.emit(
                "order_waiting",
                {"order_id": order_id, "status": "Order waiting for acceptance"},
            )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


# Start the RabbitMQ listener in a background thread.
threading.Thread(target=rabbitmq_listener, daemon=True).start()

@app.route("/assign_order", methods=["POST"])
def assign_order():
    """
    HTTP endpoint that the customer calls when placing a new order.
    It broadcasts the new order to available pickers via RabbitMQ.
    """
    data = request.get_json()
    if not data or "order_id" not in data:
        return jsonify({"error": "Missing order_id in request data"}), 400

    order_id = data["order_id"]

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)
        # Publish a message indicating a new order is available
        message = json.dumps({"order_id": order_id, "type": "new_order"})
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", body=message)
        connection.close()
    except Exception as e:
        return jsonify({"error": f"Failed to publish order message: {str(e)}"}), 500

    # Respond immediately to the customer
    return (
        jsonify({"message": "Order broadcast sent. Waiting for picker acceptance."}),
        200,
    )


@app.route("/picker_accept", methods=["POST"])
def picker_accept():
    """
    Endpoint for a picker to accept an order.
    Expects JSON with 'order_id' and 'picker_id'.
    Publishes a 'picker_acceptance' message to the exchange.
    """
    data = request.get_json()
    if not data or "order_id" not in data or "picker_id" not in data:
        return (
            jsonify({"error": "Missing required fields: order_id and picker_id"}),
            400,
        )

    order_id = data["order_id"]
    picker_id = data["picker_id"]

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)
        message = json.dumps(
            {"order_id": order_id, "picker_id": picker_id, "type": "picker_acceptance"}
        )
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", body=message)
        connection.close()
    except Exception as e:
        return jsonify({"error": f"Failed to publish acceptance: {str(e)}"}), 500

    return jsonify({"message": "Picker acceptance sent."}), 200


@socketio.on("connect")
def handle_connect():
    print("Customer connected via WebSocket.")


if __name__ == "__main__":
    # Run the service with SocketIO support on port 5005
    socketio.run(app, port=5005, debug=True)
