from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/FoodStallsDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class FoodStall(db.Model):
    __tablename__ = 'FoodStall'

    stall_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stallName = db.Column(db.String(255), nullable=False)
    stallLocation = db.Column(db.String(255), nullable=False)

    menus = db.relationship('FoodMenu', back_populates='stall')

    def __init__(self, stallName, stallLocation):
        self.stallName = stallName
        self.stallLocation = stallLocation

    def json(self):
        return {
            "stallID": self.stallID,
            "stallName": self.stallName,
            "stallLocation": self.stallLocation,
            "menus": [menu.json() for menu in self.menus]
        }

class FoodMenu(db.Model):
    __tablename__ = 'FoodMenu'

    menuID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stallID = db.Column(db.Integer, db.ForeignKey('FoodStall.stallID'), nullable=False)
    menuName = db.Column(db.String(255), nullable=False)
    menuPrice = db.Column(db.Float, nullable=False)

    stall = db.relationship('FoodStall', back_populates='menus')

    def __init__(self, stallID, menuName, menuPrice):
        self.stallID = stallID
        self.menuName = menuName
        self.menuPrice = menuPrice

    def json(self):
        return {
            "menuID": self.menuID,
            "stallID": self.stallID,
            "menuName": self.menuName,
            "menuPrice": self.menuPrice
        }

@app.route("/")

# Add new stall
@app.route("/stall", methods=['POST'])
def add_stall():
    data = request.get_json()
    stallName = data.get('stallName')
    stallLocation = data.get('stallLocation')

    if not stallName or not stallLocation:
        return jsonify(
            {
                "code": 400,
                "message": "Stall name and location are required."
            }
        ), 400

    stall = FoodStall(stallName=stallName, stallLocation=stallLocation)

    try:
        db.session.add(stall)
        db.session.commit()
        return jsonify(
            {
                "code": 201,
                "data": stall.json()
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while adding the stall: {str(e)}"
            }
        ), 500

# Add new item to the menu
@app.route("/stall/<int:stallID>/menu", methods=['POST'])
def add_menu_item(stallID):
    data = request.get_json()
    menuName = data.get('menuName')
    menuPrice = data.get('menuPrice')

    if not menuName or not menuPrice:
        return jsonify(
            {
                "code": 400,
                "message": "Menu name and price are required."
            }
        ), 400

    stall = FoodStall.query.get(stallID)

    if not stall:
        return jsonify(
            {
                "code": 404,
                "message": f"Stall with ID {stallID} not found."
            }
        ), 404

    menu_item = FoodMenu(stallID=stallID, menuName=menuName, menuPrice=menuPrice)

    try:
        db.session.add(menu_item)
        db.session.commit()
        return jsonify(
            {
                "code": 201,
                "data": menu_item.json()
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while adding the menu item: {str(e)}"
            }
        ), 500

# Delete item of the menu from specific stall
@app.route("/stall/<int:stallID>/menu/<int:menuID>", methods=['DELETE'])
def delete_menu_item(stallID, menuID):
    menu_item = FoodMenu.query.filter_by(stallID=stallID, menuID=menuID).first()

    if not menu_item:
        return jsonify(
            {
                "code": 404,
                "message": f"Menu item with ID {menuID} not found at stall {stallID}."
            }
        ), 404

    try:
        db.session.delete(menu_item)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": f"Menu item {menuID} has been deleted."
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while deleting the menu item: {str(e)}"
            }
        ), 500

# Get stall location
@app.route("/stalls/<int:stallID>/stallLocation", methods=['GET'])
def get_stall_location(stallID):
    stall = FoodStall.query.get(stallID)
    if stall:
        return jsonify(
            {
                "code": 200,
                "data": {"stallLocation": stall.stallLocation}
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "message": f"Stall with ID {stallID} not found."
            }
        ), 404

# Get all stalls
@app.route("/stalls", methods=['GET'])
def get_all_stalls():
    stalls = FoodStall.query.all()
    if stalls:
        return jsonify(
            {
                "code": 200,
                "data": [stall.json() for stall in stalls]
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "message": "No stalls found."
            }
        ), 404

# Get menu from specific stall
@app.route("/stalls/<int:stallID>/menu", methods=['GET'])
def get_stall_menu(stallID):
    stall = FoodStall.query.get(stallID)
    if stall:
        return jsonify(
            {
                "code": 200,
                "data": [menu.json() for menu in stall.menus]
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "message": f"Stall with ID {stallID} not found."
            }
        ), 404

# Get details of specific stall
@app.route("/stall/<int:stallID>", methods=['GET'])
def get_stall(stallID):
    stall = FoodStall.query.get(stallID)
    return jsonify({"code": 200, "data": stall.json()}), 200 if stall else ({"code": 404, "message": f"Stall {stallID} not found."}, 404)

# Update specific menu details
@app.route("/stall/<int:stallID>/menu/<int:menuID>", methods=['PUT'])
def update_menu_item(stallID, menuID):
    menu_item = FoodMenu.query.filter_by(stallID=stallID, menuID=menuID).first()
    if not menu_item:
        return jsonify({"code": 404, "message": f"Menu item {menuID} not found."}), 404

    data = request.get_json()
    menu_item.menuName = data.get('menuName', menu_item.menuName)
    menu_item.menuPrice = data.get('menuPrice', menu_item.menuPrice)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": menu_item.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": str(e)}), 500

# Get menu item
@app.route("/stall/<int:stallID>/menu/<int:menuID>", methods=['GET'])
def get_menu_item(stallID, menuID):
    menu_item = FoodMenu.query.filter_by(stallID=stallID, menuID=menuID).first()

    if menu_item:
        return jsonify({"code": 200, "data": menu_item.json()}), 200
    else:
        return jsonify({"code": 404, "message": f"Menu item {menuID} not found in stall {stallID}."}), 404


@app.route("/prepareorder/<int:orderID>", methods=['PUT'])
def prepare_order(orderID):
    
    # This will be replaced with the Docker container link later
    order_microservice_url = f"http://order_microservice_url/orders/{orderID}"

    try:
        response = requests.get(order_microservice_url)
        
        if response.status_code == 404:
            return jsonify({"code": 404, "message": f"Order {orderID} not found."}), 404
        
        order_data = response.json()

        order_data["status"] = "Preparing"

        # THIS ONE NOT YET UPDATED YA GUYS!!!!!!!!!!
        update_response = requests.put(order_microservice_url, json=order_data)

        if update_response.status_code == 200:
            return jsonify({"code": 200, "message": f"Order {orderID} is now being prepared."}), 200
        else:
            return jsonify({"code": 500, "message": "Failed to update order status."}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"code": 500, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)