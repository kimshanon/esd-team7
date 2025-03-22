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
    
db_path = os.path.join(db_dir, 'main.db')

# Configure SQLAlchemy to use a SQLite database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class FoodStall(db.Model):
    stall_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stall_name = db.Column(db.String(100), nullable=False)
    stall_location = db.Column(db.String(100), nullable=False)
    # Relationship to FoodItem; cascade delete to remove associated menu items.
    stall_menu = db.relationship('FoodItem', backref='food_stall', cascade="all, delete-orphan", lazy=True)

    def as_dict(self):
        return {
            "stall_id": self.stall_id,
            "stall_name": self.stall_name,
            "stall_location": self.stall_location,
            "stall_menu": [item.as_dict() for item in self.stall_menu]
        }

class FoodItem(db.Model):
    food_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('food_stall.stall_id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    food_description = db.Column(db.String(200), nullable=True)
    food_price = db.Column(db.Float, nullable=False)

    def as_dict(self):
        return {
            "food_id": self.food_id,
            "stall_id": self.stall_id,
            "food_name": self.food_name,
            "food_description": self.food_description,
            "food_price": self.food_price
        }

with app.app_context():
    db.create_all()

# -------- Food Stall Endpoints --------

# GET all food stalls with their menus.
@app.route('/stalls', methods=['GET'])
def get_stalls():
    stalls = FoodStall.query.all()
    return jsonify([stall.as_dict() for stall in stalls]), 200

# GET a specific food stall by stall_id.
@app.route('/stalls/<int:stall_id>', methods=['GET'])
def get_stall(stall_id):
    stall = FoodStall.query.get(stall_id)
    if not stall:
        abort(404, description="Food stall not found")
    return jsonify(stall.as_dict()), 200

# POST to create a new food stall.
@app.route('/stalls', methods=['POST'])
def create_stall():
    if not request.json or not all(key in request.json for key in ['stall_name', 'stall_location']):
        abort(400, description="Missing required stall fields")
    new_stall = FoodStall(
        stall_name=request.json['stall_name'],
        stall_location=request.json['stall_location']
    )
    db.session.add(new_stall)
    db.session.commit()
    return jsonify(new_stall.as_dict()), 201

# PUT to update an existing food stall.
@app.route('/stalls/<int:stall_id>', methods=['PUT'])
def update_stall(stall_id):
    stall = FoodStall.query.get(stall_id)
    if not stall:
        abort(404, description="Food stall not found")
    if not request.json:
        abort(400, description="Missing request body")
    stall.stall_name = request.json.get('stall_name', stall.stall_name)
    stall.stall_location = request.json.get('stall_location', stall.stall_location)
    db.session.commit()
    return jsonify(stall.as_dict()), 200

# DELETE a food stall (and its associated menu items).
@app.route('/stalls/<int:stall_id>', methods=['DELETE'])
def delete_stall(stall_id):
    stall = FoodStall.query.get(stall_id)
    if not stall:
        abort(404, description="Food stall not found")
    db.session.delete(stall)
    db.session.commit()
    return jsonify({"message": f"Food stall {stall_id} deleted"}), 200

# -------- Food Menu Endpoints --------

# GET all food items for a specific stall.
@app.route('/stalls/<int:stall_id>/menu', methods=['GET'])
def get_menu(stall_id):
    stall = FoodStall.query.get(stall_id)
    if not stall:
        abort(404, description="Food stall not found")
    return jsonify([item.as_dict() for item in stall.stall_menu]), 200

# POST to add multiple food items to a stall's menu.
@app.route('/stalls/<int:stall_id>/menu', methods=['POST'])
def add_multiple_menu_items(stall_id):
    stall = FoodStall.query.get(stall_id)
    if not stall:
        abort(404, description="Food stall not found")
    
    # Ensure the request JSON is a list.
    if not request.json or not isinstance(request.json, list):
        abort(400, description="Expected a JSON list of food items")
    
    new_items = []
    for item in request.json:
        # Validate required fields for each food item.
        if 'food_name' not in item or 'food_price' not in item:
            abort(400, description="Each food item must include 'food_name' and 'food_price'")
        
        new_food = FoodItem(
            stall_id=stall_id,
            food_name=item['food_name'],
            food_description=item.get('food_description', ''),
            food_price=item['food_price']
        )
        db.session.add(new_food)
        new_items.append(new_food)
    
    db.session.commit()
    return jsonify([food.as_dict() for food in new_items]), 201

# PUT to update an existing food item for a stall.
@app.route('/stalls/<int:stall_id>/menu/<int:food_id>', methods=['PUT'])
def update_menu_item(stall_id, food_id):
    food_item = FoodItem.query.filter_by(food_id=food_id, stall_id=stall_id).first()
    if not food_item:
        abort(404, description="Menu item not found for this stall")
    if not request.json:
        abort(400, description="Missing request body")
    food_item.food_name = request.json.get('food_name', food_item.food_name)
    food_item.food_description = request.json.get('food_description', food_item.food_description)
    food_item.food_price = request.json.get('food_price', food_item.food_price)
    db.session.commit()
    return jsonify(food_item.as_dict()), 200

# DELETE a food item from a stall's menu.
@app.route('/stalls/<int:stall_id>/menu/<int:food_id>', methods=['DELETE'])
def delete_menu_item(stall_id, food_id):
    food_item = FoodItem.query.filter_by(food_id=food_id, stall_id=stall_id).first()
    if not food_item:
        abort(404, description="Menu item not found for this stall")
    db.session.delete(food_item)
    db.session.commit()
    return jsonify({"message": f"Menu item {food_id} deleted from stall {stall_id}"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)
