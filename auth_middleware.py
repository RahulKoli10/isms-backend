from functools import wraps
from flask import request, jsonify, session


def login_required(f):
    """
    Decorator to protect routes — requires a valid session.
    Apply to any route that should only be accessible after login.
    Usage:
        @app.route('/admins')
        @login_required
        def get_admins():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({
                "success": False,
                "message": "Authentication required. Please log in."
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator to restrict routes by role.
    Usage:
        @app.route('/admins', methods=['DELETE'])
        @login_required
        @role_required('superadmin', 'admin')
        def delete_admin(admin_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role", "")
            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "Access denied. Insufficient permissions."
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
