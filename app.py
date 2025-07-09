from flask import Flask
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    
    # MongoDB Configuration
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://dhanashreedhabarde:CdCu769MzMTPwX0y@cluster0.n9xx0xa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
    # Initialize extensions
    mongo.init_app(app)
    
    # Import routes after app context is available
    with app.app_context():
        from webhook_receiver import register_routes
        register_routes(app, mongo)
    
    return app
