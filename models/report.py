from . import db


# ── Daily Report ───
class DailyReport(db.Model):
    __tablename__ = 'daily_reports'

    id           = db.Column(db.String(50), primary_key=True)
    title        = db.Column(db.String(100))
    projectName  = db.Column(db.String(100))
    designation  = db.Column(db.String(50))
    name         = db.Column(db.String(100))
    createdBy    = db.Column(db.String(100))
    status       = db.Column(db.String(20))
    date         = db.Column(db.String(20))
    day          = db.Column(db.String(20))
    reportContent = db.Column(db.Text)
    mobileNumber = db.Column(db.String(20))
    email        = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id":            self.id,
            "title":         self.title,
            "projectName":   self.projectName,
            "designation":   self.designation,
            "name":          self.name,
            "createdBy":     self.createdBy,
            "status":        self.status,
            "date":          self.date,
            "day":           self.day,
            "reportContent": self.reportContent,
            "mobileNumber":  self.mobileNumber,
            "email":         self.email,
            "type":          "Daily",
        }


# ── Weekly Report ───
class WeeklyReport(db.Model):
    __tablename__ = 'weekly_reports'

    id              = db.Column(db.String(50), primary_key=True)
    title           = db.Column(db.String(100))
    projectName     = db.Column(db.String(100))
    designation     = db.Column(db.String(50))
    name            = db.Column(db.String(100))
    createdBy       = db.Column(db.String(100))
    status          = db.Column(db.String(20))
    date            = db.Column(db.String(20))
    day             = db.Column(db.String(20))
    reportContent   = db.Column(db.Text)
    mobileNumber    = db.Column(db.String(20))
    email           = db.Column(db.String(100))
    # Weekly-only fields
    weeklySummary   = db.Column(db.Text)
    attachmentName  = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id":             self.id,
            "title":          self.title,
            "projectName":    self.projectName,
            "designation":    self.designation,
            "name":           self.name,
            "createdBy":      self.createdBy,
            "status":         self.status,
            "date":           self.date,
            "day":            self.day,
            "reportContent":  self.reportContent,
            "mobileNumber":   self.mobileNumber,
            "email":          self.email,
            "weeklySummary":  self.weeklySummary,
            "attachmentName": self.attachmentName,
            "type":           "Weekly",
        }
