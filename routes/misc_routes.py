from flask import Blueprint, jsonify
from models import Log
from auth_middleware import login_required, role_required

misc_bp = Blueprint('misc', __name__)

@misc_bp.route("/logs", methods=["GET"])
@login_required
def get_logs():
    """Returns last 20 logs. Requires login."""
    logs = Log.query.order_by(Log.id.desc()).limit(20).all()
    return jsonify([l.to_dict() for l in logs])

@misc_bp.route("/mentors/performance", methods=["GET"])
@login_required
def get_mentor_performance():
    mentors = []
    return jsonify(mentors)
