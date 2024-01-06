from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import requests
import threading
import time
import json
import base64
from openai import OpenAI
import os

# Configuration Variables
DATABASE_URI = 'sqlite:///messages.db'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
SERVER_URL_SEND = os.environ['SERVER_URL_SEND']
SERVER_URL_RECEIVE = os.environ['SERVER_URL_RECEIVE']
AUTH_USERNAME = os.environ['SERVER_USERNAME']
AUTH_PASSWORD = os.environ['SERVER_PASSWORD']
GROUP_ID = os.environ['GROUP_ID']
USER_NUMBER = os.environ['USER_NUMBER']

# Flask App and Database Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Database Model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_number = db.Column(db.String(120))
    source_name = db.Column(db.String(120))
    timestamp = db.Column(db.String(120))
    message = db.Column(db.Text)
    group_id = db.Column(db.String(120))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Initialize Database
with app.app_context():
    db.create_all()

# OpenAI Client Setup
client = OpenAI(api_key=OPENAI_API_KEY)


# Utility Functions
def format_messages(messages):
    return "\n".join([f"{msg.source_name}: {msg.message}" for msg in messages])


def generate_gpt_summary(formatted_messages):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{
            "role":
            "system",
            "content":
            "Your task is to summarize text messages. You will be given some messages of a group chat, identify the discussion from the rest of the conversation, then summarize the discussion. Disregard everything but the discussion you identify. \n\nThis is how you should format your summary:\n\n1. The overarching topic of discussion, if there are multiple then state that\n2. Every person's view points\n3. A play by play, a more indepth sequential timeline of the discussion\n\nIf you cannot find a discussion, respond with that\n\nIf you do a good job, I will give you 20 dollars and some ice cream."
        }, {
            "role": "user",
            "content": formatted_messages
        }],
        temperature=1,
        max_tokens=1535,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0)
    return response.choices[0].message.content


def send_or_print_summary(summary):
    print(summary)  # Print the summary for logging
    send_message_via_server(
        summary)  # Send the summary to the specified number


# Database Interaction Functions
def get_last_messages(limit=400):
    return Message.query.order_by(Message.id.desc()).limit(limit).all()[::-1]


def get_messages_after(start_timestamp=None, limit=400):
    print(f"Getting messages after timestamp: {start_timestamp}")
    query = Message.query.with_entities(Message.source_name, Message.message)

    if start_timestamp:
        query = query.filter(Message.timestamp > start_timestamp)

    query = query.order_by(Message.timestamp.asc()).limit(limit)
    message_tuples = query.all()
    print(f"Retrieved {len(message_tuples)} messages")

    # Formatting messages into a single string from oldest to newest
    formatted_messages = "\n".join([f"{source_name}: {message}" for source_name, message in message_tuples])

    return formatted_messages

def insert_message_into_db(source_number, source_name, timestamp, message, group_id):
    new_message = Message(source_number=source_number, source_name=source_name, timestamp=timestamp, message=message, group_id=group_id)
    db.session.add(new_message)
    db.session.commit()
    print(f"New message logged: Source Number: {source_number}, Source Name: {source_name}, Timestamp: {timestamp}, Message: {message}, Group ID: {group_id}")

def process_message_data(envelope, message_data):
    group_info = message_data.get('groupInfo', {})
    group_id = group_info.get('groupId', 'N/A')

    # Only process messages from the specified group
    if group_id == 'XWvirHXNRRgtVdkTyZ4drvRZFEc/Vr3FhnBuz/Ungoc=':
        source_number = envelope.get('sourceNumber', 'N/A')
        source_name = envelope.get('sourceName', 'N/A')
        timestamp = envelope.get('timestamp', 'N/A')
        message = message_data.get('message', 'N/A')

        insert_message_into_db(source_number, source_name, timestamp, message, group_id)

        # Check if the message is the '/summary' command
        if message_data.get('message') == '/summary':
            quote_id = message_data.get('quote', {}).get('id', None)
            if quote_id:
                # Proceed with summary generation if the message is a reply to a quote
                last_messages = get_messages_after(quote_id)
                print("formated messages returned ")
                gpt_summary = generate_gpt_summary(last_messages)
                send_or_print_summary(gpt_summary)
            else:
                # Send a response if /summary is not a reply to a message
                response = "ERROR: The command /summary must be a reply to the first message in the discussion, the chat logs from that point on will be summarized."
                send_message_via_server(response)
    else:
        print(f"Message from different group ignored. Group ID: {group_id}")


def parse_signal_response(response_data):
    for item in response_data:
        envelope = item.get('envelope', {})
        if 'dataMessage' in envelope:
            data_message = envelope['dataMessage']
            process_message_data(envelope, data_message)
        elif 'syncMessage' in envelope and 'sentMessage' in envelope[
                'syncMessage']:
            sent_message = envelope['syncMessage']['sentMessage']
            process_message_data(envelope, sent_message)


# Server Communication Functions
def send_message_via_server(message):
    headers = {
        'Content-Type':
        'application/json',
        'Authorization':
        'Basic ' + base64.b64encode(
            f'{AUTH_USERNAME}:{AUTH_PASSWORD}'.encode()).decode('utf-8')
    }
    data = {
        "message": message,
        "number": USER_NUMBER,  # Specified phone number
        "recipients": [f'group.{GROUP_ID}'],
        "text_mode": "normal"
    }
    try:
        response = requests.post(SERVER_URL_SEND, headers=headers, json=data)
        print("Message sent via server. Status code:", response)
    except Exception as e:
        print("Error sending message via server:", e)


def send_periodic_requests():
    with app.app_context():  # Push the Flask app context
        successful_requests = 0
        while True:
            response = requests.get(SERVER_URL_RECEIVE,
                                    auth=(AUTH_USERNAME, AUTH_PASSWORD))
            if response.status_code == 200:
                successful_requests += 1
                print(f"Successful requests: {successful_requests}")
                parse_signal_response(response.json())

            time.sleep(10)


def start_background_thread():
    thread = threading.Thread(target=send_periodic_requests)
    thread.daemon = True
    thread.start()


# Flask Routes
@app.route('/')
def home():
    return "Hello, World!"

# Main Block
if __name__ == '__main__':
    start_background_thread()
    app.run(host='0.0.0.0', port=4999, debug=False)
