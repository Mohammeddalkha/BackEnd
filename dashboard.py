from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import subprocess

app = Flask(__name__)

# ✅ Allow requests from all origins (Frontend & GitHub Pages)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Hardcoded Database Configuration
DB_CONFIG = {
    'host': 'ballast.proxy.rlwy.net',
    'user': 'root',
    'password': 'RnHgTWEWcuvjvlQHTKSEzYqLGGFtDUSS',
    'database': 'railway',
    'port': 32373
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/get_status', methods=['GET'])
def get_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    today = request.args.get('today')

    query = "SELECT timestamp, url, call_initiated, recipient FROM monitor_log"

    if today:
        query += " WHERE DATE(timestamp) = CURDATE()"

    query += " ORDER BY timestamp DESC"

    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    response = jsonify(data)
    response.headers.add("Access-Control-Allow-Origin", "*")  # ✅ Fixes CORS issue
    return response

if __name__ == "__main__":
        # ✅ Start Flask API
    app.run(host='0.0.0.0', port=5000, debug=True)
