import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
from urllib.parse import urlparse

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
    app.config.from_object(config_class)
    is_production = not app.debug

    # Cross-site session cookies must be Secure + SameSite=None on Render HTTPS.
    app.config["SESSION_COOKIE_SAMESITE"] = "None" if is_production else "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # CORS SETTINGS - Define allowed origins
    allowed_origins = [
        "https://isms-frontend.onrender.com",
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

    # Initialize CORS with comprehensive settings
    cors = CORS(
        app,
        supports_credentials=True,
        origins=allowed_origins,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        expose_headers=["Content-Range", "X-Content-Range", "Content-Length"],
        max_age=3600
    )
    
    # Add explicit CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
        return response
 
    # DATABASE 

    db.init_app(app)
 
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

if __name__ == "__main__":

    # Ensure database exists
    _create_database_if_not_exists(app.config)

    with app.app_context():

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

    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
