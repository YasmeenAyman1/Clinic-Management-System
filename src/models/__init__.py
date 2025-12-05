# from flask import Flask, render_template, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
# from controllers.authO_controller import authO_bp
# from controllers.patient_controller import patient_bp

# def create_app():
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'yassmen123'
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
#     db = SQLAlchemy(app) 
#     app.register_blueprint(authO_bp)
#     app.register_blueprint(patient_bp)

#     return app