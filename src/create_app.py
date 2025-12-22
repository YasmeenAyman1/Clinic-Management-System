# src/create_app.py
import os
from dotenv import load_dotenv
from flask import Flask

from controllers.assistant_controller import assistant_bp
from controllers.authO_controller import authO_bp
from controllers.doctor_controller import doctor_bp
from controllers.patient_controller import patient_bp
from controllers.admin_controller import admin_bp
from database.db_singleton import DatabaseConnection
from repositories.repositories_factory import RepositoryFactory

def create_app(config_name=None):
    """
    Application Factory Pattern
    Creates and configures the Flask application
    """
    # Load environment variables
    load_dotenv()
    
    # 1. Create Flask app instance
    app = Flask(__name__)
    
    # 2. Configure the app based on config_name
    if config_name == 'testing':
        app.config.update(
            SECRET_KEY='test-secret-key-for-testing-only',
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            DEBUG=False
        )
    else:
        # Default configuration
        app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret-key")
        app.config['DEBUG'] = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # 3. Initialize database connection
    db_conn = DatabaseConnection()
    # Only ensure schema in non-testing environments
    if config_name != 'testing':
        # db_conn.ensure_schema()  # Uncomment if needed
        pass
    
    # 4. Register blueprints
    app.register_blueprint(authO_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(admin_bp)
    
    # 5. Register routes
    from flask import render_template, request, flash, redirect, url_for
    
    @app.route("/")
    def home():
        return render_template("/home/home.html")
    
    @app.route("/about")
    def about():
        return render_template("/home/about.html")
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page"""
        if request.method == 'POST':
            contact_repo = RepositoryFactory.get_repository('contact')
            
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            message = request.form.get('message', '').strip()
            
            if name and email and message:
                contact_repo.save_message(name, email, message)
                flash('Thank you for your message! We will get back to you soon.', 'success')
                return redirect(url_for('contact'))
            else:
                flash('Please fill in all fields.', 'danger')
        
        return render_template('home/contact.html')
    
    # 6. Return the configured application
    return app