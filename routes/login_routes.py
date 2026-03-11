from flask import Blueprint, request, jsonify, session
import datetime
from models import db, User, Admin, Log

user_bp = Blueprint('login', __name__)


# =========================
# LOGIN ROUTE
# =========================
@user_bp.route("/login", methods=["POST", "OPTIONS"])
def login():

    # Handle CORS preflight request
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()

        # Validate request body
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
                "message": "Username and password are required"
            }), 400

        # Check Admin table first
        user = Admin.query.filter_by(username=username).first()

        # Then check User table
        if not user:
            user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        # Password check
        if not user.check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid password"
            }), 401

        # Update status
        user.status = "Online"

        # Create login log
        new_log = Log(
            login_time=datetime.datetime.now().isoformat(),
            username=user.username,
            email=user.email,
            designation=user.designation if user.designation else "N/A",
            domain=user.domain if user.domain else "System",
            role=user.role,
            action="User Logged In"
        )

        print(f"📝 Creating Log -> User: {new_log.username}, Designation: {new_log.designation}")

        db.session.add(new_log)
        db.session.commit()

        # Store session
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
# LOGOUT ROUTE
# =========================
@user_bp.route("/logout", methods=["POST", "OPTIONS"])
def logout():

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        username = session.get("username")

        # Fallback if session missing
        if not username and request.is_json:
            username = request.json.get("username")

        if username:
            user = Admin.query.filter_by(username=username).first() or \
                   User.query.filter_by(username=username).first()

            if user:
                user.status = "Offline"

                new_log = Log(
                    logout_time=datetime.datetime.now().isoformat(),
                    username=user.username,
                    email=user.email,
                    designation=user.designation or "N/A",
                    domain=user.domain or "System",
                    role=user.role,
                    action="User Logged Out"
                )

                db.session.add(new_log)
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
# GET LOGS ROUTE
# =========================
@user_bp.route("/logs", methods=["GET", "OPTIONS"])
def get_logs():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        logs = Log.query.order_by(Log.login_time.desc()).all()
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500