from flask import Blueprint, request, jsonify, session
from models import db, User, Admin, Log
from utils.datetime_utils import now_ist_naive

user_bp = Blueprint('login', __name__)


# =========================
# SESSION VERIFICATION
# =========================
@user_bp.route("/session", methods=["GET", "OPTIONS"])
def check_session():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    user_id = session.get("user_id")
    username = session.get("username")
    role = session.get("role")

    if user_id and username:
        return jsonify({
            "success": True,
            "authenticated": True,
            "user": {
                "id": user_id,
                "username": username,
                "role": role
            }
        }), 200

    return jsonify({
        "success": False,
        "authenticated": False,
        "message": "No active session"
    }), 401


# =========================
# LOGIN
# =========================
@user_bp.route("/login", methods=["POST", "OPTIONS"])
def login():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body missing"
            }), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password required"
            }), 400

        # Check admin
        user = Admin.query.filter_by(username=username).first()

        # Check user
        if not user:
            user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if not user.check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid password"
            }), 401

        # Update status
        user.status = "Online"

        # Create login log
        new_log = Log(
            login_time=now_ist_naive(),
            username=user.username,
            email=user.email,
            designation=user.designation or "N/A",
            domain=user.domain or "System",
            role=user.role,
            action="User Logged In"
        )

        db.session.add(new_log)
        db.session.commit()

        # Create session
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Server error",
            "error": str(e)
        }), 500


# =========================
# LOGOUT
# =========================
@user_bp.route("/logout", methods=["POST", "OPTIONS"])
def logout():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        username = session.get("username")

        if not username and request.is_json:
            username = request.json.get("username")

        if username:

            user = Admin.query.filter_by(username=username).first() \
                   or User.query.filter_by(username=username).first()

            if user:
                user.status = "Offline"

                # find last login log
                last_log = Log.query.filter_by(
                    username=user.username,
                    logout_time=None
                ).order_by(Log.id.desc()).first()

                if last_log:
                    last_log.logout_time = now_ist_naive()
                    last_log.action = "User Logged Out"

                db.session.commit()

        session.clear()

        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Server error",
            "error": str(e)
        }), 500


# =========================
# GET LOGS
# =========================
@user_bp.route("/logs", methods=["GET", "OPTIONS"])
def get_logs():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        logs = Log.query.order_by(Log.id.desc()).all()

        return jsonify([
            log.to_dict() for log in logs
        ]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
