from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Log(db.Model):
    __tablename__ = 'logs'
    user_id = db.Column(db.String(50), primary_key=True)
    activity = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meta_data = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<Log {self.user_id} - {self.activity}>'
