from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app