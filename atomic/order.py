import os
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Build the database path. Assuming the following structure:
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, '..', 'database')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
db_path = os.path.join(db_dir, 'main.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------
# Models
# ---------------------------

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    picker_id = db.Column(db.Integer, nullable=False)
    store_id = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    order_location = db.Column(db.String(255), nullable=False)
    order_start = db.Column(db.DateTime, nullable=False)
    order_completed = db.Column(db.DateTime, nullable=True)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    # Relationship to OrderItem
    order_items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan", lazy=True)

    def as_dict(self):
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "picker_id": self.picker_id,
            "store_id": self.store_id,
            "order_status": self.order_status,
            "order_location": self.order_location,
            "order_start": self.order_start.isoformat() if self.order_start else None,
            "order_completed": self.order_completed.isoformat() if self.order_completed else None,
            "is_paid": self.is_paid,
            "order_items": [item.as_dict() for item in self.order_items]
        }

class OrderItem(db.Model):
    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    order_item = db.Column(db.String(100), nullable=False)
    order_quantity = db.Column(db.Integer, nullable=False)
    order_price = db.Column(db.Float, nullable=False)

    def as_dict(self):
        return {
            "order_item_id": self.order_item_id,
            "order_item": self.order_item,
            "order_quantity": self.order_quantity,
            "order_price": self.order_price
        }

with app.app_context():
    db.create_all()

# ---------------------------
# Endpoints
# ---------------------------

# GET all orders
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([order.as_dict() for order in orders]), 200

# GET a specific order by order_id
@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        abort(404, description="Order not found")
    return jsonify(order.as_dict()), 200

# POST create a new order (with multiple order items)
@app.route('/orders', methods=['POST'])
def create_order():
    if not request.json:
        abort(400, description="Missing JSON body")
    data = request.json
    # Validate required fields for the order
    required_fields = ['customer_id', 'picker_id', 'store_id', 'order_status', 'order_location', 'order_start', 'is_paid']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing required field: {field}")

    # Parse datetime values from ISO format strings
    try:
        order_start = datetime.fromisoformat(data['order_start'])
    except Exception:
        abort(400, description="Invalid order_start format. Use ISO format (e.g., '2025-03-18T12:34:56').")
    
    order_completed = None
    if 'order_completed' in data and data['order_completed']:
        try:
            order_completed = datetime.fromisoformat(data['order_completed'])
        except Exception:
            abort(400, description="Invalid order_completed format. Use ISO format.")

    new_order = Order(
        customer_id=data['customer_id'],
        picker_id=data['picker_id'],
        store_id=data['store_id'],
        order_status=data['order_status'],
        order_location=data['order_location'],
        order_start=order_start,
        order_completed=order_completed,
        is_paid=data['is_paid']
    )

    # Validate and process order_items
    if 'order_items' not in data or not isinstance(data['order_items'], list):
        abort(400, description="Missing or invalid order_items; expected a list.")
    
    for item in data['order_items']:
        if 'order_item' not in item or 'order_quantity' not in item or 'order_price' not in item:
            abort(400, description="Each order item must include 'order_item','order_quantity' and 'order_price.")
        new_item = OrderItem(
            order_item=item['order_item'],
            order_quantity=item['order_quantity'],
            order_price=item['order_price']
        )
        new_order.order_items.append(new_item)

    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.as_dict()), 201

# PUT update an existing order
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        abort(404, description="Order not found")
    data = request.json
    if not data:
        abort(400, description="Missing JSON body")

    # Update basic order fields if provided
    if 'customer_id' in data:
        order.customer_id = data['customer_id']
    if 'picker_id' in data:
        order.picker_id = data['picker_id']
    if 'store_id' in data:
        order.store_id = data['store_id']
    if 'order_status' in data:
        order.order_status = data['order_status']
    if 'order_location' in data:
        order.order_location = data['order_location']
    if 'order_start' in data:
        try:
            order.order_start = datetime.fromisoformat(data['order_start'])
        except Exception:
            abort(400, description="Invalid order_start format. Use ISO format.")
    if 'order_completed' in data:
        if data['order_completed']:
            try:
                order.order_completed = datetime.fromisoformat(data['order_completed'])
            except Exception:
                abort(400, description="Invalid order_completed format. Use ISO format.")
        else:
            order.order_completed = None
    if 'is_paid' in data:
        order.is_paid = data['is_paid']

    # Update order_items if provided: here, we'll assume a full replacement of order_items.
    if 'order_items' in data:
        # Remove existing order items
        for item in order.order_items:
            db.session.delete(item)
        order.order_items = []
        if not isinstance(data['order_items'], list):
            abort(400, description="order_items should be a list")
        for item in data['order_items']:
            if 'order_item' not in item or 'order_quantity' not in item:
                abort(400, description="Each order item must include 'order_item' and 'order_quantity'")
            new_item = OrderItem(
                order_item=item['order_item'],
                order_quantity=item['order_quantity']
            )
            order.order_items.append(new_item)

    db.session.commit()
    return jsonify(order.as_dict()), 200

# DELETE an order by order_id
@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        abort(404, description="Order not found")
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": f"Order {order_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5004)
