# learner input + AI feedback
from app.extension import db
from datetime import datetime

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # learning content
    concept = db.Column(db.String(255), nullable=False)
    learner_input = db.Column(db.Text, nullable=False)
    ai_feedback = db.Column(db.Text, nullable=True)

    #understanding score
    understanding_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def to_dict(self):
        """Convert response object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "concept": self.concept,
            "learner_input": self.learner_input,
            "ai_feedback": self.ai_feedback,
            "understanding_score": self.understanding_score,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f'<Response {self.id}, {self.concept}>'
