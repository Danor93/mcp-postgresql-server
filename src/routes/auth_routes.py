from flask import request, jsonify
from marshmallow import Schema, fields
from src.middleware.auth import JWTAuth
from src.middleware.security import validate_json_input

class LoginSchema(Schema):
    username = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 4)

def create_auth_routes(app):
    @app.route('/auth/login', methods=['POST'])
    @validate_json_input(LoginSchema)
    def login():
        data = request.validated_json
        username = data['username']
        password = data['password']
        
        # Simple demo authentication - in production use proper password hashing
        if username == "admin" and password == "password":
            auth = JWTAuth()
            token = auth.generate_token(1, username)
            return jsonify({
                'token': token,
                'user': {'id': 1, 'username': username}
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    @app.route('/auth/verify', methods=['GET'])
    def verify_token():
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        auth = JWTAuth()
        payload = auth.verify_token(token)
        
        if payload is None:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return jsonify({'valid': True, 'user': payload})