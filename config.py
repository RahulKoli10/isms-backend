import os
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_bool(name, default=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"true", "1", "yes", "on"}


def _normalize_database_url(database_url):
    if not database_url:
        sqlite_path = os.path.join(BASE_DIR, "database.db").replace("\\", "/")
        return f"sqlite:///{sqlite_path}"

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


class Config:
    IS_PRODUCTION = _get_bool("IS_PRODUCTION", default=_get_bool("RENDER", default=False))
    DEBUG = _get_bool("DEBUG", default=False)

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")

    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 280)),
    }

    SCREENSHOT_FOLDER = os.path.join(
        BASE_DIR,
        os.environ.get("SCREENSHOT_FOLDER", "storage/screenshots"),
    )

    allowed_origins_env = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    ALLOWED_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in allowed_origins_env.split(",")
        if origin.strip()
    ]

    PORT = int(os.environ.get("PORT", 5000))
    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"

    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "isms_session")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _get_bool("SESSION_COOKIE_SECURE", default=IS_PRODUCTION)
    SESSION_COOKIE_SAMESITE = os.environ.get(
        "SESSION_COOKIE_SAMESITE",
        "None" if IS_PRODUCTION else "Lax",
    )
    SESSION_PERMANENT = True

    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
