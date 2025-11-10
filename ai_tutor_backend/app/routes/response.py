# app/routes/response_routes.py
from flask import Blueprint, request, jsonify
from app.extension import db
from app.models.response import Response
from app.services.ai_service import AITutorService

response_bp = Blueprint('response', __name__)
ai_service = AITutorService()

@response_bp.route('/', methods=['POST'])
def analyze_response():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        concept = data.get('concept')
        learner_input = data.get('learner_input')

        if not (user_id and concept and learner_input):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        analysis = ai_service.analyze_explanation(concept, learner_input)

        response_entry = Response(
            user_id=user_id,
            concept=concept,
            learner_input=learner_input,
            ai_feedback=analysis['feedback'],
            understanding_score=analysis['understanding_score']
        )

        db.session.add(response_entry)
        db.session.commit()

        return jsonify({'success': True, 'data': response_entry.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to analyze response: {str(e)}'}), 500
