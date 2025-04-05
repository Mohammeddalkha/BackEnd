import requests
import time
from datetime import datetime
from twilio.rest import Client
import urllib3
import pytz
import os
import uuid
import boto3
from pytz import timezone

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== Twilio Credentials ==================
TWILIO_ACCOUNT_SID  = "ACc1478a277b5cec22c01f25fdef4cf41a"
TWILIO_AUTH_TOKEN  = "0bfbdc2db27e179386d9f2d57a12c354"
TWILIO_PHONE_NUMBER = "+18454078544"

RECIPIENTS = {
    "+918300521700": "DALHA",
    "+919876543210": "USER2"
}

# ================== URLs to Monitor ==================
URLS_TO_MONITOR = [
    'https://fcrm.myfundbox.com',
    'https://httpstat.us/502'
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ================== DynamoDB Setup ==================
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('MonitorLogs')

IST = timezone('Asia/Kolkata')

def log_to_db(url, status, call_initiated, recipient):
    """Log monitoring events to DynamoDB in IST."""
    timestamp = datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p")  # 12-hour IST format
    log_id = str(uuid.uuid4())

    try:
        table.put_item(
            Item={
                'id': log_id,
                'timestamp': timestamp,
                'url': url,
                'status': status,
                'call_initiated': call_initiated,
                'recipient': recipient
            }
        )
        print(f"✅ Log saved to DynamoDB (ID: {log_id})")
    except Exception as e:
        print(f"ERROR logging to DynamoDB: {e}")

def wait_for_call_status(client, call_sid, timeout=60):
    """Wait for call status."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        call = client.calls(call_sid).fetch()
        if call.status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
            return call.status
        time.sleep(2)
    return 'no-answer'

def send_call_notification(phone_number, url):
    """Send a single call notification when the site is down."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = f"The monitored website {url} is down with status code 502. Please check immediately."

        call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say>{message}</Say></Response>"
        )

        print(f"📞 Call initiated to {phone_number}, Call SID: {call.sid}")

        call_status = wait_for_call_status(client, call.sid)
        print(f"📞 Call status: {call_status}")

        return call_status not in ['failed', 'canceled']

    except Exception as e:
        print(f"❌ ERROR: Unable to send call to {phone_number}. Exception: {e}")
        return False

def check_url(url):
    """Check the status of a given URL."""
    try:
        response = requests.get(url, timeout=10, verify=False, headers=HEADERS)
        status_code = response.status_code

        if status_code == 502:
            print(f"🚨 ALERT: {url} is DOWN (502 Bad Gateway)")
            for phone, recipient in RECIPIENTS.items():
                call_sent = send_call_notification(phone, url)
                if call_sent:
                    log_to_db(url, "DOWN", "YES", recipient)

        elif status_code == 403:
            print(f"⚠️ WARNING: {url} returned 403 Forbidden. Checking response body...")
            if "502 Bad Gateway" in response.text:
                print("Detected 502 error in body despite 403.")
                for phone, recipient in RECIPIENTS.items():
                    call_sent = send_call_notification(phone, url)
                    if call_sent:
                        log_to_db(url, "DOWN", "YES", recipient)
            else:
                print("Site blocked by WAF. No action.")

        else:
            print(f"✅ {url} is UP (Status Code: {status_code})")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Unable to reach {url}. Exception: {e}")

# For local or Lambda use
def lambda_handler(event=None, context=None):
    for url in URLS_TO_MONITOR:
        check_url(url)

if __name__ == "__main__":
    lambda_handler()
# test change for GitHub sync
