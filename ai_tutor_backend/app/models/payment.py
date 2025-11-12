from app.extension import db
from datetime import datetime

class Payment(db.Model):
    """Track M-Pesa payment transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # M-Pesa transaction details
    checkout_request_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    merchant_request_id = db.Column(db.String(100), nullable=True)
    mpesa_receipt_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    
    # Payment details
    amount = db.Column(db.Integer, nullable=False)  # Amount in KES
    phone_number = db.Column(db.String(20), nullable=False)
    account_reference = db.Column(db.String(100), nullable=True)
    transaction_desc = db.Column(db.String(255), nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled, failed, timeout
    result_code = db.Column(db.String(10), nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)
    
    # Subscription details
    plan_type = db.Column(db.String(20), nullable=True)  # monthly, yearly
    subscription_activated = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def mark_completed(self, mpesa_receipt_number=None, result_code=None, result_desc=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.subscription_activated = True
        self.completed_at = datetime.utcnow()
        if mpesa_receipt_number:
            self.mpesa_receipt_number = mpesa_receipt_number
        if result_code:
            self.result_code = result_code
        if result_desc:
            self.result_desc = result_desc
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, result_code=None, result_desc=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if result_code:
            self.result_code = result_code
        if result_desc:
            self.result_desc = result_desc
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self):
        """Mark payment as cancelled"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
    
    def mark_timeout(self):
        """Mark payment as timed out"""
        self.status = 'timeout'
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'checkout_request_id': self.checkout_request_id,
            'merchant_request_id': self.merchant_request_id,
            'mpesa_receipt_number': self.mpesa_receipt_number,
            'amount': self.amount,
            'phone_number': self.phone_number,
            'status': self.status,
            'plan_type': self.plan_type,
            'subscription_activated': self.subscription_activated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.status} - {self.amount} KES>'

