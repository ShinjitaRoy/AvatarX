from flask import Blueprint, request, jsonify
from src.webapi.service_scheduler import ServiceScheduler
from src.webapi.models import User
import re

bp = Blueprint("meetings", __name__, url_prefix="/api")
scheduler = ServiceScheduler()

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@bp.route("/schedule", methods=["POST"])
def schedule_meeting():
    data = request.get_json() or {}
    meeting_id = data.get("meeting_id")
    start_time = data.get("start_time")
    password = data.get("password", "")
    user_id = data.get("user_id")  # Get from auth token in production!
    
    if not all([meeting_id, start_time, user_id]):
        return jsonify({"error": "meeting_id, start_time and user_id required"}), 400
    if not TIME_RE.match(start_time):
        return jsonify({"error": "start_time must be in HH:MM format"}), 400
        
    try:
        # Schedule in memory
        scheduler.schedule_meeting(meeting_id, password, start_time)
        # Save to database
        if User.add_meeting(user_id, meeting_id, password, start_time):
            return jsonify({"ok": True, "scheduled": {
                "meeting_id": meeting_id,
                "password": password,
                "start_time": start_time
            }})
        return jsonify({"error": "Failed to save meeting"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/start", methods=["POST"])
def start_now():
    data = request.get_json() or {}
    meeting_id = data.get("meeting_id")
    password = data.get("password", "")
    if not meeting_id:
        return jsonify({"error": "meeting_id required"}), 400
    try:
        res = scheduler.start_now(meeting_id, password)
        return jsonify({"ok": True, "result": bool(res)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/leave", methods=["POST"])
def leave():
    try:
        ok = scheduler.leave()
        return jsonify({"ok": bool(ok)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/list", methods=["GET"])
def list_scheduled():
    user_id = request.args.get("user_id")  # Get from auth token in production!
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
        
    try:
        meetings = User.get_meetings(int(user_id))
        return jsonify({"scheduled": meetings})
    except Exception as e:
        return jsonify({"error": str(e)}), 500