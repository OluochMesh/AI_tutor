# AI tutor endpoint (analyze input, feedback)
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extension import db
from app.models import User, Response, Progress
from app.services.ai_service import AITutorService
from datetime import datetime, date



tutor_bp = Blueprint('tutor', __name__)
#nitializa ai services
ai_service = AITutorService()
#Rate limiting helper
def check_daily_limit(user):
    """Check if user has exceeded daily AI request limit"""
    if user.is_premium():
        return True, None  # No limit for premium users
    #fre users 5 limits  per day
    today = date.today()
    today_responses = Response.query.filter(
        Response.user_id == user.id,
        db.func.date(Response.created_at) == today
    ).count()
    if today_responses >= 5:
        return False, "Daily limit reached (5 requests). Upgrade to Premium for unlimited access."
    
    return True, None


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
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        # Check rate limit
        can_proceed, message = check_daily_limit(user)
        if not can_proceed:
            return jsonify({'error': message}), 429
        data = request.get_json()
        concept = data.get('concept', '').strip()
        explanation= data.get('explanation', '').strip()
        if not concept or not explanation:
            return jsonify({'error': 'Concept and explanation are required'}), 400
        
        if len(explanation) < 10:
            return jsonify({'error': 'Explanation too short. Please provide more detail.'}), 400
        
        #get ai feedback
        ai_result = ai_service.analyze_explanation(concept, explanation)
        #save response to db
        response = Response()
        response.user_id = user.id
        response.concept = concept
        response.learner_input= explanation
        response.ai_feedback = ai_result['feedback']
        response.understanding_score = ai_result['understanding_score']

        db.session.add(response)
        db.session.commit()

        #update the progress
        update_user_progress(user.id, concept, ai_result['understanding_score'])

        remainin_requests = None
        if not user.is_premium():
            today_count = Response.query.filter(
                Response.user_id == user.id,
                db.func.date(Response.created_at) == date.today()
            ).count()
            remaining_requests = max(0, 5 - today_count)
            return jsonify({
            'message': 'Explanation analyzed successfully',
            'response_id': response.id,
            'feedback': ai_result['feedback'],
            'understanding_score': ai_result['understanding_score'],
            'strengths': ai_result.get('strengths', []),
            'areas_to_improve': ai_result.get('areas_to_improve', []),
            'remaining_requests': remaining_requests
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to analyze explanation: {str(e)}'}), 500
    



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
        
        #get query params
        limit = request.args.get('limit', 10, type= int)
        concept = request.args.get('concept', None, type=str)

        #build the query
        query = Response.query.filter_by(user_id=user.id)

        if concept:
            query = query.filter_by(concept=concept)
        
        responses = query.order_by(Response.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'total': len(responses),
            'history': [response.to_dict() for response in responses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get history: {str(e)}'}), 500
    

@tutor_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_user_progress():
    """
    Get user's learning progress across all topics
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        progress_records = Progress.query.filter_by(user_id=user.id)\
                                        .order_by(Progress.average_score.desc())\
                                        .all()
        
        # Calculate overall statistics
        total_sessions = sum(p.total_sessions for p in progress_records)
        overall_avg = sum(p.average_score * p.total_sessions for p in progress_records) / total_sessions if total_sessions > 0 else 0
        
        return jsonify({
            'total_sessions': total_sessions,
            'overall_average': round(overall_avg, 2),
            'topics_studied': len(progress_records),
            'progress': [p.to_dict() for p in progress_records]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500
    
@tutor_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """
    Get personalized study recommendations based on performance
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find weak topics (score < 0.7)
        weak_topics = Progress.query.filter(
            Progress.user_id == user.id,
            Progress.average_score < 0.7
        ).order_by(Progress.average_score.asc()).limit(3).all()
        
        weak_topic_names = [p.topic for p in weak_topics]
        
        # Get AI-generated study tips
        study_tips = ai_service.generate_study_tips(weak_topic_names)
        
        return jsonify({
            'weak_topics': [p.to_dict() for p in weak_topics],
            'study_tips': study_tips,
            'recommendation': 'Focus on your weak areas for better overall progress'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500
    
@tutor_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """
    Get comprehensive user statistics
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Total responses
        total_responses = Response.query.filter_by(user_id=user.id).count()
        
        # Today's responses
        today_responses = Response.query.filter(
            Response.user_id == user.id,
            db.func.date(Response.created_at) == date.today()
        ).count()
        
        # Average score
        avg_score = db.session.query(db.func.avg(Response.understanding_score))\
                             .filter(Response.user_id == user.id).scalar() or 0
        
        # Best and worst topics
        progress_records = Progress.query.filter_by(user_id=user.id).all()
        
        best_topic = max(progress_records, key=lambda p: p.average_score) if progress_records else None
        worst_topic = min(progress_records, key=lambda p: p.average_score) if progress_records else None
        
        return jsonify({
            'total_responses': total_responses,
            'today_responses': today_responses,
            'average_understanding': round(avg_score, 2),
            'topics_studied': len(progress_records),
            'best_topic': best_topic.to_dict() if best_topic else None,
            'worst_topic': worst_topic.to_dict() if worst_topic else None,
            'subscription_status': user.subscription_status
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500
    
# Helper function to update progress
def update_user_progress(user_id, topic, score):
    """Update or create progress record for a topic"""
    try:
        progress = Progress.query.filter_by(user_id=user_id, topic=topic).first()
        
        if progress:
            progress.update_progress(score)
        else:
            progress = Progress()
            progress.user_id = user_id
            progress.topic = topic
            progress.total_sessions = 1
            progress.average_score = score
            progress.last_session_date = datetime.utcnow()
            db.session.add(progress)
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error updating progress: {str(e)}")
        db.session.rollback()

# Test endpoint
@tutor_bp.route('/hello', methods=['GET'])
def hello_tutor():
    return jsonify({
        'message': 'AI Tutor API is working',
        'endpoints': {
            'explain': 'POST /api/tutor/explain (submit explanation for feedback)',
            'history': 'GET /api/tutor/history (get learning history)',
            'progress': 'GET /api/tutor/progress (get progress across topics)',
            'recommendations': 'GET /api/tutor/recommendations (get study tips)',
            'stats': 'GET /api/tutor/stats (get user statistics)'
        }
    }), 200

