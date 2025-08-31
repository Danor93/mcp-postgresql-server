from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, fields, ValidationError
import re

class MCPToolCallSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0 and len(x) <= 100)
    arguments = fields.Dict(required=False, missing={})

def validate_json_input(schema_class):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({'error': 'Invalid JSON payload'}), 400
                
                schema = schema_class()
                validated_data = schema.load(data)
                request.validated_json = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
            except Exception as e:
                return jsonify({'error': 'Invalid request format'}), 400
        
        return decorated_function
    return decorator

def sanitize_input(text):
    if not isinstance(text, str):
        return text
    
    # Remove potential SQL injection patterns
    text = re.sub(r'[;\'\"\\]', '', text)
    # Remove script tags and common XSS patterns
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_sql_query_params():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for key, value in request.args.items():
                if isinstance(value, str):
                    # Basic SQL injection pattern detection
                    dangerous_patterns = [
                        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b|\bUPDATE\b)',
                        r'(--|\/\*|\*\/)',
                        r'(\bOR\b.*=.*\bOR\b|\bAND\b.*=.*\bAND\b)'
                    ]
                    
                    for pattern in dangerous_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            return jsonify({'error': 'Invalid query parameters detected'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator