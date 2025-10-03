# Subscription details
from app.extension import db
from datetime import datetime, timedelta

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    # subscription details
    plan_type = db.Column(db.String(20), nullable=False)  # e.g., 'free', 'premium'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)  # null for free plans
    payment_status = db.Column(db.String(20), default='active')

    #payment tracking
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_active(self):
        """Check if subscription is currently active."""
        if self.plan_type == 'free':
            return True
        
        if self.payment_status != 'active':
            return False
            
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
            
        return True
    
    def upgrade_to_premium(self, months=1):
        """Upgrade subscription to premium."""
        self.plan_type = 'premium'
        self.start_date = datetime.utcnow()
        self.end_date = datetime.utcnow() + timedelta(days=30 * months)
        self.payment_status = 'active'

    def to_dict(self):
        """Convert subscription object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan": self.plan,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self):
        return f'<Subscription {self.id} - {self.payment_status}>'
