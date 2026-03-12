import os
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "secret_key_123_change_in_production"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        'mysql+mysqlconnector://admin:password@localhost:3306/isms'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Storage Configuration
    SCREENSHOT_FOLDER = os.path.join(BASE_DIR, os.environ.get("SCREENSHOT_FOLDER", "storage/screenshots"))

    # CORS
    # Handle both string and list formats for ALLOWED_ORIGINS
    allowed_origins_env = os.environ.get(
        "ALLOWED_ORIGINS",
        "https://isms-frontend.onrender.com,http://localhost:5173,http://localhost:3000",
    )
    # Split by comma and filter empty strings
    ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    if not ALLOWED_ORIGINS:
        ALLOWED_ORIGINS = [
            "https://isms-frontend.onrender.com",
            "http://localhost:5173",
            "http://localhost:3000",
        ]

    # App
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
    PORT = int(os.environ.get("PORT", 5000))

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt_secret_change_in_production"
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    # Razorpay
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
