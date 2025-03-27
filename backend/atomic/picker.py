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

# Configure SQLAlchemy to use a SQLite database called picker.db.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Picker(db.Model):
    picker_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    picker_name = db.Column(db.String(80), nullable=False)
    picker_email = db.Column(db.String(120), nullable=False)
    picker_phone = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)

    def as_dict(self):
        return {
            "picker_id": self.picker_id,
            "picker_name": self.picker_name,
            "picker_email": self.picker_email,
            "picker_phone": self.picker_phone,
            "is_available": self.is_available
        }

with app.app_context():
    db.create_all()

# GET all pickers
@app.route('/pickers', methods=['GET'])
def get_pickers():
    pickers = Picker.query.all()
    return jsonify([picker.as_dict() for picker in pickers]), 200

# GET a specific picker by picker_id
@app.route('/pickers/<int:picker_id>', methods=['GET'])
def get_picker(picker_id):
    picker = Picker.query.get(picker_id)
    if not picker:
        abort(404, description="Picker not found")
    return jsonify(picker.as_dict()), 200

# POST create a new picker
@app.route('/pickers', methods=['POST'])
def create_picker():
    if not request.json or not all(key in request.json for key in ['picker_name', 'picker_email', 'picker_phone', 'is_available']):
        abort(400, description="Missing required picker fields")
    
    new_picker = Picker(
        picker_name=request.json['picker_name'],
        picker_email=request.json['picker_email'],
        picker_phone=request.json['picker_phone'],
        is_available=request.json['is_available']
    )
    db.session.add(new_picker)
    db.session.commit()
    return jsonify(new_picker.as_dict()), 201

# PUT update an existing picker
@app.route('/pickers/<int:picker_id>', methods=['PUT'])
def update_picker(picker_id):
    picker = Picker.query.get(picker_id)
    if not picker:
        abort(404, description="Picker not found")
    if not request.json:
        abort(400, description="Missing request body")
    
    picker.picker_name = request.json.get('picker_name', picker.picker_name)
    picker.picker_email = request.json.get('picker_email', picker.picker_email)
    picker.picker_phone = request.json.get('picker_phone', picker.picker_phone)
    picker.is_available = request.json.get('is_available', picker.is_available)
    
    db.session.commit()
    return jsonify(picker.as_dict()), 200

# DELETE a picker by picker_id
@app.route('/pickers/<int:picker_id>', methods=['DELETE'])
def delete_picker(picker_id):
    picker = Picker.query.get(picker_id)
    if not picker:
        abort(404, description="Picker not found")
    db.session.delete(picker)
    db.session.commit()
    return jsonify({"message": f"Picker {picker_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)
