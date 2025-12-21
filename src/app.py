import os
from os import path
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from controllers.assistant_controller import assistant_bp
from controllers.authO_controller import authO_bp
from controllers.doctor_controller import doctor_bp
from controllers.patient_controller import patient_bp
from controllers.admin_controller import admin_bp
from database.db_singleton import DatabaseConnection
from repositories.repositories_factory import RepositoryFactory

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Initialize shared DB connection once at startup and ensure legacy schema is fixed
db_conn = DatabaseConnection()
# db_conn.ensure_schema()

app.register_blueprint(authO_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(admin_bp)


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

if __name__ == "__main__":
    app.run(debug=True)