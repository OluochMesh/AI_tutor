from flask import Blueprint, jsonify, Response as FlaskResponse
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extension import db
from app.models import User, Response, Progress
from app.utils.decorators import premium_required
from datetime import datetime
import csv
import io

export_bp = Blueprint('export', __name__)

@export_bp.route('/history-csv', method='GET')
@jwt_required()
@premium_required

def export_history_csv():
    """
    Premium: Export learning history as CSV
    Returns CSV file download
    """
    try:
        current_user_id= get_jwt_identity()
        user= User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        #get all user responses
        responses = Response.query.filter_by(user_id=user.id)\
                                  .order_by(Response.created_at.desc()).all()

        #creating csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Date',
            'Time',
            'Concept',
            'Your Explanation',
            'AI Feedback',
            'Understanding Score (%)',
            'Performance Level'
        ])

        #write data
        for response in responses:
            score_percent = round(response.understanding_score*100, 1)
            if score_percent >= 90:
                level = 'Excellent'
            elif score_percent >= 70:
                level = 'Strong'
            elif score_percent >= 50:
                level = 'Good'
            else:
                level = 'Needs Improvement'
            
            writer.writerow([
                response.created_at.strftime('%Y-%m-%d'),
                response.created_at.strftime('%H:%M:%S'),
                response.concept,
                response.learner_input,
                response.ai_feedback,
                score_percent,
                level
            ])

        output.seek(0)

        return FlaskResponse(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=ai_tutor_history_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/progress-csv', methods=['GET'])
@jwt_required()
@premium_required
def export_progress_csv():
    """
    Premium: Export progress data as CSV
    Returns CSV file download
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all progress records
        progress_records = Progress.query.filter_by(user_id=user.id)\
                                        .order_by(Progress.average_score.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Topic',
            'Total Sessions',
            'Average Score (%)',
            'Performance Level',
            'Last Practiced',
            'First Practiced'
        ])
        
        # Write data
        for progress in progress_records:
            score_percent = round(progress.average_score * 100, 1)
            
            # Determine performance level
            if score_percent >= 90:
                level = 'Excellent'
            elif score_percent >= 70:
                level = 'Strong'
            elif score_percent >= 50:
                level = 'Good'
            else:
                level = 'Needs Improvement'
            
            writer.writerow([
                progress.topic,
                progress.total_sessions,
                score_percent,
                level,
                progress.last_session_date.strftime('%Y-%m-%d %H:%M:%S'),
                progress.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Prepare response
        output.seek(0)
        
        return FlaskResponse(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=ai_tutor_progress_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/full-report-csv', methods=['GET'])
@jwt_required()
@premium_required
def export_full_report():
    """
    Premium: Export comprehensive learning report
    Includes summary stats + all data
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get data
        responses = Response.query.filter_by(user_id=user.id).all()
        progress_records = Progress.query.filter_by(user_id=user.id).all()
        
        # Calculate overall stats
        total_sessions = len(responses)
        avg_score = sum(r.understanding_score for r in responses) / total_sessions if total_sessions > 0 else 0
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary section
        writer.writerow(['AI TUTOR LEARNING REPORT'])
        writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['User:', user.email])
        writer.writerow([])
        
        writer.writerow(['OVERALL STATISTICS'])
        writer.writerow(['Total Learning Sessions', total_sessions])
        writer.writerow(['Average Understanding Score', f'{round(avg_score * 100, 1)}%'])
        writer.writerow(['Topics Studied', len(progress_records)])
        writer.writerow([])
        
        # Progress by topic
        writer.writerow(['PROGRESS BY TOPIC'])
        writer.writerow(['Topic', 'Sessions', 'Avg Score (%)', 'Last Practiced'])
        for progress in progress_records:
            writer.writerow([
                progress.topic,
                progress.total_sessions,
                round(progress.average_score * 100, 1),
                progress.last_session_date.strftime('%Y-%m-%d')
            ])
        writer.writerow([])
        
        # Recent sessions
        writer.writerow(['RECENT LEARNING SESSIONS (Last 10)'])
        writer.writerow(['Date', 'Concept', 'Score (%)', 'Feedback Summary'])
        recent = Response.query.filter_by(user_id=user.id)\
                              .order_by(Response.created_at.desc()).limit(10).all()
        for r in recent:
            feedback_summary = r.ai_feedback[:100] + '...' if len(r.ai_feedback) > 100 else r.ai_feedback
            writer.writerow([
                r.created_at.strftime('%Y-%m-%d'),
                r.concept,
                round(r.understanding_score * 100, 1),
                feedback_summary
            ])
        
        # Prepare response
        output.seek(0)
        
        return FlaskResponse(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=ai_tutor_full_report_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

        