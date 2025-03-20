from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Get the directory of the current file.
basedir = os.path.abspath(os.path.dirname(__file__))
# Build the path to the "database" folder.
db_dir = os.path.join(basedir, '..', 'database')
# Ensure the "database" folder exists.
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Build the full path to the main.db file.
db_path = os.path.join(db_dir, 'main.db')

# Configure the database URI using the absolute path.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Customer model with snake_case field names.
class Customer(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(80), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.Integer, nullable=False)

    def as_dict(self):
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_email": self.customer_email
        }

# Create the database and tables if they don't exist.
with app.app_context():
    db.create_all()

# GET all customers.
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.as_dict() for customer in customers]), 200

# GET a specific customer by customer_id.
@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        abort(404, description="Customer not found")
    return jsonify(customer.as_dict()), 200

# POST a new customer.
@app.route('/customers', methods=['POST'])
def create_customer():
    if not request.json or not all(key in request.json for key in ['customer_name', 'customer_phone', 'customer_email']):
        abort(400, description="Missing required customer fields")
    
    new_customer = Customer(
        customer_name=request.json['customer_name'],
        customer_phone=request.json['customer_phone'],
        customer_email=request.json['customer_email']
    )
    db.session.add(new_customer)
    db.session.commit()

    return jsonify(new_customer.as_dict()), 201

# PUT update an existing customer.
@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        abort(404, description="Customer not found")
    if not request.json:
        abort(400, description="Missing request body")
    
    customer.customer_name = request.json.get('customer_name', customer.customer_name)
    customer.customer_phone = request.json.get('customer_phone', customer.customer_phone)
    customer.customer_email = request.json.get('customer_email', customer.customer_email)
    
    db.session.commit()
    return jsonify(customer.as_dict()), 200

# DELETE a customer by customer_id.
@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        abort(404, description="Customer not found")
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Customer {customer_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
