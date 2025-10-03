from app.extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash= db.Column(db.String(128), nullable=False)
    subscription_status = db.Column(db.String(50), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    responses = db.relationship('Response', backref='user', lazy=True, cascade="all, delete-orphan")
    progress = db.relationship('Progress', backref='user', lazy=True, cascade="all, delete-orphan")
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        #hash and set the user's password
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        #check if the password matches the password hash
        return check_password_hash(self.password_hash, password)
    
    # check if user is premium
    def is_premium(self):
        return self.subscription_status == 'premium'
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "subscription_status": self.subscription_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
def __repr__(self):
    return f'<User {self.email}>'