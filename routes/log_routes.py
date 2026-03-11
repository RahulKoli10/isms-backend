from flask import Blueprint, request, jsonify
from models import db, Log
from auth_middleware import login_required, role_required
import datetime

logs_bp = Blueprint('logs', __name__)

@logs_bp.route("/logs", methods=["GET"])
@login_required
def get_all_logs():
    """Fetch all activity logs. Requires login."""
    try:
        logs = Log.query.order_by(Log.id.desc()).all()
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception:
        return jsonify({"error": "Failed to fetch logs."}), 500

@logs_bp.route("/logs", methods=["POST"])
@login_required
def create_log():
    """Manually create a log entry."""
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    try:
        new_log = Log(
            login_time=datetime.datetime.now().isoformat(),
            username=data.get("username"),
            email=data.get("email"),
            domain=data.get("domain", ""),
            role=data.get("role", "User"),
            designation=data.get("designation", ""),
            action=data.get("action", "No action specified")
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify(new_log.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to create log."}), 500

@logs_bp.route("/logs/clear", methods=["DELETE"])
@login_required
@role_required("superadmin")
def clear_all_logs():
    """Delete all log entries. Superadmin only."""
    try:
        db.session.query(Log).delete()
        db.session.commit()
        return jsonify({"message": "All logs cleared successfully"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to clear logs."}), 500
