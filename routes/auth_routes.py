from flask import Blueprint, request, jsonify, session
from models import db, Admin, User, Log
from sqlalchemy import or_
from utils.datetime_utils import now_ist_naive

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles login for ALL users — checks Admin table first, then User table.
    Default app-wide rate limits are enforced by Flask-Limiter.
    """

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    identifier = data.get('username', '').strip() or data.get('email', '').strip()
    password   = data.get('password', '').strip()

    if not identifier or not password:
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    # Search Admin table by username OR email
    user = Admin.query.filter(
        or_(Admin.username == identifier, Admin.email == identifier)
    ).first()

    # Fall back to User table
    if not user:
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

    if user and user.check_password(password):
        try:
            user.status = "Online"
            new_log = Log(
                login_time=now_ist_naive(),
                username=user.username,
                email=user.email,
                domain=getattr(user, 'domain', 'N/A'),
                role=user.role,
                designation=getattr(user, 'designation', 'N/A'),
                action="User Logged In"
            )
            
            db.session.add(new_log)
            db.session.commit()

            # Reset and re-issue the authenticated session cookie explicitly.
            session.clear()
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session.modified = True

            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": user.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            print(f"Login log error: {e}")
            return jsonify({"success": False, "message": "Login successful, but logging failed"}), 200

    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@auth_bp.route('/session', methods=['GET'])
def get_session():
    """
    Verifies if a user session is active and returns user data.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False, "message": "No active session"}), 401
    
    user = Admin.query.get(user_id) or User.query.get(user_id)
    
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "message": "User not found"}), 401
    
    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Handles user logout, updates status, and clears session.
    """
    try:
        username = session.get("username")
        
        # Fallback to request body if session cleared
        if not username and request.is_json:
            username = request.json.get("username")

        if username:
            user = Admin.query.filter_by(username=username).first() or \
                   User.query.filter_by(username=username).first()

            if user:
                user.status = "Offline"
                last_log = Log.query.filter_by(username=user.username)\
                                    .filter(Log.logout_time == None)\
                                    .order_by(Log.id.desc())\
                                    .first()
                
                if last_log:
                    last_log.logout_time = now_ist_naive()
                    last_log.action = "User Session Completed"
                    db.session.commit()

        session.clear()
        return jsonify({"success": True, "message": "Logged out successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error during logout"}), 500
