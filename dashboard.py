from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('MonitorLogs')

IST = pytz.timezone('Asia/Kolkata')

@app.route("/")
def home():
    return '✅ Flask API is live on AWS Lambda!'

@app.route("/get_status", methods=["GET"])
def get_status():
    today_only = request.args.get('today')

    try:
        response = table.scan()
        items = response.get('Items', [])

        # Optional: filter today's logs only
        if today_only:
            today_str = datetime.now(IST).strftime("%Y-%m-%d")
            items = [item for item in items if item['timestamp'].startswith(today_str)]

        # Sort by timestamp descending
        items.sort(key=lambda x: x['timestamp'], reverse=True)

        # Return specific fields only
        filtered_data = [
            {
                "timestamp": item["timestamp"],
                "url": item["url"],
                "call_initiated": item["call_initiated"],
                "recipient": item["recipient"]
            } for item in items
        ]

        response = jsonify(filtered_data)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
