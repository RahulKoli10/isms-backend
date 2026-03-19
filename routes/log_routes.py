from flask import Blueprint, request, jsonify
from models import db, Log, Activity
from auth_middleware import login_required, role_required
from utils.datetime_utils import now_ist, now_ist_naive, ensure_ist

logs_bp = Blueprint('logs', __name__)


def _attach_idle_times(logs):
    usernames = {
        (log.username or "").strip().lower()
        for log in logs
        if (log.username or "").strip()
    }

    if not usernames:
        return [log.to_dict() for log in logs]

    idle_activities = (
        Activity.query.filter(
            db.func.lower(Activity.username).in_(usernames),
            Activity.idle_time.isnot(None),
            Activity.idle_time > 0,
        )
        .order_by(Activity.created_at.asc())
        .all()
    )

    activity_map = {}
    for activity in idle_activities:
        key = (activity.username or "").strip().lower()
        activity_map.setdefault(key, []).append(activity)

    enriched_logs = []

    for log in logs:
        serialized = log.to_dict()
        username_key = (log.username or "").strip().lower()
        session_start = ensure_ist(log.login_time)
        session_end = ensure_ist(log.logout_time)
        total_idle_time = 0

        if session_start and username_key in activity_map:
            if session_end:
                # Closed session: only count idle within [login, logout]
                for activity in activity_map[username_key]:
                    activity_time = ensure_ist(activity.created_at)
                    if activity_time and session_start <= activity_time <= session_end:
                        total_idle_time += activity.idle_time or 0
            else:
                # Open session (no logout yet): only count idle on the same day
                session_date = session_start.date()
                for activity in activity_map[username_key]:
                    activity_time = ensure_ist(activity.created_at)
                    if activity_time and activity_time.date() == session_date and activity_time >= session_start:
                        total_idle_time += activity.idle_time or 0

        serialized["idle_time"] = total_idle_time
        enriched_logs.append(serialized)

    return enriched_logs

@logs_bp.route("/logs", methods=["GET"])
@login_required
def get_all_logs():
    """Fetch all activity logs. Requires login."""
    try:
        logs = Log.query.order_by(Log.id.desc()).all()
        return jsonify(_attach_idle_times(logs)), 200
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
            login_time=now_ist_naive(),
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
