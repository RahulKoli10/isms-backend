from flask import Blueprint, jsonify, request
from models import db, Log, Activity, User, Admin
from config import Config
from utils.datetime_utils import now_ist, now_ist_iso, now_ist_naive
import json
import os
import base64

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


@activity_bp.route("/activity", methods=["POST", "PATCH"])
def save_activity():

    data = request.json
    print("Incoming Activity:", data)

    username = data.get("username")
    action = data.get("action")

    try:

        # =========================
        # SCREENSHOT HANDLING
        # =========================

        screenshot_data = data.get("screenshot")
        file_path = None

        if screenshot_data:

            image_bytes = base64.b64decode(screenshot_data)

            os.makedirs(Config.SCREENSHOT_FOLDER, exist_ok=True)

            filename = f"{username}_{int(now_ist().timestamp())}.png"

            file_path = os.path.join(Config.SCREENSHOT_FOLDER, filename)

            with open(file_path, "wb") as f:
                f.write(image_bytes)

        # =========================
        # LOGIN EVENT
        # =========================

        if action == "login":
            actor_details = get_actor_details(username, data)

            new_log = Log(
                username=username,
                login_time=now_ist_naive(),
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
                login_time=now_ist(),
                created_at=now_ist()
            )

            db.session.add(activity)

        # =========================
        # LOGOUT EVENT
        # =========================

        elif action == "logout":

            last_login = Log.query.filter(
                Log.username == username,
                Log.logout_time == None
            ).order_by(Log.id.desc()).first()

            if last_login:
                last_login.logout_time = now_ist_naive()
                last_login.action = "logout"

            activity = Activity(
                username=username,
                action="logout",
                logout_time=now_ist(),
                created_at=now_ist()
            )

            db.session.add(activity)

        # =========================
        # IDLE START
        # =========================

        elif action == "idle_start":

            idle_activity = Activity(
                username=username,
                action="idle",
                idle_time=None,
                activity_metadata=json.dumps({
                    "idle_start": now_ist_iso()
                }),
                created_at=now_ist()
            )

            db.session.add(idle_activity)

        # =========================
        # IDLE END
        # =========================

        elif action == "idle_end":

            duration = data.get("duration")

            if not duration:
                metadata = data.get("metadata", {})
                duration = metadata.get("duration")

            idle_start = None
            if data.get("metadata"):
                idle_start = data["metadata"].get("idle_start")

            last_idle = Activity.query.filter(
                Activity.username == username,
                Activity.action == "idle",
                Activity.idle_time == None
            ).order_by(Activity.id.desc()).first()

            if last_idle:

                last_idle.idle_time = duration

                last_idle.activity_metadata = json.dumps({
                    "idle_start": idle_start,
                    "idle_end": now_ist_iso(),
                    "duration": duration
                })

            else:

                activity = Activity(
                    username=username,
                    action="idle",
                    idle_time=duration,
                    activity_metadata=json.dumps({
                        "idle_start": idle_start,
                        "idle_end": now_ist_iso(),
                        "duration": duration
                    }),
                    created_at=now_ist()
                )

                db.session.add(activity)

        # =========================
        # APP USAGE
        # =========================

        elif action == "app_usage":

            activity = Activity(
                username=username,
                action="app_usage",
                app_url=data.get("app_url"),
                created_at=now_ist()
            )

            db.session.add(activity)

        # =========================
        # SCREENSHOT EVENT
        # =========================

        elif action == "screenshot":

            activity = Activity(
                username=username,
                action="screenshot",
                screenshot_path=file_path,
                created_at=now_ist()
            )

            db.session.add(activity)

        db.session.commit()

        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        print("ERROR:", e)  # Log server-side only
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again."
        }), 500
