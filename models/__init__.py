from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .admin import Admin
from .report import DailyReport, WeeklyReport
from .task import Task
from .log import Log
from .activity import Activity

__all__ = ['db', 'User', 'Admin', 'DailyReport', 'WeeklyReport', 'Task', 'Log', 'Activity']
