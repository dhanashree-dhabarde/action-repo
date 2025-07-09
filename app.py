# Pull request test
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://dhanashreedhabarde:CdCu769MzMTPwX0y@cluster0.n9xx0xa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["webhook_db"]
collection = db["events"]

@app.route('/')
def home():
    return "Webhook server is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    event = {}
    now = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    if event_type == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        event["type"] = "push"
        event["message"] = f'"{author}" pushed to "{to_branch}" on {now}'

    elif event_type == "pull_request":
        action = data["action"]
        if action == "opened":
            author = data["pull_request"]["user"]["login"]
            from_branch = data["pull_request"]["head"]["ref"]
            to_branch = data["pull_request"]["base"]["ref"]
            event["type"] = "pull_request"
            event["message"] = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {now}'
        elif action == "closed" and data["pull_request"]["merged"]:
            author = data["pull_request"]["user"]["login"]
            from_branch = data["pull_request"]["head"]["ref"]
            to_branch = data["pull_request"]["base"]["ref"]
            event["type"] = "merge"
            event["message"] = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {now}'

    if event:
        collection.insert_one(event)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "ignored"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("_id", -1).limit(10))
    return jsonify([e["message"] for e in events])

if __name__ == "__main__":
    app.run(port=5000)
