from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extension import db
from app.models import User, Response, Progress
from app.services.ai_service import AITutorService
from datetime import datetime, date

tutor_bp = Blueprint('tutor', __name__)
ai_service = AITutorService()


# 🧭 Rate limiting helper
def check_daily_limit(user):
    """Check if user has exceeded daily AI request limit"""
    if user.is_premium():
        return True, None  # No limit for premium users

    today = date.today()
    today_responses = Response.query.filter(
        Response.user_id == user.id,
        db.func.date(Response.created_at) == today
    ).count()

    if today_responses >= 5:
        return False, "Daily limit reached (5 requests). Upgrade to Premium for unlimited access."

    return True, None


# 🧠 Submit explanation for AI analysis
@tutor_bp.route('/explain', methods=['POST'])
@jwt_required()
def submit_explanation():
    """
    Submit learner's explanation for AI feedback
    Expected JSON: {
        "concept": "Photosynthesis",
        "explanation": "Plants use sunlight to make food..."
    }
    """
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Get and validate user
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'Authentication failed: Invalid token'
            }), 401
        
        try:
            user_id = int(current_user)
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': 'Invalid user ID format',
                'details': str(e)
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Check rate limit
        can_proceed, message = check_daily_limit(user)
        if not can_proceed:
            return jsonify({
                'success': False,
                'error': message
            }), 429

        # Extract fields - support both 'explanation' and 'learner_input' for compatibility
        concept = data.get('concept', '').strip()
        explanation = data.get('explanation', '').strip() or data.get('learner_input', '').strip()

        # Validate concept
        if not concept:
            return jsonify({
                'success': False,
                'error': 'Concept is required',
                'field': 'concept'
            }), 400
        
        if len(concept) < 2:
            return jsonify({
                'success': False,
                'error': 'Concept must be at least 2 characters long',
                'field': 'concept'
            }), 400

        # Validate explanation
        if not explanation:
            return jsonify({
                'success': False,
                'error': 'Explanation is required',
                'field': 'explanation'
            }), 400

        if len(explanation) < 10:
            return jsonify({
                'success': False,
                'error': 'Explanation too short. Please provide at least 10 characters.',
                'field': 'explanation',
                'min_length': 10
            }), 400

        if len(explanation) > 5000:
            return jsonify({
                'success': False,
                'error': 'Explanation too long. Maximum 5000 characters allowed.',
                'field': 'explanation',
                'max_length': 5000
            }), 400

        # Get AI feedback
        try:
            ai_result = ai_service.analyze_explanation(concept, explanation)
            
            # Validate AI result structure
            if not isinstance(ai_result, dict):
                raise ValueError("AI service returned invalid response format")
            
            if 'feedback' not in ai_result:
                raise ValueError("AI service response missing 'feedback' field")
            
            if 'understanding_score' not in ai_result:
                raise ValueError("AI service response missing 'understanding_score' field")
            
            # Ensure understanding_score is a number
            score = ai_result['understanding_score']
            if not isinstance(score, (int, float)):
                try:
                    score = float(score)
                except (ValueError, TypeError):
                    score = 0.5  # Default score
                ai_result['understanding_score'] = score
            
            # Ensure feedback is a string
            feedback = ai_result.get('feedback', '')
            if not isinstance(feedback, str):
                feedback = str(feedback) if feedback else "No feedback available."
            ai_result['feedback'] = feedback
            
        except Exception as ai_error:
            # If AI service fails, use fallback but log the error
            return jsonify({
                'success': False,
                'error': 'AI service temporarily unavailable',
                'details': str(ai_error)
            }), 503

        # Save response to DB
        try:
            response = Response(
                user_id=user.id,
                concept=concept,
                learner_input=explanation,
                ai_feedback=ai_result['feedback'],
                understanding_score=float(ai_result['understanding_score'])
            )
            db.session.add(response)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Failed to save response to database',
                'details': str(db_error)
            }), 500

        # Update progress (don't fail if this fails)
        try:
            update_user_progress(user.id, concept, float(ai_result['understanding_score']))
        except Exception:
            # Log but don't fail the request
            pass

        # Compute remaining requests
        remaining_requests = None
        if not user.is_premium():
            today_count = Response.query.filter(
                Response.user_id == user.id,
                db.func.date(Response.created_at) == date.today()
            ).count()
            remaining_requests = max(0, 5 - today_count)

        return jsonify({
            'success': True,
            'message': 'Explanation analyzed successfully',
            'response_id': response.id,
            'feedback': ai_result['feedback'],
            'understanding_score': ai_result['understanding_score'],
            'strengths': ai_result.get('strengths', []),
            'areas_to_improve': ai_result.get('areas_to_improve', []),
            'remaining_requests': remaining_requests
        }), 200

    except ValueError as e:
        # Handle JSON decode errors or invalid data
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Invalid request data',
            'details': str(e)
        }), 400
    except TypeError as e:
        # Handle type errors
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Type error in request processing',
            'details': str(e)
        }), 400
    except KeyError as e:
        # Handle missing keys in response
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Missing required data',
            'details': f'Missing key: {str(e)}'
        }), 500
    except Exception as e:
        # Catch-all for any other errors
        db.session.rollback()
        # In production, log the full exception for debugging
        import traceback
        error_trace = traceback.format_exc()
        
        return jsonify({
            'success': False,
            'error': 'Failed to analyze explanation',
            'details': str(e),
            'trace': error_trace if current_app.config.get('DEBUG', False) else None
        }), 500


# 📜 Learning history
@tutor_bp.route('/history', methods=['GET'])
@jwt_required()
def get_learning_history():
    """
    Get user's learning history
    Query params: ?limit=10&concept=Photosynthesis
    """
    try:
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        limit = request.args.get('limit', 10, type=int)
        concept = request.args.get('concept', None, type=str)

        query = Response.query.filter_by(user_id=user.id)
        if concept:
            query = query.filter_by(concept=concept)

        responses = query.order_by(Response.created_at.desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'total': len(responses),
            'history': [r.to_dict() for r in responses]
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get history: {str(e)}'}), 500


# 📈 Learning progress
@tutor_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_user_progress():
    """Get user's learning progress across all topics"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        progress_records = Progress.query.filter_by(user_id=user.id) \
                                         .order_by(Progress.average_score.desc()) \
                                         .all()

        total_sessions = sum(p.total_sessions for p in progress_records)
        overall_avg = (sum(p.average_score * p.total_sessions for p in progress_records) / total_sessions
                       if total_sessions > 0 else 0)

        return jsonify({
            'success': True,
            'total_sessions': total_sessions,
            'overall_average': round(overall_avg, 2),
            'topics_studied': len(progress_records),
            'progress': [p.to_dict() for p in progress_records]
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500


# 🎯 Study recommendations
@tutor_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get personalized study recommendations based on performance"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        weak_topics = Progress.query.filter(
            Progress.user_id == user.id,
            Progress.average_score < 0.7
        ).order_by(Progress.average_score.asc()).limit(3).all()

        weak_topic_names = [p.topic for p in weak_topics]
        study_tips = ai_service.generate_study_tips(weak_topic_names)

        return jsonify({
            'success': True,
            'weak_topics': [p.to_dict() for p in weak_topics],
            'study_tips': study_tips,
            'recommendation': 'Focus on your weak areas for better overall progress'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500


# 📊 User stats
@tutor_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get comprehensive user statistics"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        total_responses = Response.query.filter_by(user_id=user.id).count()
        today_responses = Response.query.filter(
            Response.user_id == user.id,
            db.func.date(Response.created_at) == date.today()
        ).count()

        avg_score = db.session.query(db.func.avg(Response.understanding_score)) \
                              .filter(Response.user_id == user.id).scalar() or 0

        topics_studied_count = Progress.query.filter_by(user_id=user.id).count()
        best_topic = Progress.query.filter_by(user_id=user.id) \
                                   .order_by(Progress.average_score.desc()) \
                                   .first()
        worst_topic = Progress.query.filter_by(user_id=user.id) \
                                    .order_by(Progress.average_score.asc()) \
                                    .first()

        return jsonify({
            'success': True,
            'total_responses': total_responses,
            'today_responses': today_responses,
            'average_understanding': round(avg_score, 2),
            'topics_studied': topics_studied_count,
            'best_topic': best_topic.to_dict() if best_topic else None,
            'worst_topic': worst_topic.to_dict() if worst_topic else None,
            'subscription_status': user.subscription_status
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500


# 🧩 Progress updater
def update_user_progress(user_id, topic, score):
    """Update or create progress record for a topic"""
    try:
        progress = Progress.query.filter_by(user_id=user_id, topic=topic).first()
        if progress:
            progress.update_progress(score)
        else:
            progress = Progress(
                user_id=user_id,
                topic=topic,
                total_sessions=1,
                average_score=score,
                last_session_at=datetime.utcnow()
            )
            db.session.add(progress)
        db.session.commit()

    except Exception as e:
        # Log error without printing - proper logging would be better
        db.session.rollback()


# 🔧 Health check endpoint
@tutor_bp.route('/hello', methods=['GET'])
def hello_tutor():
    return jsonify({
        'message': 'AI Tutor API is working',
        'endpoints': {
            'explain': 'POST /api/tutor/explain',
            'history': 'GET /api/tutor/history',
            'progress': 'GET /api/tutor/progress',
            'recommendations': 'GET /api/tutor/recommendations',
            'stats': 'GET /api/tutor/stats'
        }
    }), 200



