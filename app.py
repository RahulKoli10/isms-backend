import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
from flask_session import Session
import mysql.connector
from urllib.parse import urlparse
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db
from config import Config

 
# CREATE DATABASE IF NOT EXISTS 

def _create_database_if_not_exists(app_config):
    """Creates the database specified in the SQLAlchemy URI if it doesn't exist."""

    try:

        db_uri = app_config["SQLALCHEMY_DATABASE_URI"]

        if not db_uri or not db_uri.startswith("mysql"):
            return

        parsed_uri = urlparse(db_uri)
        db_name = parsed_uri.path.lstrip("/")

        mydb = mysql.connector.connect(
            host=parsed_uri.hostname,
            user=parsed_uri.username,
            password=parsed_uri.password,
            port=parsed_uri.port or 3306
        )

        cursor = mydb.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")

        print(f"✅ Database '{db_name}' verified/created.")

    except mysql.connector.Error as err:

        print(f"❌ Database creation/verification failed: {err}")
        exit(1)


def create_app(config_class=Config):

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config.from_object(config_class)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # 🎯 PRODUCTION SESSION FIX: 8hr persistent sessions
    app.permanent_session_lifetime = timedelta(hours=8)
    app.config['SESSION_PERMANENT'] = True

    # Cross-site browser auth requires an explicit cookie policy.
    session_same_site = str(app.config.get("SESSION_COOKIE_SAMESITE", "None")).strip().capitalize()
    if session_same_site not in {"Lax", "Strict", "None"}:
        session_same_site = "None"
    app.config["SESSION_COOKIE_SAMESITE"] = session_same_site
    app.config["SESSION_COOKIE_SECURE"] = bool(app.config.get("SESSION_COOKIE_SECURE", True))
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # CORS SETTINGS - Define allowed origins
    allowed_origins = [
        "https://isms-frontend-hsz2.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    # Allow overriding from environment variable
    env_origins = os.environ.get("ALLOWED_ORIGINS")
    if env_origins:
        allowed_origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    
    # Also check config
    config_origins = app.config.get("ALLOWED_ORIGINS", [])
    if config_origins:
        allowed_origins = config_origins
    
    print(f"🔧 CORS Allowed Origins: {allowed_origins}")

    # Initialize CORS with comprehensive settings for credentials support
    CORS(
        app,
        resources={
            r"/api/*": {"origins": allowed_origins},
            r"/": {"origins": allowed_origins}
        },
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cookie", "Set-Cookie"],
        expose_headers=["Content-Range", "X-Content-Range", "Content-Length", "Set-Cookie"],
        max_age=3600,
        vary_header=True
    )
 
    # DATABASE 

    db.init_app(app)
    Session(app)
 
    # RATE LIMITER 

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["1000 per day", "300 per hour"],
        storage_uri="memory://",
    )

    app.limiter = limiter
 
    # ENSURE STORAGE FOLDERS EXIST 

    os.makedirs(app.config["SCREENSHOT_FOLDER"], exist_ok=True)
 
    # REGISTER ROUTES 

    from routes.register_routes import register_routes
    register_routes(app)
 
    # ERROR HANDLERS 

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404


    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    # 🛠️ DEBUG ENDPOINT - REMOVE AFTER FIX
    @app.route("/api/debug-session")
    def debug_session():
        return jsonify({
            "session_keys": list(session.keys()),
            "user_id": session.get("user_id"),
            "username": session.get("username"), 
            "role": session.get("role"),
            "cookies_present": bool(request.cookies.get(app.secret_key[:4] + "!!")),  
            "all_cookies": dict(request.cookies),
            "permanent": getattr(session, 'permanent', False)
        })

    # HEALTH CHECK ROUTE 
    @app.route("/")
    def home():
        return jsonify({
            "status": "online",
            "message": "ISMS API Server Running 🚀",
            "version": "1.0.0"
        })

    return app

 
# START APPLICATION 
app = create_app()

def setup_database():
    with app.app_context():
        # Ensure database exists (for MySQL)
        _create_database_if_not_exists(app.config)
        db.create_all()
        print("✅ Database Tables Verified/Created")

        # AUTO CREATE SUPERADMIN 
        from models import Admin
        super_admin = Admin.query.filter_by(username="superadmin").first()

        if not super_admin:
            print("🌱 Seeding default Superadmin...")
            super_admin = Admin(
                username="superadmin",
                email="superadmin@isms.com",
                role="superadmin",
                status="Offline",
                custom_id="SA/IN/24/0001",
                domain="Management",
                designation="HR Head"
            )
            super_admin.set_password(
                os.environ.get("SUPERADMIN_DEFAULT_PASSWORD", "ChangeMe@123!")
            )
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Default Superadmin Created")
        else:
            if super_admin.designation != "HR Head" or super_admin.domain != "Management":
                print("🔄 Updating Superadmin details...")
                super_admin.designation = "HR Head"
                super_admin.domain = "Management"
                db.session.commit()
                print("✅ Superadmin details updated")

# Run DB setup during import/initialization phase for production safety
setup_database()

if __name__ == "__main__":
    # Local development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
