# app/routes/subscription.py - Daraja M-Pesa Integration

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Subscription, Payment
from app.extension import db
from datetime import datetime, timedelta
from app.services.payment_service import MpesaService
import os
import logging

# Set up logger
logger = logging.getLogger(__name__)

subscription_bp = Blueprint('subscription', __name__)

# Initialize M-Pesa service
mpesa = MpesaService()

# Pricing configuration
PRICING = {
    'monthly': {
        'kes': 300,
        'duration_days': 30
    },
    'yearly': {
        'kes': 3600,
        'duration_days': 365
    }
}


@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available subscription plans"""
    return jsonify({
        'plans': [
            {
                'id': 'free',
                'name': 'Free',
                'price_kes': 0,
                'features': [
                    '5 AI feedback requests per day',
                    'Basic progress tracking',
                    'Learning history'
                ]
            },
            {
                'id': 'monthly',
                'name': 'Premium Monthly',
                'price_kes': PRICING['monthly']['kes'],
                'duration': '30 days',
                'features': [
                    'Unlimited AI feedback',
                    'Advanced analytics',
                    'Priority support'
                ],
                'popular': True
            },
            {
                'id': 'yearly',
                'name': 'Premium Yearly',
                'price_kes': PRICING['yearly']['kes'],
                'duration': '365 days',
                'savings': '17% off',
                'features': [
                    'All Premium features',
                    'Early access to features'
                ],
                'best_value': True
            }
        ],
        'payment_method': 'M-Pesa (Lipa Na M-Pesa)',
        'currency': 'KES'
    }), 200


@subscription_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Get current subscription status"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()

        if not subscription:
            subscription = Subscription()
            subscription.user_id = user.id
            subscription.plan_type = 'free'
            subscription.payment_status = 'active'
            db.session.add(subscription)
            db.session.commit()

        # Calculate usage for free users
        usage = None
        if subscription.plan_type == 'free':
            from app.models import Response
            from datetime import date

            today_count = Response.query.filter(
                Response.user_id == user.id,
                db.func.date(Response.created_at) == date.today()
            ).count()

            usage = {
                'requests_used_today': today_count,
                'requests_limit': 5,
                'requests_remaining': max(0, 5 - today_count)
            }

        return jsonify({
            'subscription': subscription.to_dict(),
            'usage': usage,
            'can_upgrade': subscription.plan_type == 'free'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get subscription: {str(e)}'}), 500


@subscription_bp.route('/initiate-mpesa', methods=['POST'])
@jwt_required()
def initiate_mpesa_payment():
    """
    Initiate M-Pesa STK Push
    Request: {
        "plan": "monthly" or "yearly",
        "phone_number": "0712345678" or "254712345678"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404
    
        data = request.get_json()
        plan = data.get('plan', 'monthly')
        phone_number = data.get('phone_number', '').strip()

        # Validation
        if plan not in PRICING:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Validate and format phone number
        formatted_phone = mpesa.validate_phone_number(phone_number)
        if not formatted_phone:
            return jsonify({
                'error': 'Invalid phone number. Use format: 0712345678 or 254712345678'
            }), 400
    
        # Get pricing
        amount = PRICING[plan]['kes']
        
        # Create account reference (user ID)
        account_reference = f"USER{user.id}"
        transaction_desc = f"AI Tutor {plan.title()} Subscription"
        
        # Initiate STK Push
        result = mpesa.initiate_stk_push(
            phone_number=formatted_phone,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        if result.get('success'):
            # Create payment record
            checkout_request_id = result.get('checkout_request_id')
            merchant_request_id = result.get('merchant_request_id')
            
            payment = Payment(
                user_id=user.id,
                checkout_request_id=checkout_request_id,
                merchant_request_id=merchant_request_id,
                amount=amount,
                phone_number=formatted_phone,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                plan_type=plan,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            logger.info(f"Payment initiated for user {user.id}. CheckoutRequestID: {checkout_request_id}, Amount: {amount} KES")
            
            return jsonify({
                'success': True,
                'checkout_request_id': checkout_request_id,
                'payment_id': payment.id,
                'message': 'M-Pesa payment request sent to your phone',
                'amount': amount,
                'phone_number': formatted_phone,
                'instructions': [
                    '1. Check your phone for M-Pesa prompt',
                    '2. Enter your M-Pesa PIN',
                    '3. Wait for SMS confirmation',
                    '4. Your subscription will be activated automatically'
                ]
            }), 200
        else:
            logger.error(f"Failed to initiate payment for user {user.id}: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Payment initiation failed')
            }), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Exception initiating payment for user {user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to initiate payment: {str(e)}'}), 500


@subscription_bp.route('/check-payment', methods=['POST'])
@jwt_required()
def check_payment_status():
    """
    Check M-Pesa payment status
    Request: {"checkout_request_id": "ws_CO_xxx"}
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        checkout_request_id = data.get('checkout_request_id')

        if not checkout_request_id:
            return jsonify({'error': 'checkout_request_id required'}), 400

        # Find payment record
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id, user_id=user.id).first()
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Query transaction status from M-Pesa
        result = mpesa.query_stk_status(checkout_request_id)
        
        if result.get('success'):
            status = result.get('status')
            result_code = result.get('result_code')
            result_desc = result.get('result_desc', '')
            
            # Update payment record status if changed
            if status == 'COMPLETED' and payment.status != 'completed':
                # Check if callback already processed this
                if not payment.subscription_activated:
                    # Manually trigger subscription activation if callback missed it
                    payment.mark_completed(
                        result_code=result_code,
                        result_desc=result_desc
                    )
                    
                    subscription = Subscription.query.filter_by(user_id=user.id).first()
                    if not subscription:
                        subscription = Subscription()
                        subscription.user_id = user.id
                        db.session.add(subscription)
                    
                    plan = payment.plan_type or 'monthly'
                    duration_days = PRICING[plan]['duration_days']
                    subscription.upgrade_to_premium(months=(duration_days // 30))
                    user.subscription_status = 'premium'
                    
                    db.session.commit()
                    logger.info(f"Payment completed via status check for user {user.id}")
            elif status == 'CANCELLED' and payment.status != 'cancelled':
                payment.mark_cancelled()
                db.session.commit()
            elif status == 'TIMEOUT' and payment.status != 'timeout':
                payment.mark_timeout()
                db.session.commit()
            elif status == 'FAILED' and payment.status != 'failed':
                payment.mark_failed(
                    result_code=result_code,
                    result_desc=result_desc
                )
                db.session.commit()
            
            return jsonify({
                'success': True,
                'status': status,
                'completed': status == 'COMPLETED',
                'message': {
                    'PENDING': 'Payment pending. Please complete the M-Pesa prompt.',
                    'COMPLETED': 'Payment successful! Subscription activated.',
                    'CANCELLED': 'Payment was cancelled.',
                    'TIMEOUT': 'Payment request timed out. Please try again.',
                    'FAILED': 'Payment failed. Please try again.'
                }.get(status, 'Unknown status'),
                'result_desc': result_desc,
                'payment': payment.to_dict()
            }), 200
        else:
            logger.error(f"Failed to query payment status: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 500

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    """
    M-Pesa callback endpoint - receives payment notifications from Safaricom
    This endpoint is called by Safaricom's servers when payment status changes.
    """
    try:
        # Get callback data
        data = request.get_json()
        
        logger.info(f"M-Pesa callback received: {data}")
        
        if not data:
            logger.warning("Empty callback data received")
            return jsonify({
                'ResultCode': 1,
                'ResultDesc': 'Invalid request'
            }), 200
        
        # Extract callback data
        body = data.get('Body', {}).get('stkCallback', {})
        if not body:
            logger.warning(f"Invalid callback structure: {data}")
            return jsonify({
                'ResultCode': 1,
                'ResultDesc': 'Invalid callback structure'
            }), 200
        
        result_code = body.get('ResultCode')
        checkout_request_id = body.get('CheckoutRequestID')
        result_desc = body.get('ResultDesc', '')
        
        logger.info(f"Callback for CheckoutRequestID: {checkout_request_id}, ResultCode: {result_code}")
        
        # Find payment record
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
        
        if not payment:
            logger.error(f"Payment not found for checkout_request_id: {checkout_request_id}")
            # Still return success to Safaricom to avoid retries
            return jsonify({
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            }), 200
        
        # Handle different result codes
        if result_code == 0:
            # Payment successful
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            
            # Extract payment details
            amount = None
            phone_number = None
            mpesa_receipt = None
            
            for item in callback_metadata:
                name = item.get('Name')
                if name == 'Amount':
                    amount = item.get('Value')
                elif name == 'PhoneNumber':
                    phone_number = item.get('Value')
                elif name == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
            
            # Update payment record
            payment.mark_completed(
                mpesa_receipt_number=mpesa_receipt,
                result_code=str(result_code),
                result_desc=result_desc
            )
            
            # Determine plan from amount
            if amount:
                if amount >= 3600:
                    plan = 'yearly'
                else:
                    plan = 'monthly'
            else:
                plan = payment.plan_type or 'monthly'
            
            # Activate subscription
            user = User.query.get(payment.user_id)
            if user:
                subscription = Subscription.query.filter_by(user_id=user.id).first()
                if not subscription:
                    subscription = Subscription()
                    subscription.user_id = user.id
                    db.session.add(subscription)
                
                # Calculate duration
                duration_days = PRICING[plan]['duration_days']
                subscription.upgrade_to_premium(months=(duration_days // 30))
                user.subscription_status = 'premium'
                
                db.session.commit()
                
                logger.info(f"Payment completed and subscription activated for user {user.id}. "
                          f"Receipt: {mpesa_receipt}, Amount: {amount} KES, Plan: {plan}")
            else:
                logger.error(f"User {payment.user_id} not found for payment {payment.id}")
                db.session.commit()
        else:
            # Payment failed, cancelled, or timed out
            if result_code == 1032:
                payment.mark_cancelled()
                logger.info(f"Payment cancelled by user. CheckoutRequestID: {checkout_request_id}")
            elif result_code == 1037:
                payment.mark_timeout()
                logger.warning(f"Payment request timed out. CheckoutRequestID: {checkout_request_id}")
            else:
                payment.mark_failed(
                    result_code=str(result_code),
                    result_desc=result_desc
                )
                logger.error(f"Payment failed. CheckoutRequestID: {checkout_request_id}, "
                           f"ResultCode: {result_code}, Description: {result_desc}")
            
            db.session.commit()
        
        # Always return success to Safaricom (to acknowledge receipt)
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}", exc_info=True)
        # Still return success to Safaricom to avoid retries
        # But log the error for investigation
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200


@subscription_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_subscription():
    """
    Manually upgrade (for testing or after payment verification)
    Request: {"plan": "monthly" or "yearly"}
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        plan = data.get('plan', 'monthly')
        
        if plan not in PRICING:
            return jsonify({'error': 'Invalid plan'}), 400
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        if not subscription:
            subscription = Subscription()
            subscription.user_id = user.id
            db.session.add(subscription)
        
        duration_days = PRICING[plan]['duration_days']
        subscription.upgrade_to_premium(months=(duration_days // 30))
        user.subscription_status = 'premium'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription upgraded successfully',
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to upgrade: {str(e)}'}), 500


@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel premium subscription"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or subscription.plan_type == 'free':
            return jsonify({'error': 'No active premium subscription'}), 400
        
        subscription.payment_status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled',
            'access_until': subscription.end_date.isoformat() if subscription.end_date else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to cancel: {str(e)}'}), 500


@subscription_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Get usage statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        from app.models import Response
        from datetime import date
        
        today_count = Response.query.filter(
            Response.user_id == user.id,
            db.func.date(Response.created_at) == date.today()
        ).count()
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        is_premium = subscription and subscription.plan_type != 'free'
        
        return jsonify({
            'subscription_type': subscription.plan_type if subscription else 'free',
            'is_premium': is_premium,
            'usage': {
                'today': {
                    'count': today_count,
                    'limit': None if is_premium else 5,
                    'remaining': None if is_premium else max(0, 5 - today_count)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get usage: {str(e)}'}), 500
