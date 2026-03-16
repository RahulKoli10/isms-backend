import os
import sqlite3
from datetime import timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.engine import make_url
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from models import Admin, db


def _sync_sqlite_legacy_schema(database_uri):
    if not database_uri or not database_uri.startswith("sqlite:///"):
        return

    sqlite_path = database_uri.replace("sqlite:///", "", 1)
    if not os.path.exists(sqlite_path):
        return

    connection = sqlite3.connect(sqlite_path)
    try:
        cursor = connection.cursor()
        table_exists = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not table_exists:
            return

        user_columns = {
            row[1]: row for row in cursor.execute("PRAGMA table_info(users)").fetchall()
        }
        expected_columns = {"custom_id", "domain", "designation"}
        has_legacy_layout = (
            not expected_columns.issubset(user_columns.keys())
            or user_columns.get("id", (None, None, ""))[2].upper() != "INTEGER"
        )
        if not has_legacy_layout:
            return

        cursor.execute("ALTER TABLE users RENAME TO users_legacy")
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id VARCHAR(50),
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'User',
                domain VARCHAR(50) DEFAULT '',
                designation VARCHAR(50) DEFAULT '',
                status VARCHAR(20) DEFAULT 'Offline'
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO users (username, email, password, role, domain, designation, status)
            SELECT
                username,
                COALESCE(email, username || '@isms.local'),
                password,
                COALESCE(role, 'User'),
                COALESCE(department, ''),
                '',
                CASE
                    WHEN status IS NULL OR status = '' THEN 'Offline'
                    WHEN LOWER(status) = 'active' THEN 'Online'
                    ELSE status
                END
            FROM users_legacy
            """
        )
        connection.commit()
        print("Legacy SQLite users table migrated to current schema.")
    finally:
        connection.close()


def _create_database_if_not_exists(database_uri):
    if not database_uri:
        return

    try:
        parsed_uri = make_url(database_uri)
    except Exception:
        return

    if not parsed_uri.drivername.startswith("mysql"):
        return

    try:
        import mysql.connector

        db_name = parsed_uri.database
        connection = mysql.connector.connect(
            host=parsed_uri.host,
            user=parsed_uri.username,
            password=parsed_uri.password,
            port=parsed_uri.port or 3306,
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cursor.close()
        connection.close()
        print(f"Database '{db_name}' verified/created.")
    except Exception as exc:
        raise RuntimeError(f"Database creation/verification failed: {exc}") from exc


def _seed_default_superadmin():
    super_admin = Admin.query.filter_by(username="superadmin").first()

    if not super_admin:
        super_admin = Admin(
            username="superadmin",
            email="superadmin@isms.com",
            role="superadmin",
            status="Offline",
            custom_id="SA/IN/24/0001",
            domain="Management",
            designation="HR Head",
        )
        super_admin.set_password(
            os.environ.get("SUPERADMIN_DEFAULT_PASSWORD", "ChangeMe@123!")
        )
        db.session.add(super_admin)
        db.session.commit()
        print("Default superadmin created.")
        return

    if super_admin.designation != "HR Head" or super_admin.domain != "Management":
        super_admin.designation = "HR Head"
        super_admin.domain = "Management"
        db.session.commit()
        print("Default superadmin details updated.")


def initialize_database(app):
    with app.app_context():
        _create_database_if_not_exists(app.config["SQLALCHEMY_DATABASE_URI"])
        _sync_sqlite_legacy_schema(app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        _seed_default_superadmin()
        print("Database schema verified.")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config.from_object(config_class)

    if app.config["IS_PRODUCTION"]:
        insecure_defaults = {
            "dev-secret-key-change-me",
            "dev-jwt-secret-change-me",
        }
        if app.config["SECRET_KEY"] in insecure_defaults:
            raise RuntimeError("SECRET_KEY must be set for production deployments.")
        if app.config["JWT_SECRET_KEY"] in insecure_defaults:
            raise RuntimeError("JWT_SECRET_KEY must be set for production deployments.")

    app.permanent_session_lifetime = timedelta(hours=8)

    session_same_site = str(app.config.get("SESSION_COOKIE_SAMESITE", "Lax")).strip().capitalize()
    if session_same_site not in {"Lax", "Strict", "None"}:
        session_same_site = "Lax"
    app.config["SESSION_COOKIE_SAMESITE"] = session_same_site
    app.config["SESSION_COOKIE_SECURE"] = bool(app.config.get("SESSION_COOKIE_SECURE", False))
    app.config["SESSION_COOKIE_PARTITIONED"] = bool(
        app.config.get("SESSION_COOKIE_PARTITIONED", False)
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    allowed_origins = list(dict.fromkeys(app.config.get("ALLOWED_ORIGINS", [])))
    print(f"CORS allowed origins: {allowed_origins}")

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        max_age=3600,
        vary_header=True,
    )

    db.init_app(app)

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["10000 per day", "5000 per hour"],
        storage_uri="memory://",
    )
    app.limiter = limiter

    os.makedirs(app.config["SCREENSHOT_FOLDER"], exist_ok=True)

    @app.before_request
    def _enforce_allowed_origins():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        origin = request.headers.get("Origin")
        if origin and origin.rstrip("/") not in allowed_origins:
            return jsonify({"error": "Origin is not allowed"}), 403

        return None

    from routes.register_routes import register_routes

    register_routes(app)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/")
    def home():
        return jsonify(
            {
                "status": "online",
                "message": "ISMS API server running",
                "version": "1.0.0",
            }
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    return app


app = create_app()

if os.environ.get("AUTO_INIT_DB_ON_START", "").strip().lower() in {"true", "1", "yes", "on"}:
    initialize_database(app)


if __name__ == "__main__":
    initialize_database(app)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
