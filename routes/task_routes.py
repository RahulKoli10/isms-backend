from flask import Blueprint, request, jsonify, session
from models import db, Task
from auth_middleware import login_required, role_required
import datetime
from utils.datetime_utils import now_ist_iso

task_bp = Blueprint('task', __name__)

@task_bp.route("/tasks", methods=["GET", "POST"])
@login_required
def handle_tasks():
    if request.method == "GET":
        try:
            tasks = Task.query.order_by(Task.id.desc()).all()
            return jsonify([t.to_dict() for t in tasks])
        except Exception:
            return jsonify({"error": "Failed to fetch tasks."}), 500

    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400
            
        new_task = Task(
            title=data.get("title"),
            domain=data.get("domain"),
            assignedTo=data.get("assignedTo"),
            userId=data.get("userId"),
            deadline=data.get("deadline"),
            priority=data.get("priority"),
            description=data.get("description"),
            status=data.get("status", "Pending"),
            createdAt=data.get("createdAt", now_ist_iso())
        )
        try:
            db.session.add(new_task)
            db.session.commit()
            return jsonify(new_task.to_dict()), 201
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Failed to create task."}), 500

@task_bp.route("/tasks/<int:task_id>", methods=["PUT", "DELETE"])
@login_required
def handle_task_item(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    if request.method == "PUT":
        data = request.json
        try:
            if "title" in data: task.title = data["title"]
            if "status" in data: task.status = data["status"]
            if "isChecked" in data: task.isChecked = data["isChecked"]
            if "priority" in data: task.priority = data["priority"]
            if "deadline" in data: task.deadline = data["deadline"]
            
            db.session.commit()
            return jsonify(task.to_dict())
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Failed to update task."}), 500

    if request.method == "DELETE":
        # Restrict deletion to admins
        @role_required("superadmin", "admin", "mentor")
        def delete_task():
            try:
                db.session.delete(task)
                db.session.commit()
                return jsonify({"success": True, "message": "Task deleted"})
            except Exception:
                db.session.rollback()
                return jsonify({"error": "Failed to delete task."}), 500
        return delete_task()
