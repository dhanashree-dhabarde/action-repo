# this is app
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Environment variables for security
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'dhanashreedhabarde')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'CdCu769MzMTPwX0y')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER', 'cluster0.n9xx0xa.mongodb.net')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'webhook_db')

# URL encode credentials to handle special characters
username = quote_plus(MONGODB_USERNAME)
password = quote_plus(MONGODB_PASSWORD)

# MongoDB connection with error handling
try:
    connection_string = f"mongodb+srv://{username}:{password}@{MONGODB_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(connection_string)
    db = client[MONGODB_DATABASE]
    collection = db["events"]
    # Test connection
    client.admin.command('ping')
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    raise

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "Webhook server is running!",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook events"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        event_type = request.headers.get('X-GitHub-Event')
        if not event_type:
            return jsonify({"error": "Missing X-GitHub-Event header"}), 400
        
        event = {}
        timestamp = datetime.utcnow()
        formatted_time = timestamp.strftime("%d %B %Y - %I:%M %p UTC")
        
        # Handle different event types
        if event_type == "push":
            event = handle_push_event(data, formatted_time)
        elif event_type == "pull_request":
            event = handle_pull_request_event(data, formatted_time)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return jsonify({"status": "ignored", "reason": f"Unhandled event type: {event_type}"}), 200
        
        # Store event if processed
        if event:
            event["timestamp"] = timestamp
            event["event_type"] = event_type
            collection.insert_one(event)
            logger.info(f"Stored event: {event['type']}")
            return jsonify({"status": "success"}), 200
        
        return jsonify({"status": "ignored"}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

def handle_push_event(data, formatted_time):
    """Process push events"""
    try:
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        repository = data["repository"]["name"]
        
        return {
            "type": "push",
            "message": f'"{author}" pushed to "{to_branch}" in "{repository}" on {formatted_time}',
            "author": author,
            "branch": to_branch,
            "repository": repository
        }
    except KeyError as e:
        logger.error(f"Missing field in push event: {e}")
        return None

def handle_pull_request_event(data, formatted_time):
    """Process pull request events"""
    try:
        action = data["action"]
        pull_request = data["pull_request"]
        author = pull_request["user"]["login"]
        from_branch = pull_request["head"]["ref"]
        to_branch = pull_request["base"]["ref"]
        repository = pull_request["base"]["repo"]["name"]
        pr_number = pull_request["number"]
        
        if action == "opened":
            return {
                "type": "pull_request",
                "message": f'"{author}" submitted pull request #{pr_number} from "{from_branch}" to "{to_branch}" in "{repository}" on {formatted_time}',
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "repository": repository,
                "pr_number": pr_number,
                "action": action
            }
        elif action == "closed" and pull_request.get("merged", False):
            return {
                "type": "merge",
                "message": f'"{author}" merged pull request #{pr_number} from "{from_branch}" to "{to_branch}" in "{repository}" on {formatted_time}',
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "repository": repository,
                "pr_number": pr_number,
                "action": action
            }
        else:
            logger.info(f"Ignored pull request action: {action}")
            return None
    except KeyError as e:
        logger.error(f"Missing field in pull request event: {e}")
        return None

@app.route('/events', methods=['GET'])
def get_events():
    """Retrieve recent events with optional filtering"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 events
        event_type = request.args.get('type')
        
        # Build query
        query = {}
        if event_type:
            query['type'] = event_type
        
        # Fetch events
        cursor = collection.find(query, {'_id': 0}).sort("timestamp", -1).limit(limit)
        events = list(cursor)
        
        return jsonify({
            "events": events,
            "count": len(events),
            "limit": limit
        })
    
    except Exception as e:
        logger.error(f"Error retrieving events: {e}")
        return jsonify({"error": "Failed to retrieve events"}), 500

@app.route('/events/summary', methods=['GET'])
def get_events_summary():
    """Get a summary of recent events"""
    try:
        # Get counts by event type
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        summary = list(collection.aggregate(pipeline))
        total_events = sum(item["count"] for item in summary)
        
        return jsonify({
            "total_events": total_events,
            "event_types": summary
        })
    
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({"error": "Failed to get summary"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
