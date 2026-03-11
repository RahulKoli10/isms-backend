from .auth_routes import auth_bp
from .admin_routes import admins_bp
from .user_routes import users_bp
from .log_routes import logs_bp
from .report_routes import DailyReport_bp, WeeklyReport_bp
from .task_routes import task_bp
from .activity_routes import activity_bp
from .misc_routes import misc_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(admins_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(logs_bp, url_prefix='/api')
    app.register_blueprint(DailyReport_bp, url_prefix='/api')
    app.register_blueprint(WeeklyReport_bp, url_prefix='/api')
    app.register_blueprint(task_bp, url_prefix='/api')
    app.register_blueprint(activity_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')
