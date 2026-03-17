from . import db
from utils.datetime_utils import to_ist_iso

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    login_time = db.Column(db.DateTime)
    logout_time = db.Column(db.DateTime)
    email = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    role = db.Column(db.String(20))
    designation = db.Column(db.String(50))
    action = db.Column(db.String(255))

    def to_dict(self):
        normalized_action = (self.action or "").strip().lower()
        is_logout_action = (
            "logout" in normalized_action
            or "log out" in normalized_action
            or "logged out" in normalized_action
            or "session completed" in normalized_action
            or "session end" in normalized_action
        )

        return {
            "id": self.id,
            "username": self.username,
            "login_time": to_ist_iso(self.login_time),
            "logout_time": to_ist_iso(self.logout_time),
            "timestamp": (
                to_ist_iso(self.logout_time)
                if is_logout_action and self.logout_time
                else (to_ist_iso(self.login_time) or to_ist_iso(self.logout_time))
            ),
            "email": self.email,
            "domain": self.domain,
            "role": self.role,
            "designation": self.designation,
            "action": self.action
        }
