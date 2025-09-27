#Signup, login, JWT refresh
from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/hello', methods=['GET'])
def hello():
    return jsonify({
        "message": "Hello, from the auth api!",
        "status": "success"
    })
@auth_bp.route('/test', methods=['GET'])
def test_auth():
    return jsonify({
        'message': 'Auth blueprint is working!',
        'status': 'success'
    })