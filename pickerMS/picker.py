from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import logging
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = 'picker_db.sqlite'

def get_db_connection():
    """Create a database connection and return connection and cursor."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with the required tables."""
    try:
        conn = get_db_connection()
        with open('picker.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
    finally:
        if conn:
            conn.close()

# Initialize database on startup
if not os.path.exists(DB_PATH):
    init_db()

@app.route('/pickers/<int:pickerID>', methods=['GET'])
def get_picker(pickerID):
    """Get picker details by pickerID."""
    try:
        conn = get_db_connection()
        picker = conn.execute("SELECT * FROM picker WHERE pickerID = ?", (pickerID,)).fetchone()
        
        if not picker:
            return jsonify({"error": "Picker not found"}), 404
        
        # Convert to dictionary
        picker_data = {
            "pickerID": picker['pickerID'],
            "pickerName": picker['pickerName'],
            "pickerPhone": picker['pickerPhone']
        }
        
        return jsonify(picker_data), 200
    except Exception as e:
        logger.error(f"Error retrieving picker: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/confirmorder/<int:orderID>', methods=['PUT'])
def confirm_order(orderID):
    """Confirm an order by updating its status."""
    try:
        data = request.json
        pickerID = data.get('pickerID')
        
        # Validate request data
        if not pickerID:
            return jsonify({"error": "pickerID is required"}), 400
        
        conn = get_db_connection()
        
        # Check if picker exists
        picker_exists = conn.execute("SELECT 1 FROM picker WHERE pickerID = ?", (pickerID,)).fetchone()
        if not picker_exists:
            return jsonify({"error": "Picker not found"}), 404
        
        # Check if order exists
        order_exists = conn.execute("SELECT 1 FROM orders WHERE orderID = ?", (orderID,)).fetchone()
        
        if order_exists:
            # Update existing order
            conn.execute(
                "UPDATE orders SET status = 'confirmed', pickerID = ?, confirmationTimestamp = CURRENT_TIMESTAMP WHERE orderID = ?", 
                (pickerID, orderID)
            )
        else:
            # Create new order
            conn.execute(
                "INSERT INTO orders (orderID, status, pickerID, confirmationTimestamp) VALUES (?, 'confirmed', ?, CURRENT_TIMESTAMP)",
                (orderID, pickerID)
            )
        
        conn.commit()
        
        return jsonify({
            "message": f"Order {orderID} confirmed successfully",
            "orderID": orderID,
            "pickerID": pickerID,
            "status": "confirmed"
        }), 200
    except Exception as e:
        logger.error(f"Error confirming order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/picker', methods=['POST'])
def add_picker():
    """Add a new picker to the system."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['pickerName', 'pickerPhone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        pickerName = data['pickerName']
        pickerPhone = data['pickerPhone']
        
        conn = get_db_connection()
        
        # Insert new picker
        cursor = conn.execute(
            "INSERT INTO picker (pickerName, pickerPhone) VALUES (?, ?)",
            (pickerName, pickerPhone)
        )
        
        conn.commit()
        
        # Return the newly created picker with its ID
        new_pickerID = cursor.lastrowid
        
        return jsonify({
            "message": "Picker added successfully",
            "picker": {
                "pickerID": new_pickerID,
                "pickerName": pickerName,
                "pickerPhone": pickerPhone
            }
        }), 201
    except Exception as e:
        logger.error(f"Error adding picker: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

# Additional helper endpoints

@app.route('/pickers', methods=['GET'])
def get_all_pickers():
    """Get all pickers in the system."""
    try:
        conn = get_db_connection()
        pickers = conn.execute("SELECT * FROM picker").fetchall()
        
        result = []
        for picker in pickers:
            result.append({
                "pickerID": picker['pickerID'],
                "pickerName": picker['pickerName'],
                "pickerPhone": picker['pickerPhone']
            })
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error retrieving pickers: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/picker/<int:pickerID>', methods=['DELETE'])
def delete_picker(pickerID):
    """Delete a picker by ID."""
    try:
        conn = get_db_connection()
        
        # Check if picker exists
        picker_exists = conn.execute("SELECT 1 FROM picker WHERE pickerID = ?", (pickerID,)).fetchone()
        if not picker_exists:
            return jsonify({"error": "Picker not found"}), 404
        
        # Delete the picker
        conn.execute("DELETE FROM picker WHERE pickerID = ?", (pickerID,))
        conn.commit()
        
        return jsonify({"message": f"Picker {pickerID} deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting picker: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
