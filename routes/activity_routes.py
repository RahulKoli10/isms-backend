from flask import Blueprint, jsonify, request
from models import db, Log, Activity, User, Admin
from config import Config
from utils.datetime_utils import now_ist, now_ist_iso, now_ist_naive, ensure_ist
from datetime import datetime
import json
import os
import base64
from auth_middleware import login_required

activity_bp = Blueprint('activity', __name__)


def get_actor_details(username, payload):
    actor = None
    if username:
        actor = Admin.query.filter_by(username=username).first() or User.query.filter_by(username=username).first()

    return {
        "email": payload.get("email") or (actor.email if actor else "system@gmail.com"),
        "domain": payload.get("domain") or (actor.domain if actor else "Agent"),
        "role": payload.get("role") or (actor.role if actor else "User"),
        "designation": payload.get("designation") or (actor.designation if actor else ""),
    }


def parse_client_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return ensure_ist(value)

    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return None

    normalized = text.replace(" ", "T")

    try:
        return ensure_ist(datetime.fromisoformat(normalized))
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return ensure_ist(datetime.strptime(text, fmt))
        except ValueError:
            continue

    return None


def get_event_time(metadata, *keys):
    for key in keys:
        parsed = parse_client_datetime(metadata.get(key))
        if parsed is not None:
            return parsed
    return now_ist()


@activity_bp.route("/activity", methods=["GET"])
@login_required
def get_activity():
    try:
        activities = Activity.query.order_by(Activity.id.desc()).all()
        return jsonify([activity.to_dict() for activity in activities]), 200
    except Exception:
        return jsonify({"error": "Failed to fetch activity."}), 500


@activity_bp.route("/activity", methods=["POST", "PATCH"])
def save_activity():
    data = request.json or {}
    print("Incoming Activity:", data)

    username = data.get("username")
    action = data.get("action")
    metadata = data.get("metadata") or {}

    try:
        screenshot_data = metadata.get("screenshot") or data.get("screenshot")
        file_path = None

        if screenshot_data:
            image_bytes = base64.b64decode(screenshot_data)
            os.makedirs(Config.SCREENSHOT_FOLDER, exist_ok=True)
            filename = f"{username}_{int(now_ist().timestamp())}.png"
            file_path = os.path.join(Config.SCREENSHOT_FOLDER, filename)

            with open(file_path, "wb") as f:
                f.write(image_bytes)

        if action == "login":
            actor_details = get_actor_details(username, data)
            login_time = get_event_time(metadata, "login_time", "timestamp")

            new_log = Log(
                username=username,
                login_time=login_time.replace(tzinfo=None),
                logout_time=None,
                email=actor_details["email"],
                domain=actor_details["domain"],
                role=actor_details["role"],
                designation=actor_details["designation"],
                action="login"
            )
            db.session.add(new_log)

            activity = Activity(
                username=username,
                action="login",
                login_time=login_time,
                screenshot_path=file_path,
                created_at=login_time
            )
            db.session.add(activity)

        elif action == "logout":
            logout_time = get_event_time(metadata, "logout_time", "timestamp")

            last_login = Log.query.filter(
                Log.username == username,
                Log.logout_time == None
            ).order_by(Log.id.desc()).first()

            if last_login:
                last_login.logout_time = logout_time.replace(tzinfo=None)
                last_login.action = "logout"

            activity = Activity(
                username=username,
                action="logout",
                logout_time=logout_time,
                idle_time=metadata.get("idle_time"),
                screenshot_path=file_path,
                created_at=logout_time
            )
            db.session.add(activity)

        elif action == "idle_start":
            idle_start = get_event_time(metadata, "idle_start", "timestamp")
            idle_activity = Activity(
                username=username,
                action="idle",
                idle_time=None,
                activity_metadata=json.dumps({
                    "idle_start": idle_start.isoformat()
                }),
                created_at=idle_start
            )
            db.session.add(idle_activity)

        elif action == "idle_end":
            duration = data.get("duration")
            if duration is None:
                duration = metadata.get("duration")

            idle_start = metadata.get("idle_start")
            idle_end = get_event_time(metadata, "idle_end", "timestamp")

            last_idle = Activity.query.filter(
                Activity.username == username,
                Activity.action == "idle",
                Activity.idle_time == None
            ).order_by(Activity.id.desc()).first()

            payload_metadata = json.dumps({
                "idle_start": idle_start,
                "idle_end": idle_end.isoformat(),
                "duration": duration
            })

            if last_idle:
                last_idle.idle_time = duration
                last_idle.activity_metadata = payload_metadata
                last_idle.created_at = idle_end
            else:
                activity = Activity(
                    username=username,
                    action="idle",
                    idle_time=duration,
                    activity_metadata=payload_metadata,
                    created_at=idle_end
                )
                db.session.add(activity)

        elif action == "app_usage":
            event_time = get_event_time(metadata, "timestamp")
            activity = Activity(
                username=username,
                action="app_usage",
                app_url=data.get("app_url") or metadata.get("app_url"),
                created_at=event_time
            )
            db.session.add(activity)

        elif action == "screenshot":
            event_time = get_event_time(metadata, "timestamp")
            activity = Activity(
                username=username,
                action="screenshot",
                screenshot_path=file_path,
                created_at=event_time
            )
            db.session.add(activity)

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        print("ERROR:", e)
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again."
        }), 500
