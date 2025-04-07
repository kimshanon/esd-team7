from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import ValidationError
from models.stall_model import StallModel, MenuItemModel

load_dotenv()  # Loads the .env file

# Initialize Firebase (if not already initialized)
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Set the Firestore DB client.
db = firestore.client()

app = Flask(__name__)
CORS(app)

# TEST
@app.route('/test', methods=['GET'])
def test():
    return "Stall MS is running"

# GET all food stalls with their menus.
@app.route("/stalls", methods=["GET"])
def get_stalls():
    stalls_ref = db.collection("stalls")
    docs = stalls_ref.stream()
    stalls = []
    for doc in docs:
        stall_data = doc.to_dict()
        stall_data["id"] = doc.id
        # Retrieve menu items as documents in the subcollection "menu".
        menu_docs = doc.reference.collection("menu").stream()
        menu_items = []
        for menu_doc in menu_docs:
            menu_item = menu_doc.to_dict()
            menu_item["id"] = menu_doc.id
            menu_items.append(menu_item)
        stall_data["menu"] = menu_items
        stalls.append(stall_data)
    return jsonify(stalls), 200


# GET a specific food stall by stall_id.
@app.route("/stalls/<stall_id>", methods=["GET"])
def get_stall(stall_id):
    doc_ref = db.collection("stalls").document(stall_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Food stall not found")
    stall_data = doc.to_dict()
    stall_data["id"] = doc.id
    # Get the stall's menu (from the "menu" subcollection)
    menu_docs = doc_ref.collection("menu").stream()
    menu_items = []
    for menu_doc in menu_docs:
        menu_item = menu_doc.to_dict()
        menu_item["id"] = menu_doc.id
        menu_items.append(menu_item)
    stall_data["menu"] = menu_items
    return jsonify(stall_data), 200


# POST to create a new food stall.
@app.route("/stalls", methods=["POST"])
def create_stall():
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")

    try:
        # Validate stall data using Pydantic model (excluding menu items)
        menu_items = data.pop("menu", [])
        stall_model = StallModel(**data)

        # Add the new stall document to Firestore
        doc_ref = db.collection("stalls").document()
        doc_ref.set(stall_model.to_dict())

        # Return the new stall with its ID
        new_stall = stall_model.to_dict()
        new_stall["id"] = doc_ref.id
        new_stall["menu"] = []

        # Add menu items if provided
        if menu_items:
            return add_menu_items(doc_ref.id, menu_items)

        return jsonify(new_stall), 201

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400


# PUT to update an existing food stall.
@app.route("/stalls/<stall_id>", methods=["PUT"])
def update_stall(stall_id):
    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")

    doc_ref = db.collection("stalls").document(stall_id)
    doc = doc_ref.get()

    if not doc.exists:
        abort(404, description="Food stall not found")

    try:
        # If menu is included, handle it separately
        menu_items = data.pop("menu", None)

        # Get current data and update with new data
        current_data = doc.to_dict()
        current_data.update(data)

        # Validate the updated data
        stall_model = StallModel.from_dict(current_data)

        # Update the document with validated data
        doc_ref.update(stall_model.to_dict())

        # Re-read the updated document
        updated_doc = doc_ref.get()
        stall_data = updated_doc.to_dict()
        stall_data["id"] = updated_doc.id

        # Also fetch updated menu items.
        menu_docs = doc_ref.collection("menu").stream()
        menu_list = []
        for menu_doc in menu_docs:
            item = menu_doc.to_dict()
            item["id"] = menu_doc.id
            menu_list.append(item)
        stall_data["menu"] = menu_list

        # If menu items were provided, update them
        if menu_items is not None:
            # Delete existing menu items
            for menu_doc in doc_ref.collection("menu").stream():
                menu_doc.reference.delete()

            # Add new menu items
            if menu_items:
                add_menu_items(stall_id, menu_items)
                stall_data["menu"] = menu_items

        return jsonify(stall_data), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400


# DELETE a food stall (and its associated menu items).
@app.route("/stalls/<stall_id>", methods=["DELETE"])
def delete_stall(stall_id):
    doc_ref = db.collection("stalls").document(stall_id)
    doc = doc_ref.get()
    if not doc.exists:
        abort(404, description="Food stall not found")
    # Delete all menu items in the "menu" subcollection.
    menu_collection = doc_ref.collection("menu")
    for menu_doc in menu_collection.stream():
        menu_doc.reference.delete()
    # Delete the stall document.
    doc_ref.delete()
    return jsonify({"message": f"Food stall {stall_id} deleted"}), 200


# GET all food items for a specific stall (its menu).
@app.route("/stalls/<stall_id>/menu", methods=["GET"])
def get_menu(stall_id):
    doc_ref = db.collection("stalls").document(stall_id)
    if not doc_ref.get().exists:
        abort(404, description="Food stall not found")
    menu_docs = doc_ref.collection("menu").stream()
    menu_items = []
    for menu_doc in menu_docs:
        item = menu_doc.to_dict()
        item["id"] = menu_doc.id
        menu_items.append(item)
    return jsonify(menu_items), 200


# Helper function to add menu items
def add_menu_items(stall_id, items):
    doc_ref = db.collection("stalls").document(stall_id)
    if not doc_ref.get().exists:
        abort(404, description="Food stall not found")

    new_items = []
    for item in items:
        try:
            # Validate menu item using Pydantic model
            menu_item = MenuItemModel(**item)
            item_dict = menu_item.to_dict()

            # Add the food item to the "menu" subcollection
            menu_doc_ref = doc_ref.collection("menu").document()
            menu_doc_ref.set(item_dict)

            # Add ID to the item
            item_dict["id"] = menu_doc_ref.id
            new_items.append(item_dict)

        except ValidationError as e:
            return jsonify({"error": f"Invalid menu item: {str(e)}"}), 400

    # Get updated stall data
    stall_doc = doc_ref.get()
    stall_data = stall_doc.to_dict()
    stall_data["id"] = stall_doc.id
    stall_data["menu"] = new_items

    return jsonify(stall_data), 201


# POST to add multiple food items to a stall's menu.
@app.route("/stalls/<stall_id>/menu", methods=["POST"])
def add_multiple_menu_items(stall_id):
    items = request.get_json()
    if not items or not isinstance(items, list):
        abort(400, description="Expected a JSON list of food items")

    return add_menu_items(stall_id, items)


# PUT to update an existing food item for a stall.
@app.route("/stalls/<stall_id>/menu/<food_id>", methods=["PUT"])
def update_menu_item(stall_id, food_id):
    doc_ref = db.collection("stalls").document(stall_id)
    menu_doc_ref = doc_ref.collection("menu").document(food_id)

    if not menu_doc_ref.get().exists:
        abort(404, description="Menu item not found for this stall")

    data = request.get_json()
    if not data:
        abort(400, description="Missing request body")

    try:
        # Get current data and update with new data
        current_data = menu_doc_ref.get().to_dict()
        current_data.update(data)

        # Validate the updated data
        menu_item = MenuItemModel(**current_data)

        # Update the document with validated data
        menu_doc_ref.update(menu_item.to_dict())

        # Return updated menu item with ID
        updated_data = menu_item.to_dict()
        updated_data["id"] = food_id
        return jsonify(updated_data), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400


# DELETE a food item from a stall's menu.
@app.route("/stalls/<stall_id>/menu/<food_id>", methods=["DELETE"])
def delete_menu_item(stall_id, food_id):
    doc_ref = db.collection("stalls").document(stall_id)
    menu_doc_ref = doc_ref.collection("menu").document(food_id)
    if not menu_doc_ref.get().exists:
        abort(404, description="Menu item not found for this stall")
    menu_doc_ref.delete()
    return (
        jsonify({"message": f"Menu item {food_id} deleted from stall {stall_id}"}),
        200,
    )


# Test function to add bulk data
@app.route("/test/add-bulk-data", methods=["POST"])
def add_bulk_test_data():
    # Sample data updated to match the current model
    test_data = [
        {
            "stall_name": "Prata Shop",
            "stall_image": "/images/prata-shop.jpg",
            "stall_description": "Authentic prata shop with the best recipes",
            "rating": 4.5,
            "review_count": 120,
            "cuisines": ["Indian", "Halal"],
            "preparation_time_mins": 15,
            "delivery_fee": 3.50,
            "stall_location": "40 Stamford Road #01-06 SMU Connexion Singapore 178908",
            "is_promoted": True,
            "menu": [
                {
                    "food_name": "Original Prata",
                    "food_price": 9.99,
                    "food_description": "Best Prata in the world",
                    "food_category": "Main",
                    "food_image": "/images/original-prata.jpg",
                },
                {
                    "food_name": "Cheese Prata",
                    "food_price": 10.50,
                    "food_description": "Prata filled with melted cheese",
                    "food_category": "Main",
                    "food_image": "/images/original-prata.jpg",
                },
                {
                    "food_name": "Egg Prata",
                    "food_price": 9.50,
                    "food_description": "Prata with a perfectly cooked egg inside",
                    "food_category": "Main",
                    "food_image": "/images/original-prata.jpg",
                },
                {
                    "food_name": "Chicken Prata",
                    "food_price": 11.00,
                    "food_description": "Prata stuffed with spicy chicken filling",
                    "food_category": "Main",
                    "food_image": "/images/original-prata.jpg",
                },
                {
                    "food_name": "Mutton Prata",
                    "food_price": 12.00,
                    "food_description": "Delicious prata with a hearty mutton filling",
                    "food_category": "Main",
                    "food_image": "/images/original-prata.jpg",
                },
            ],
        },
        {
            "stall_name": "Pasta Express",
            "stall_image": "/images/pasta-express.jpg",
            "stall_description": "Quick Italian pasta dishes",
            "rating": 4.2,
            "review_count": 85,
            "cuisines": ["Italian", "Western"],
            "preparation_time_mins": 10,
            "delivery_fee": 2.50,
            "stall_location": "40 Stamford Road #01-05 SMU Connexion Singapore 178908",
            "is_promoted": False,
            "menu": [
                {
                    "food_name": "Aglio Olio Pasta",
                    "food_price": 9.0,
                    "food_description": "Classic garlic and olive oil pasta",
                    "food_category": "Main",
                    "food_image": "/images/aglio-olio.jpg",
                },
                {
                    "food_name": "Bolognese Pasta",
                    "food_price": 7.0,
                    "food_description": "Hearty meat sauce pasta",
                    "food_category": "Main",
                    "food_image": "/images/aglio-olio.jpg",
                },
                {
                    "food_name": "Carbonara Pasta",
                    "food_price": 8.5,
                    "food_description": "Creamy pasta with bacon and egg",
                    "food_category": "Main",
                    "food_image": "/images/aglio-olio.jpg",
                },
                {
                    "food_name": "Pesto Pasta",
                    "food_price": 8.0,
                    "food_description": "Pasta tossed in a fresh basil pesto sauce",
                    "food_category": "Main",
                    "food_image": "/images/aglio-olio.jpg",
                },
                {
                    "food_name": "Seafood Pasta",
                    "food_price": 10.0,
                    "food_description": "Mixed seafood pasta in a light tomato sauce",
                    "food_category": "Main",
                    "food_image": "/images/aglio-olio.jpg",
                },
            ],
        },
        {
            "stall_name": "Kuro Kare",
            "stall_image": "/images/kuro-kare.jpg",
            "stall_description": "Japanese curry specialties",
            "rating": 4.7,
            "review_count": 150,
            "cuisines": ["Japanese", "Asian"],
            "preparation_time_mins": 12,
            "delivery_fee": 3.00,
            "stall_location": "40 Stamford Road #01-04 SMU Connexion Singapore 178908",
            "is_promoted": True,
            "menu": [
                {
                    "food_name": "Wasabi Mayo Chicken Katsu Curry Rice",
                    "food_price": 6.5,
                    "food_description": "Crispy chicken with wasabi mayo and curry",
                    "food_category": "Main",
                    "food_image": "/images/katsu.jpg",
                },
                {
                    "food_name": "Original Chicken Katsu Curry Rice",
                    "food_price": 6.0,
                    "food_description": "Classic chicken katsu with curry sauce",
                    "food_category": "Main",
                    "food_image": "/images/katsu.jpg",
                },
                {
                    "food_name": "Beef Curry Rice",
                    "food_price": 7.0,
                    "food_description": "Tender beef pieces in a rich curry sauce",
                    "food_category": "Main",
                    "food_image": "/images/katsu.jpg",
                },
                {
                    "food_name": "Vegetable Curry Rice",
                    "food_price": 5.5,
                    "food_description": "Mixed vegetables in a mild and aromatic curry",
                    "food_category": "Main",
                    "food_image": "/images/katsu.jpg",
                },
                {
                    "food_name": "Pork Curry Rice",
                    "food_price": 7.5,
                    "food_description": "Succulent pork simmered in a flavorful curry sauce",
                    "food_category": "Main",
                    "food_image": "/images/katsu.jpg",
                },
            ],
        },
        {
            "stall_name": "Michelin Nasi Lemak",
            "stall_image": "/images/nasi-lemak.jpg",
            "stall_description": "Delicious and authentic Nasi Lemak with a Michelin twist",
            "rating": 4.8,
            "review_count": 200,
            "cuisines": ["Malay", "Halal"],
            "preparation_time_mins": 20,
            "delivery_fee": 4.00,
            "stall_location": "10 Orchard Road #02-11 ION Orchard Singapore 238888",
            "is_promoted": True,
            "menu": [
                {
                    "food_name": "Classic Nasi Lemak",
                    "food_price": 8.50,
                    "food_description": "Traditional Nasi Lemak with sambal and anchovies",
                    "food_category": "Main",
                    "food_image": "/images/classic-nasi-lemak.jpg",
                },
                {
                    "food_name": "Spicy Sambal Nasi Lemak",
                    "food_price": 9.00,
                    "food_description": "Nasi Lemak with extra spicy sambal for a kick",
                    "food_category": "Main",
                    "food_image": "/images/classic-nasi-lemak.jpg",
                },
                {
                    "food_name": "Fried Chicken Nasi Lemak",
                    "food_price": 10.00,
                    "food_description": "Crispy fried chicken paired with creamy coconut rice",
                    "food_category": "Main",
                    "food_image": "/images/classic-nasi-lemak.jpg",
                },
                {
                    "food_name": "Vegetarian Nasi Lemak",
                    "food_price": 8.00,
                    "food_description": "A vegetarian twist on the classic, with tofu and tempeh",
                    "food_category": "Main",
                    "food_image": "/images/classic-nasi-lemak.jpg",
                },
                {
                    "food_name": "Egg Nasi Lemak",
                    "food_price": 8.75,
                    "food_description": "Perfectly cooked egg on a bed of coconut rice",
                    "food_category": "Main",
                    "food_image": "/images/classic-nasi-lemak.jpg",
                },
            ],
        },
        {
            "stall_name": "Subway Sandwich",
            "stall_image": "/images/subway-sandwich.jpg",
            "stall_description": "Freshly made sandwiches with a variety of fillings",
            "rating": 4.3,
            "review_count": 95,
            "cuisines": ["Western", "Fast Food"],
            "preparation_time_mins": 8,
            "delivery_fee": 2.75,
            "stall_location": "500 Changi Road #03-07 Changi City Point Singapore 486015",
            "is_promoted": False,
            "menu": [
                {
                    "food_name": "Turkey Sandwich",
                    "food_price": 7.50,
                    "food_description": "Sliced turkey with fresh veggies and sauce",
                    "food_category": "Main",
                    "food_image": "/images/sandwich.jpg",
                },
                {
                    "food_name": "Italian BMT",
                    "food_price": 8.00,
                    "food_description": "A classic sub with Italian cold cuts and cheese",
                    "food_category": "Main",
                    "food_image": "/images/sandwich.jpg",
                },
                {
                    "food_name": "Veggie Delite",
                    "food_price": 7.00,
                    "food_description": "A fresh mix of vegetables and light dressings",
                    "food_category": "Main",
                    "food_image": "/images/sandwich.jpg",
                },
                {
                    "food_name": "Chicken Teriyaki Sandwich",
                    "food_price": 8.25,
                    "food_description": "Grilled chicken with teriyaki sauce and lettuce",
                    "food_category": "Main",
                    "food_image": "/images/sandwich.jpg",
                },
                {
                    "food_name": "Tuna Sandwich",
                    "food_price": 7.75,
                    "food_description": "Classic tuna salad with crunchy vegetables",
                    "food_category": "Main",
                    "food_image": "/images/sandwich.jpg",
                },
            ],
        },
    ]

    # Results tracking
    results = {"success": [], "errors": []}

    # Process each stall
    for stall_data in test_data:
        try:
            # Extract menu items for separate validation
            menu_items = stall_data.pop("menu", [])

            # Validate stall data
            stall_model = StallModel(**stall_data)

            # Add stall to Firestore
            doc_ref = db.collection("stalls").document()
            doc_ref.set(stall_model.to_dict())
            stall_id = doc_ref.id

            # Process menu items
            menu_success = []
            for item in menu_items:
                try:
                    # Validate menu item
                    menu_item = MenuItemModel(**item)

                    # Add to Firestore
                    menu_doc_ref = doc_ref.collection("menu").document()
                    menu_doc_ref.set(menu_item.to_dict())

                    # Track success
                    item_with_id = menu_item.to_dict()
                    item_with_id["id"] = menu_doc_ref.id
                    menu_success.append(item_with_id)

                except Exception as e:
                    results["errors"].append(
                        f"Error adding menu item {item.get('food_name')} to stall {stall_data.get('stall_name')}: {str(e)}"
                    )

            # Record success
            stall_result = stall_model.to_dict()
            stall_result["id"] = stall_id
            stall_result["menu"] = menu_success
            results["success"].append(stall_result)

        except Exception as e:
            results["errors"].append(
                f"Error adding stall {stall_data.get('stall_name')}: {str(e)}"
            )

    return jsonify(results), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002, threaded=True)
