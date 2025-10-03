from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extension import db
from app.models import User, Response, Progress
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract

analytics_bp = Blueprint('analytics',__name__)

@analytics_bp.route('/timeline', methods=['GET'], endpoint='get_timeline')
@jwt_required()
def get_timeline_data():
    """
    Get timeline data for score over time graph
    Query params: ?days=30 (default: 30)
    """
    try:
        current_user_id= get_jwt_identity()
        user= User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'user not found'}), 404
        days= request.args.get('days', 30, type=int)
        start_date= datetime.utcnow() - timedelta(days=days)

        #get daily average scores
        daily_scores= db.session.query(
            func.date(Response.created_at).label('date'),
            func.avg(Response.understanding_score).label('avg_score'),
            func.count(Response.id).label('session_count')

        ).filter(
            Response.user_id==current_user_id,
            Response.created_at >= start_date
        ).group_by(
            func.date(Response.created_at)
        ).order_by('date').all()

        timeline_data = [
            {
                'date': str(score.date),
                'score': round(score.avg_score * 100, 1),
                'sessions': score.session_count
            }
            for score in daily_scores
        ]
        return jsonify({
            'timeline_data': timeline_data,
            'period': f'Last {days} days'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get timeline: {str(e)}'}), 500
    
@analytics_bp.route('/topic-comparison', methods=['GET'], endpoint='get_topic_comparison')
@jwt_required()
def get_topic_comparison():
    """
    Compare performance across topics
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # get topic statistics
        topics = Progress.query.filter_by(user_id=current_user_id).all()

        topic_data=[]

        for topic in topics:
            topic_data.append({
                'topic': topic.topic,
                'average_score': round(topic.average_score * 100, 1),
                'total_sessions': topic.total_sessions,
                'last_practiced': topic.last_session_date.isoformat(),
                'performance_level': get_performance_level(topic.average_score)
            })

            #sort the score from best to worst
        topic_data.sort(key=lambda x: x['average_score'], reverse=True)
        return jsonify({
            'topics': topic_data,
            'best_topic': topic_data[0] if topic_data else None,
            'worst_topic': topic_data[-1] if topic_data else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to compare topics: {str(e)}'}), 500
    
@analytics_bp.route('/streak', methods=['GET'], endpoint='get_learning_streak')
@jwt_required()
def get_learning_streak():
    """
    Calculate current learning streak (consecutive days)
    """
    try:
        current_user_id = get_jwt_identity()  # ADD PARENTHESES HERE
        user = User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all the unique dates with activities - FIXED QUERY
        activity_dates = db.session.query(
            func.date(Response.created_at).label('date')
        ).filter(
            Response.user_id == current_user_id  # FIXED: use user_id, not current_user_id
        ).distinct().order_by(func.date(Response.created_at).desc()).all()  # FIXED: order by created_at
        
        if not activity_dates:
            return jsonify({
                'current_streak': 0,
                'longest_streak': 0,
                'last_activity': None  # FIXED: typo in 'activity'
            }), 200

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        today = date.today()
        dates = [d[0] if isinstance(d, tuple) else d.date for d in activity_dates]  # Handle tuple results

        # Convert to date objects if they aren't already
        dates = [d if isinstance(d, date) else d.date() if hasattr(d, 'date') else d for d in dates]
        
        # Check if user practiced today or yesterday for current streak
        if dates[0] == today or dates[0] == today - timedelta(days=1):
            current_streak = 1
            
            # Count consecutive days from most recent
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i + 1]).days == 1:
                    current_streak += 1
                else:
                    break

        # Calculate longest streak across all dates
        temp_streak = 1
        for i in range(len(dates) - 1):
            if (dates[i] - dates[i + 1]).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        # Ensure longest_streak is at least 1 if there are any activities
        longest_streak = max(longest_streak, 1) if dates else 0

        return jsonify({
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_activity': str(dates[0]),
            'message': get_streak_message(current_streak) if 'get_streak_message' in globals() else f"Current streak: {current_streak} days"
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to calculate streak: {str(e)}'}), 500
    
@analytics_bp.route('/weekly-summary', methods=['GET'], endpoint='get_weekly_summary')
@jwt_required()
def get_weekly_summary():
    """
    Get summary of last 7 days
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get this week's data
        this_week = Response.query.filter(
            Response.user_id == user.id,
            Response.created_at >= week_ago
        ).all()
        
        # Get previous week's data for comparison
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        last_week = Response.query.filter(
            Response.user_id == user.id,
            Response.created_at >= two_weeks_ago,
            Response.created_at < week_ago
        ).all()
        
        # Calculate stats
        this_week_sessions = len(this_week)
        last_week_sessions = len(last_week)
        
        this_week_avg = sum(r.understanding_score for r in this_week) / this_week_sessions if this_week_sessions > 0 else 0
        last_week_avg = sum(r.understanding_score for r in last_week) / last_week_sessions if last_week_sessions > 0 else 0
        
        # Get unique topics this week
        topics_this_week = set(r.concept for r in this_week)
        
        # Calculate improvement
        improvement = ((this_week_avg - last_week_avg) * 100) if last_week_avg > 0 else 0
        
        return jsonify({
            'this_week': {
                'sessions': this_week_sessions,
                'average_score': round(this_week_avg * 100, 1),
                'topics_covered': len(topics_this_week)
            },
            'last_week': {
                'sessions': last_week_sessions,
                'average_score': round(last_week_avg * 100, 1)
            },
            'improvement': round(improvement, 1),
            'trend': 'up' if improvement > 0 else 'down' if improvement < 0 else 'stable'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get weekly summary: {str(e)}'}), 500
    
@analytics_bp.route('/heatmap', methods=['GET'], endpoint='get_activity_heatmap')
@jwt_required()
def get_activity_heatmap():
    """
    Get activity heatmap data (sessions per day over time)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get last 90 days of activity
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        activities = db.session.query(
            func.date(Response.created_at).label('date'),
            func.count(Response.id).label('count')
        ).filter(
            Response.user_id == user.id,
            Response.created_at >= ninety_days_ago
        ).group_by(
            func.date(Response.created_at)
        ).all()
        
        heatmap_data = [
            {
                'date': str(activity.date),
                'count': activity.count,
                'level': get_activity_level(activity.count)
            }
            for activity in activities
        ]
        
        return jsonify({
            'heatmap': heatmap_data,
            'period': 'Last 90 days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get heatmap: {str(e)}'}), 500
    
@analytics_bp.route('/time-patterns', methods=['GET'], endpoint='get_time_patterns')
@jwt_required()
def get_time_patterns():
    """
    Analyze when user is most active (day of week, time of day)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all responses
        responses = Response.query.filter_by(user_id=user.id).all()
        
        if not responses:
            return jsonify({
                'most_active_day': None,
                'most_active_hour': None,
                'patterns': []
            }), 200
        
        # Analyze day of week
        day_counts = {}
        hour_counts = {}
        
        for response in responses:
            day = response.created_at.strftime('%A')
            hour = response.created_at.hour
            
            day_counts[day] = day_counts.get(day, 0) + 1
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Find most active day and hour
        most_active_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        
        # Format day patterns
        day_pattern = [
            {'day': day, 'sessions': count}
            for day, count in day_counts.items()
        ]
        
        return jsonify({
            'most_active_day': most_active_day,
            'most_active_hour': f'{most_active_hour}:00' if most_active_hour is not None else None,
            'day_distribution': day_pattern,
            'recommendation': f'You learn best on {most_active_day}s!' if most_active_day else 'Keep building your routine!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to analyze patterns: {str(e)}'}), 500
    
# Helper functions
def get_performance_level(score):
    """Convert score to performance level"""
    if score >= 0.9:
        return 'Excellent'
    elif score >= 0.7:
        return 'Strong'
    elif score >= 0.5:
        return 'Good'
    elif score >= 0.3:
        return 'Needs Work'
    else:
        return 'Poor'


def get_activity_level(count):
    """Convert activity count to level (for heatmap)"""
    if count >= 5:
        return 4  # Very high
    elif count >= 3:
        return 3  # High
    elif count >= 2:
        return 2  # Medium
    elif count >= 1:
        return 1  # Low
    else:
        return 0  # None


def get_streak_message(streak):
    """Get motivational message based on streak"""
    if streak >= 30:
        return "Incredible! You're on fire!"
    elif streak >= 14:
        return "Amazing consistency! Keep it up!"
    elif streak >= 7:
        return "Great week of learning!"
    elif streak >= 3:
        return "Nice streak! Keep going!"
    elif streak >= 1:
        return "Good start! Come back tomorrow!"
    else:
        return "Start your streak today!"