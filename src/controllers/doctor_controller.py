from flask import Flask, render_template, Blueprint
from models.upload_model import Upload

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/')
def doctor_home():
    return render_template('doctor_home.html')

@doctor_bp.route('/patients')
def manage_patients():
    return "Manage patients will be displayed here."
    # patients = Upload.get_all_patients()
    # return render_template('manage_patients.html', patients=patients)
@doctor_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    return render_template('schedule.html')
    # if request.method == 'POST':
    #     # Handle schedule update logic here
    #     pass
    # schedule = Schedule.get_by_doctor(current_user.id)
    # return render_template('schedule.html', schedule=schedule)
@doctor_bp.route('/profile/<username>')
def doctor_profile(username):
    doctor = Upload.get_by_username(username)
    if doctor:
        return render_template('doctor_profile.html', doctor=doctor)
    else:
        return "Doctor not found", 404
@doctor_bp.route('/reports')
def view_reports():
    return "Medical reports will be displayed here."
    # reports = Report.get_by_doctor(current_user.id)
    # return render_template('view_reports.html', reports=reports)
