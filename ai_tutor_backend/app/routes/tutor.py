# AI tutor endpoint (analyze input, feedback)
from flask import Blueprint, request, jsonify

tutor_bp = Blueprint('tutor', __name__)

@tutor_bp.route('/hello', methods=['GET'])
def hello_tutor():
    return jsonify({
        "message": "Hello, from the tutor api!",
        "status": "success",
        "info": "This is where the learners will submit their queries.",
        "endpoint": "/api/tutor/hello"
    })

@tutor_bp.route('/test', methods=['POST'])
def test_tutor():
    data = request.json
    return jsonify({
        "message": "Test endpoint received!",
        "status": "success",
    })