from app.extension import db
from datetime import datetime, timedelta

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Subscription details
    plan_type = db.Column(db.String(20), default='free')  # 'free', 'premium'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(20), default='active')  # 'active', 'cancelled', 'expired'
    
    # Payment tracking
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
        return {
            'id': self.id,
            'plan_type': self.plan_type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'payment_status': self.payment_status,
            'is_active': self.is_active(),
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Subscription {self.plan_type} - {self.payment_status}>'
