from flask import Blueprint, request, jsonify, session
import datetime
from models import db, User, Log
from auth_middleware import login_required, role_required
from sqlalchemy.exc import IntegrityError
from utils.datetime_utils import now_ist_naive

users_bp = Blueprint('users', __name__)

def generate_user_id():
    """Generates a custom ID for a standard User."""
    prefix = 'US'
    count = User.query.count()
    year_short = datetime.datetime.now().strftime("%y")
    return f"{prefix}/IN/{year_short}/{str(count + 1).zfill(4)}"


@users_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    role_filter = request.args.get("role")
    query = User.query
    if role_filter:
        query = query.filter(User.role.ilike(f'%{role_filter}%'))
    users = query.all()
    return jsonify([u.to_dict() for u in users])


@users_bp.route("/users", methods=["POST"])
@login_required
@role_required("superadmin", "admin")
def create_user():
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Require a password — no default
    password = data.get("password")
    if not password or len(password) < 6:
        return jsonify({"error": "A password of at least 6 characters is required"}), 400

    try:
        custom_id = data.get("userId") or generate_user_id()
        designation = data.get("designation", "")
        role = str(data.get("role", "User")).strip()
        username = (data.get("username") or data.get("fullName") or "").strip()
        email = (data.get("email") or "").strip()
        domain = (
            data.get("Domain")
            or data.get("domain")
            or data.get("department")
            or ""
        ).strip()

        if designation and designation.lower() == "mentor":
            role = "mentor"
        elif not role:
            role = "User"

        if not username:
            return jsonify({"error": "Username or full name is required"}), 400
        if not email:
            return jsonify({"error": "Email is required"}), 400

        new_user = User(
            custom_id=custom_id,
            username=username,
            email=email,
            role=role,
            domain=domain,
            designation=designation,
            status=data.get("status", "Offline")
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as exc:
        db.session.rollback()
        print(f"create_user failed: {exc}")
        return jsonify({"error": "Failed to create user. Please try again."}), 500


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
@role_required("superadmin", "admin")
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    try:
        if "userId" in data: user.custom_id = data["userId"]
        if "fullName" in data and data["fullName"].strip(): user.username = data["fullName"].strip()
        if "email" in data and data["email"].strip(): user.email = data["email"].strip()
        if "password" in data and data["password"]: user.set_password(data["password"])
        if "Domain" in data or "domain" in data or "department" in data:
            user.domain = (
                data.get("Domain")
                or data.get("domain")
                or data.get("department")
                or ""
            ).strip()
        if "designation" in data:
            user.designation = data["designation"]
            if user.designation and user.designation.lower() == "mentor":
                user.role = "mentor"
        if "role" in data and not (user.designation and user.designation.lower() == "mentor"):
            user.role = data["role"]
        if "status" in data: user.status = data["status"]

        db.session.commit()
        return jsonify(user.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as exc:
        db.session.rollback()
        print(f"update_user failed: {exc}")
        return jsonify({"error": "Failed to update user. Please try again."}), 500


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
@role_required("superadmin", "admin")
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        username_to_delete = user.username
        db.session.delete(user)

        try:
            new_log = Log(
                login_time=now_ist_naive(),
                email=session.get("username", "System"),
                role=session.get("role", "System"),
                action=f"Deleted User: {username_to_delete}"
            )
            db.session.add(new_log)
        except Exception:
            pass  # Don't fail the delete if logging fails

        db.session.commit()
        return jsonify({"success": True, "message": "User deleted successfully"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to delete user. Please try again."}), 500
