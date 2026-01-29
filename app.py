from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["webhookdb"]
collection = db["events"]

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    event = request.headers.get("X-GitHub-Event")

    if event == "push":
        doc = {
            "requestid": data["after"],
            "author": data["pusher"]["name"],
            "action": "PUSH",
            "tobranch": data["ref"].split("/")[-1],
            "timestamp": datetime.utcnow().strftime("%d %B 2026 - %I:%M %p UTC"),
        }
        collection.insert_one(doc)
        return jsonify({"status": "PUSH received"}), 200

    elif event == "pull_request":
        pr_action = data["action"]
        if pr_action == "opened":
            doc = {
                "requestid": str(data["number"]),
                "author": data["sender"]["login"],
                "action": "PULLREQUEST",
                "frombranch": data["pull_request"]["head"]["ref"],
                "tobranch": data["pull_request"]["base"]["ref"],
                "timestamp": datetime.utcnow().strftime("%d %B 2026 - %I:%M %p UTC"),
            }
            collection.insert_one(doc)
            return jsonify({"status": "PULLREQUEST received"}), 200
        elif pr_action == "closed" and data["pull_request"]["merged"]:
            doc = {
                "requestid": str(data["number"]),
                "author": data["sender"]["login"],
                "action": "MERGE",
                "frombranch": data["pull_request"]["head"]["ref"],
                "tobranch": data["pull_request"]["base"]["ref"],
                "timestamp": datetime.utcnow().strftime("%d %B 2026 - %I:%M %p UTC"),
            }
            collection.insert_one(doc)
            return jsonify({"status": "MERGE received"}), 200

    return jsonify({"status": "ignored"}), 200

@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find().sort("_id", -1).limit(20))
    for e in events:
        e["_id"] = str(e["_id"])
    return jsonify(events)

@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Events Monitor</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial,sans-serif; max-width
"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

