from . import db

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    login_time = db.Column(db.String(50))
    logout_time = db.Column(db.String(50))
    email = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    role = db.Column(db.String(20))
    designation = db.Column(db.String(50))
    action = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "login_time": self.login_time,
            "logout_time": self.logout_time,
            "timestamp": self.login_time or self.logout_time,  # Frontend compatibility
            "email": self.email,
            "domain": self.domain,
            "role": self.role,
            "designation": self.designation,
            "action": self.action
        }
