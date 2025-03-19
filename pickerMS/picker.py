from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/PickerDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Picker(db.Model):
    __tablename__ = 'Picker'

    pickerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pickerName = db.Column(db.String(100), nullable=False)
    pickerPhone = db.Column(db.String(20), nullable=False)
    pickerStatus = db.Column(db.String(50), nullable=False, default='Available')

    def __init__(self, pickerName, pickerPhone, pickerStatus='Available'):
        self.pickerName = pickerName
        self.pickerPhone = pickerPhone
        self.pickerStatus = pickerStatus

    def json(self):
        return {
            "pickerID": self.pickerID,
            "pickerName": self.pickerName,
            "pickerPhone": self.pickerPhone,
            "pickerStatus": self.pickerStatus
        }

@app.route("/")
def home():
    return "Picker Microservice"

# Get all pickers
@app.route("/pickers", methods=['GET'])
def get_all_pickers():
    pickers = Picker.query.all()
    if pickers:
        return jsonify(
            {
                "code": 200,
                "data": [picker.json() for picker in pickers]
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "message": "No pickers found."
            }
        ), 404

# Get specific picker
@app.route("/pickers/<int:pickerID>", methods=['GET'])
def get_picker(pickerID):
    picker = Picker.query.get(pickerID)
    return jsonify({"code": 200, "data": picker.json()}), 200 if picker else (
        {"code": 404, "message": f"Picker {pickerID} not found."}, 404)

# Add new picker
@app.route("/picker", methods=['POST'])
def add_picker():
    data = request.get_json()
    pickerName = data.get('pickerName')
    pickerPhone = data.get('pickerPhone')
    pickerStatus = data.get('pickerStatus', 'Available')  # Default status if not provided

    if not pickerName or not pickerPhone:
        return jsonify(
            {
                "code": 400,
                "message": "Picker name and phone are required."
            }
        ), 400

    picker = Picker(pickerName=pickerName, pickerPhone=pickerPhone, pickerStatus=pickerStatus)

    try:
        db.session.add(picker)
        db.session.commit()
        return jsonify(
            {
                "code": 201,
                "data": picker.json()
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while adding the picker: {str(e)}"
            }
        ), 500

# Update picker status to available after pciker cancels
@app.route("/picker/<int:pickerID>/status", methods=['PUT'])
def update_picker_status(pickerID):
    picker = Picker.query.get(pickerID)
    if not picker:
        return jsonify(
            {
                "code": 404,
                "message": f"Picker with ID {pickerID} not found."
            }
        ), 404

    data = request.get_json()
    new_status = data.get('pickerStatus')
    
    if not new_status:
        return jsonify(
            {
                "code": 400,
                "message": "Picker status is required."
            }
        ), 400
    
    try:
        picker.pickerStatus = new_status
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": f"Picker {pickerID} status updated to {new_status}.",
                "data": picker.json()
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while updating the picker status: {str(e)}"
            }
        ), 500

# Confirm an order -- not confirmed cos this requires order microservice which i do not have in the database right now
# @app.route("/confirmorder/<int:orderID>", methods=['PUT'])
# def confirm_order(orderID):
#     data = request.get_json()
#     pickerID = data.get('pickerID')
    
#     if not pickerID:
#         return jsonify(
#             {
#                 "code": 400,
#                 "message": "Picker ID is required."
#             }
#         ), 400
    
#     # Check if picker exists
#     picker = Picker.query.get(pickerID)
#     if not picker:
#         return jsonify(
#             {
#                 "code": 404,
#                 "message": f"Picker with ID {pickerID} not found."
#             }
#         ), 404
    
#     # Check if picker is available
#     if picker.pickerStatus != 'Available':
#         return jsonify(
#             {
#                 "code": 400,
#                 "message": f"Picker {pickerID} is not available. Current status: {picker.pickerStatus}"
#             }
#         ), 400
    
#     # In a microservice architecture, we'd communicate with the Order service
#     # to update the order status. Here's a placeholder for that logic:
#     try:
#         # This would be replaced with actual service communication
#         # e.g., using requests to call the Order microservice API
        
#         # Update picker status to Busy since they're now handling an order
#         picker.pickerStatus = 'Busy'
#         db.session.commit()
        
#         # Placeholder for successful response
#         return jsonify(
#             {
#                 "code": 200,
#                 "message": f"Order {orderID} confirmed successfully with picker {pickerID}.",
#                 "data": {
#                     "orderID": orderID,
#                     "pickerID": pickerID,
#                     "pickerStatus": picker.pickerStatus,
#                     "status": "confirmed"
#                 }
#             }
#         ), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify(
#             {
#                 "code": 500,
#                 "message": f"An error occurred while confirming the order: {str(e)}"
#             }
#         ), 500

# Delete a picker
@app.route("/picker/<int:pickerID>", methods=['DELETE'])
def delete_picker(pickerID):
    picker = Picker.query.get(pickerID)
    if not picker:
        return jsonify(
            {
                "code": 404,
                "message": f"Picker with ID {pickerID} not found."
            }
        ), 404

    try:
        db.session.delete(picker)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": f"Picker {pickerID} has been deleted."
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while deleting the picker: {str(e)}"
            }
        ), 500

# Update a picker (full update)
@app.route("/picker/<int:pickerID>", methods=['PUT'])
def update_picker(pickerID):
    picker = Picker.query.get(pickerID)
    if not picker:
        return jsonify(
            {
                "code": 404,
                "message": f"Picker with ID {pickerID} not found."
            }
        ), 404

    data = request.get_json()
    pickerName = data.get('pickerName')
    pickerPhone = data.get('pickerPhone')
    pickerStatus = data.get('pickerStatus')

    if not pickerName or not pickerPhone or not pickerStatus:
        return jsonify(
            {
                "code": 400,
                "message": "Picker name, phone, and status are all required for a full update."
            }
        ), 400

    try:
        picker.pickerName = pickerName
        picker.pickerPhone = pickerPhone
        picker.pickerStatus = pickerStatus
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": f"Picker {pickerID} has been updated.",
                "data": picker.json()
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while updating the picker: {str(e)}"
            }
        ), 500

# Get available pickers after picker cancels?
@app.route("/pickers/available", methods=['GET'])
def get_available_pickers():
    pickers = Picker.query.filter_by(pickerStatus='Available').all()
    if pickers:
        return jsonify(
            {
                "code": 200,
                "data": [picker.json() for picker in pickers]
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "message": "No available pickers found."
            }
        ), 404

if __name__ == '__main__':
    app.run(port=5001, debug=True)