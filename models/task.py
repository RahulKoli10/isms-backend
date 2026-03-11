from . import db

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    assignedTo = db.Column(db.String(100))
    userId = db.Column(db.String(100))
    deadline = db.Column(db.String(20))
    priority = db.Column(db.String(20))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))
    createdAt = db.Column(db.String(50))
    isChecked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "assignedTo": self.assignedTo,
            "userId": self.userId,
            "deadline": self.deadline,
            "priority": self.priority,
            "description": self.description,
            "status": self.status,
            "createdAt": self.createdAt,
            "isChecked": self.isChecked
        }
