import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("../../firebase-adminsdk.json")  # Replace with your Firebase JSON key file
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

@app.route("/")
def home():
    return "Food Stall Microservice (Using Firebase Firestore)"

# Get all food stalls
@app.route("/foodstalls", methods=['GET'])
def get_all_foodstalls():
    foodstalls_ref = db.collection('foodstalls')
    docs = foodstalls_ref.stream()
    foodstalls = [doc.to_dict() for doc in docs]

    if foodstalls:
        return jsonify({"code": 200, "data": foodstalls}), 200
    else:
        return jsonify({"code": 404, "message": "No food stalls found."}), 404


# Add a bulk list of food stalls 
@app.route("/foodstalls/add_bulk", methods=['POST'])
def add_bulk_foodstalls():
    foodstalls = [
        {"stallName": "King Kong Curry", "stallLocation": "40 Stamford Road #01-04 SMU Connexion Singapore 178908"},
        {"stallName": "Triplets Waffle", "stallLocation": "70 Stamford Road #B1-24A Li Ka Shing Library Building, Singapore 178901"},
        {"stallName": "Khoon", "stallLocation": "90 Stamford Road #01-72 School of Economics / School of Computing and Information Systems 2 Building Singapore 178903"},
        {"stallName": "Canteen Bistro", "stallLocation": "80 Stamford Road #B1-61 School of Computing and Information Systems Building, Singapore 178902"}
    ]

    counter_ref = db.collection('metadata').document('foodstall_counter')  # Counter for stall ID
    foodstall_collection = db.collection('foodstalls')  # Food stalls collection

    counter_doc = counter_ref.get()

    if counter_doc.exists:
        count = counter_doc.to_dict().get("count", 0)
    else:
        
        counter_ref.set({"count": 0})
        count = 0

    # Set the starting ID and update the counter
    start_id = count
    new_count = start_id + len(foodstalls)
    
    # Update the counter in the metadata collection
    counter_ref.update({"count": new_count})

    # Process food stalls, assigning each a unique ID
    for i, foodstall in enumerate(foodstalls):
        stall_id = str(start_id + i + 1)  # Generate a new unique ID
        foodstall_collection.document(stall_id).set(foodstall)  # Set the food stall in Firestore

    return jsonify({"code": 201, "message": "Bulk food stalls added successfully!"}), 201

# Get all food menus for a specific food stall
@app.route("/foodstalls/<stall_id>/foodmenus", methods=['GET'])
def get_foodmenus_for_stall(stall_id):
    foodmenus_ref = db.collection('foodstalls').document(stall_id).collection('foodmenus')
    docs = foodmenus_ref.stream()
    foodmenus = [doc.to_dict() for doc in docs]

    if foodmenus:
        return jsonify({"code": 200, "data": foodmenus}), 200
    else:
        return jsonify({"code": 404, "message": "No food menus found for this stall."}), 404

# Add a bulk list of food menus for a specific food stall 
@app.route("/foodstall/<foodstall_id>/add_bulk_foodmenus", methods=['POST'])
def add_bulk_foodmenus(foodstall_id):
    foodmenus = {
        "1": [
            {"menuName": "Fresh Milk Cheese Omelette Curry Rice", "menuPrice": 6.0},
            {"menuName": "Original Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Mayo Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Spicy Mayo Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Cheese Mayo Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Black Vinegar Mayo Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Tartar Mayo Chicken Katsu Curry Rice", "menuPrice": 6.0},
            {"menuName": "Truffle Mayo Curry Rice", "menuPrice": 6.0},
            {"menuName": "Fish Katsu Curry Rice", "menuPrice": 6.5},
            {"menuName": "Salmon Katsu Curry Rice", "menuPrice": 7.0},
            {"menuName": "Ebi Katsu Curry Rice", "menuPrice": 7.0},
            {"menuName": "Takoyaki Curry Rice", "menuPrice": 6.5}
        ],
        "2": [
            {"menuName": "Plain Waffle", "menuPrice": 1.8},
            {"menuName": "Peanut Waffle", "menuPrice": 2.3},
            {"menuName": "Chocolate Waffle", "menuPrice": 2.3},
            {"menuName": "Kaya Waffle", "menuPrice": 2.3},
            {"menuName": "Cream Cheese Waffle", "menuPrice": 2.3},
            {"menuName": "Strawberry Waffle", "menuPrice": 2.3},
            {"menuName": "Blueberry Waffle", "menuPrice": 2.3},
            {"menuName": "Slice Cheese Waffle", "menuPrice": 2.3},
            {"menuName": "Crunchy Peanut Waffle", "menuPrice": 2.8},
            {"menuName": "Chocolate Oreo Waffle", "menuPrice": 2.8},
            {"menuName": "Walnut Chocolate Waffle", "menuPrice": 2.8},
            {"menuName": "Almond Chocolate Waffle", "menuPrice": 2.8},
            {"menuName": "Chicken Ham & Cheese Waffle", "menuPrice": 2.8},
            {"menuName": "Oreo Cheese Waffle", "menuPrice": 2.8},
            {"menuName": "Blueberry Cheese Waffle", "menuPrice": 2.8},
            {"menuName": "Cranberry Cheese Waffle", "menuPrice": 2.8},
            {"menuName": "Redbean Waffle", "menuPrice": 2.8}
        ],
        "3": [
            {"menuName": "Plain Waffle", "menuPrice": 1.0},
            {"menuName": "Kaya Waffle", "menuPrice": 2.0},
            {"menuName": "Butter Waffle", "menuPrice": 2.0},
            {"menuName": "Honey Waffle", "menuPrice": 2.0},
            {"menuName": "Chocolate Waffle", "menuPrice": 2.2},
            {"menuName": "Peanut Butter Waffle", "menuPrice": 2.2},
            {"menuName": "Sliced Cheese Waffle", "menuPrice": 2.2},
            {"menuName": "Biscoff Waffle", "menuPrice": 2.8},
            {"menuName": "Tater Tots", "menuPrice": 2.5},
            {"menuName": "Kaya Bun", "menuPrice": 2.2},
            {"menuName": "Chocolate Bun", "menuPrice": 2.2},
            {"menuName": "Peanut Butter Bun", "menuPrice": 2.2},
            {"menuName": "Honey Butter Bun", "menuPrice": 2.4},
            {"menuName": "Sweet Milk Bun", "menuPrice": 2.2},
            {"menuName": "Biscoff Bun", "menuPrice": 2.8},
            {"menuName": "Mushroom Vegan Baked Rice Set", "menuPrice": 4.4},
            {"menuName": "Chicken Sausage Baked Rice Set", "menuPrice": 5.5},
            {"menuName": "Chicken Sausage Burger with Egg", "menuPrice": 4.4},
            {"menuName": "Chicken Sausage Burger with Egg Set", "menuPrice": 6.5}
        ],
        "4": [
            {"menuName": "Fries", "menuPrice": 6.0},
            {"menuName": "Cheese Fries", "menuPrice": 8.0},
            {"menuName": "Truffle Fries", "menuPrice": 12.0},
            {"menuName": "Pulled Pork Fries", "menuPrice": 12.0},
            {"menuName": "Vongole", "menuPrice": 12.0},
            {"menuName": "Fried Chicken Wings", "menuPrice": 15.0},
            {"menuName": "Fried Calamari", "menuPrice": 15.0},
            {"menuName": "Tempura Prawns", "menuPrice": 15.0},
            {"menuName": "Combo Platter", "menuPrice": 26.0},
            {"menuName": "Crispy Chicken", "menuPrice": 14.0},
            {"menuName": "Crispy Fish", "menuPrice": 14.0},
            {"menuName": "Pulled Pork", "menuPrice": 16.0},
            {"menuName": "Wagyu Beef", "menuPrice": 18.0},
            {"menuName": "Grilled Chicken Chop", "menuPrice": 13.0},
            {"menuName": "Crispy Chicken Cutlet", "menuPrice": 13.0},
            {"menuName": "Fish & Chips", "menuPrice": 13.0},
            {"menuName": "Pan-Seared Salmon", "menuPrice": 18.0},
            {"menuName": "Creamy Salmon Linguine", "menuPrice": 15.0},
            {"menuName": "Creamy Meatball Linguine", "menuPrice": 15.0},
            {"menuName": "Vongole Linguine", "menuPrice": 15.0},
            {"menuName": "Mushroom Aglio Olio Linguine", "menuPrice": 15.0}
        ]
    }

    foodstall_id = str(foodstall_id)  

    if foodstall_id not in foodmenus:
        return {"error": "Invalid foodstall_id"}, 400

    foodmenu_collection = db.collection('foodstalls').document(foodstall_id).collection('foodmenus')
    batch = db.batch()  # Start a batch write

    for menu in foodmenus[foodstall_id]:  # Only process the requested foodstall_id
        doc_ref = foodmenu_collection.document()
        batch.set(doc_ref, menu)

    batch.commit()  # Commit the batch write

    return {"message": f"Bulk food menus added for foodstall {foodstall_id}"}, 200

# Add a food stall
@app.route("/foodstall", methods=['POST'])
def add_foodstall():
    data = request.get_json()
    stall_name = data.get('stallName')
    stall_location = data.get('stallLocation')

    if not stall_name or not stall_location:
        return jsonify({"code": 400, "message": "Both stallName and stallLocation are required."}), 400

    # Reference to metadata counter
    counter_ref = db.collection('metadata').document('foodstall_counter')
    foodstall_collection = db.collection('foodstalls')

    counter_doc = counter_ref.get()

    if counter_doc.exists:
        count = counter_doc.to_dict().get("count", 0)
    else:
        counter_ref.set({"count": 0})  # Initialize counter if not found
        count = 0

    new_stall_id = str(count + 1)  # Generate new stall ID

    # Store the new food stall
    foodstall_collection.document(new_stall_id).set({
        "stallName": stall_name,
        "stallLocation": stall_location
    })

    # Update the counter
    counter_ref.update({"count": count + 1})

    return jsonify({"code": 201, "message": "Food stall added successfully!", "stallID": new_stall_id}), 201


# Get a food stall by ID
@app.route("/foodstall/<stall_id>", methods=['GET'])
def get_foodstall_by_id(stall_id):
    foodstall_ref = db.collection('foodstalls').document(stall_id)
    foodstall = foodstall_ref.get()

    if foodstall.exists:
        return jsonify({"code": 200, "data": foodstall.to_dict()}), 200
    else:
        return jsonify({"code": 404, "message": "Food stall not found."}), 404
    
# Add menu to a specific food stall
@app.route("/foodstalls/<stall_id>/foodmenus", methods=['POST'])
def add_menu_to_foodstall(stall_id):
    data = request.get_json()
    menu_name = data.get('menuName')
    menu_price = data.get('menuPrice')

    if not menu_name or not menu_price:
        return jsonify({"code": 400, "message": "Both menuName and menuPrice are required."}), 400

    menu_data = {
        "menuName": menu_name,
        "menuPrice": menu_price,
    }

    foodmenu_ref = db.collection('foodstalls').document(stall_id).collection('foodmenus').add(menu_data)

    return jsonify({"code": 201, "message": "Menu item added successfully!"}), 201


# Delete a specific food menu by ID
@app.route("/foodstalls/<stall_id>/foodmenus/<food_id>", methods=['DELETE'])
def delete_food_menu(stall_id, food_id):
    # Get a reference to the specific menu document
    menu_ref = db.collection('foodstalls').document(stall_id).collection('foodmenus').document(food_id)
    
    # Check if the document exists before trying to delete it
    if menu_ref.get().exists:
        menu_ref.delete()  # Delete the document
        return jsonify({"code": 200, "message": "Menu item deleted successfully!"}), 200
    else:
        return jsonify({"code": 404, "message": "Menu item not found."}), 404

# Delete a food stall by ID
@app.route("/foodstalls/<stall_id>", methods=['DELETE'])
def delete_foodstall(stall_id):
    foodstall_ref = db.collection('foodstalls').document(stall_id)
    foodstall = foodstall_ref.get()

    if foodstall.exists:
        foodstall_ref.delete()
        return jsonify({"code": 200, "message": "Food stall deleted successfully!"}), 200
    else:
        return jsonify({"code": 404, "message": "Food stall not found."}), 404

if __name__ == "__main__":
    app.run(debug=True)
