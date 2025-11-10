# subscription checks, rolebased access
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User, Subscription

def premium_required(f):
    """
    Decorator to require premium subscription for endpoint access
    Use after @jwt_required()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(int(current_user_id))

            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            #check subscription
            subscription = Subscription.query.filter_by(user_id=user.id).first()
            #check if is premium
            if not subscription or subscription.plan_type == 'free':
                return jsonify({
                    'error': 'Premium subscription required',
                    'message': 'This feature is only available to premium users',
                    'upgrade_url': '/api/subscription/plans',
                    'current_plan': 'free'
                }), 403
            #check if subscription is active

            if not subscription.is_active():
                return jsonify({
                    'error': 'Subscription expired',
                    'message': 'Your premium subscription has expired. Please renew.',
                    'upgrade_url': '/api/subscription/plans'
                }), 403
            
            # User is premium and active, proceed
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': f'Authorization failed: {str(e)}'}), 500
    
    return decorated_function

def check_feature_access(feature_name):
    """
    Check if user has access to a specific feature
    Returns: (has_access: bool, message: str)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        if not user:
            return False, "User not found"
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        if not subscription or subscription.plan_type == 'free':
            return False, f"{feature_name} is a premium feature"
        
        if not subscription.is_active():
            return False, "Your subscription has expired"
        
        return True, "Access granted"
        
    except Exception as e:
        return False, str(e)
    