from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask

def init_rate_limiter(app: Flask):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per hour", "20 per minute"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    return limiter

def configure_rate_limits(limiter):
    return {
        'health_check': "200 per minute",
        'list_tools': "60 per minute", 
        'call_tool': "30 per minute"
    }