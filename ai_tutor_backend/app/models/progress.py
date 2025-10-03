# progress tracking
from app.extension import db
from datetime import datetime

class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # progress tracking
    topic = db.Column(db.String(255), nullable=False)
    total_sessions = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    last_session_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_progress(self, new_score):
        """Update progress with a new session score"""
        total_points = self.average_score * self.total_sessions
        self.total_sessions += 1
        self.average_score = ((self.average_score * (self.total_sessions - 1)) + new_score) / self.total_sessions
        self.last_session_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert progress object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "topic": self.topic,
            "total_sessions": self.total_sessions,
            "average_score": self.average_score,
            "last_session_at": self.last_session_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    def __repr__(self):
        return f'<Progress {self.id} - {self.average_score:.2f}>'