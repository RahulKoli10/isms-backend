# User Model
from . import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    custom_id = db.Column(db.String(50))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="User")
    domain = db.Column(db.String(50), default="")
    designation = db.Column(db.String(50), default="")
    status = db.Column(db.String(20), default="Offline")

    # 🔐 Secure password storage
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            "id": self.id,
            "custom_id": self.custom_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "domain": self.domain,
            "designation": self.designation,
            "status": self.status
        }
