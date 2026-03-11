from models import db
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Activity(db.Model):
    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    action = db.Column(db.String(100))
    login_time = db.Column(db.DateTime, nullable=True)
    logout_time = db.Column(db.DateTime, nullable=True)
    idle_time = db.Column(db.Integer, nullable=True)
    screenshot_path = db.Column(db.String(255), nullable=True)
    app_url = db.Column(db.String(255), nullable=True)
    activity_metadata = db.Column("metadata", db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(IST)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "action": self.action,
            "login_time": self.login_time,
            "logout_time": self.logout_time,
            "idle_time": self.idle_time,
            "screenshot_path": self.screenshot_path,
            "app_url": self.app_url,
            "metadata": self.activity_metadata,
            "created_at": self.created_at
        }