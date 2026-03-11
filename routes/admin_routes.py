from flask import Blueprint, request, jsonify, session
import datetime
import os
from models import db, Admin, Log
from auth_middleware import login_required, role_required

admins_bp = Blueprint('admins', __name__)

def generate_admin_id(role):
    """Generates a custom ID for admin roles."""
    prefix = {
        'superadmin': 'SA',
        'admin': 'AD',
        'mentor': 'MT'
    }.get(role.lower(), 'AD')

    count = Admin.query.filter(Admin.role.ilike(role)).count()
    year_short = datetime.datetime.now().strftime("%y")
    return f"{prefix}/IN/{year_short}/{str(count + 1).zfill(4)}"

@admins_bp.route("/admins", methods=["GET"])
@login_required
def get_admins():
    """Get all admins, optionally filtered by role."""
    role_filter = request.args.get("role")
    query = Admin.query
    if role_filter:
        query = query.filter(Admin.role.ilike(f"%{role_filter}%"))
    admins = query.all()
    return jsonify([admin.to_dict() for admin in admins])

@admins_bp.route("/admins", methods=["POST"])
@login_required
@role_required("superadmin", "admin")
def create_admin():
    """Create a new admin or mentor."""
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    try:
        designation = data.get("designation")
        role = data.get("role", "admin")

        if designation and designation.lower() == "mentor":
            role = "mentor"

        custom_id = data.get("adminId") or generate_admin_id(role)
        username = data.get("username") or data.get("fullName")

        # Require a password — no default
        password = data.get("password")
        if not password or len(password) < 6:
            return jsonify({"error": "A password of at least 6 characters is required"}), 400

        new_admin = Admin(
            custom_id=custom_id,
            username=username,
            email=data.get("email"),
            role=role,
            domain=data.get("Domain"),
            designation=designation,
            status=data.get("status", "Offline")
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        return jsonify(new_admin.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to create admin. Please try again."}), 500


@admins_bp.route("/admins/<int:admin_id>", methods=["PUT"])
@login_required
@role_required("superadmin", "admin")
def update_admin(admin_id):
    """Update an existing admin."""
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    try:
        if "adminId" in data: admin.custom_id = data["adminId"]
        if "fullName" in data: admin.username = data["fullName"]
        if "email" in data: admin.email = data["email"]
        if "password" in data and data["password"]: admin.set_password(data["password"])
        if "role" in data: admin.role = data["role"]
        if "Domain" in data: admin.domain = data["Domain"]
        if "designation" in data:
            admin.designation = data["designation"]
            if admin.designation and admin.designation.lower() == "mentor":
                admin.role = "mentor"
        if "status" in data: admin.status = data["status"]

        db.session.commit()
        return jsonify(admin.to_dict()), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to update admin. Please try again."}), 500


@admins_bp.route("/admins/<int:admin_id>", methods=["DELETE"])
@login_required
@role_required("superadmin")
def delete_admin(admin_id):
    """Delete an admin. Superadmin only."""
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    try:
        db.session.delete(admin)
        db.session.commit()
        return jsonify({"success": True, "message": "Admin deleted successfully"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to delete admin. Please try again."}), 500

# Removed redundant login/logout routes - now handled by auth_routes.py