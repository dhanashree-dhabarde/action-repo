
# GitHub Webhook Tracker

A full-stack app that listens to GitHub webhook events (push, pull request, merge), stores them in MongoDB, and displays them in real time.

## Stack

- Flask (Backend)
- MongoDB Atlas (Database)
- ReactJS (Frontend)
- Ngrok (Webhook tunneling)

## Setup

1. `cd backend` → `pip install -r requirements.txt` → `python app.py`
2. `ngrok http 5000` → Copy HTTPS URL
3. Add GitHub webhook to: `https://<ngrok-url>/webhook`
4. `cd frontend` → `npm install` → `npm start`

Watch webhook events in real time 🎉
