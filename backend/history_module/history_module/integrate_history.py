from flask import Flask
from flask_cors import CORS
from prompt_history_module import history_bp

def integrate_history(app: Flask):
    """
    Integrate the prompt history functionality into a Flask app
    
    Args:
        app: Flask application instance
    """
    # Configure CORS for the history endpoints
    CORS(app, resources={
        r"/history/*": {
            "origins": ["chrome-extension://*"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Cookie", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register the blueprint
    app.register_blueprint(history_bp)
    
    return app