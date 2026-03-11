import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
from urllib.parse import urlparse
from models import db
from config import Config


def _create_database_if_not_exists(app_config):
    """Creates the database specified in the SQLAlchemy URI if it doesn't exist."""
    try:
        db_uri = app_config['SQLALCHEMY_DATABASE_URI']
        # Skip database creation check if not using MySQL (e.g., if using SQLite)
        if not db_uri or not db_uri.startswith('mysql'):
            return

        parsed_uri = urlparse(db_uri)
        db_name = parsed_uri.path.lstrip('/')
        
        # Connect to MySQL server (without specifying a database)
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
        # Exit if we can't ensure the database exists, as the app will fail anyway.
        exit(1)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Initialize Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    app.limiter = limiter # Make it accessible to blueprints

    # Ensure storage folders exist
    os.makedirs(app.config['SCREENSHOT_FOLDER'], exist_ok=True)

    # Register Blueprints
    from routes.register_routes import register_routes
    register_routes(app)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/")
    def home():
        return jsonify({
            "status": "online",
            "message": "ISMS API Server Running 🚀",
            "version": "1.0.0"
        })

    return app

app = create_app()

if __name__ == "__main__":
    # Ensure the database exists before the app tries to connect to it.
    _create_database_if_not_exists(app.config)

    with app.app_context():
        # CAUTION: Ensure db.drop_all() is NOT called here. It deletes all data on restart.
        # db.drop_all() 
        # This will create tables if they don't exist based on models
        db.create_all()
        print("✅ Database Tables Verified/Created")

        # Automatic Seeding
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
            super_admin.set_password(os.environ.get("SUPERADMIN_DEFAULT_PASSWORD", "ChangeMe@123!"))
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Default Superadmin Created")
        else:
            # Update existing superadmin to ensure designation/domain exists
            if super_admin.designation != "HR Head" or super_admin.domain != "Management":
                print("🔄 Updating Superadmin details...")
                super_admin.designation = "HR Head"
                super_admin.domain = "Management"
                db.session.commit()
                print("✅ Superadmin details updated")
    
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
