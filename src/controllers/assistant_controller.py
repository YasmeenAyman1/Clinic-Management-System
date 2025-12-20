from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from datetime import date

from repositories.repositories_factory import RepositoryFactory

assistant_bp = Blueprint('assistant', __name__, url_prefix='/assistant')
user_repo = RepositoryFactory.get_repository("user")
patient_repo = RepositoryFactory.get_repository("patient")  
assistant_repo = RepositoryFactory.get_repository("assistant")
appointment_repo = RepositoryFactory.get_repository("appointment")
doctor_repo = RepositoryFactory.get_repository("doctor")

@assistant_bp.route('/')
def assistant_home():
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    if session.get("role") != "assistant":
        flash("Access denied. Assistant access required.", category="danger")
        return redirect(url_for("auth.dashboard"))
    
    assistant = assistant_repo.get_by_user_id(session.get("user_id"))
    if not assistant:
        flash("Assistant profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Get today's appointments for all doctors
    today = date.today().isoformat()
    # Get all appointments for today (assistant can see all)
    cursor = assistant_repo.db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.id, a.appointment_time, a.status, a.date, a.doctor_id, a.patient_id,
               d.firstName as doctor_first_name, d.lastName as doctor_last_name,
               p.firstName as patient_first_name, p.lastName as patient_last_name, p.phone
        FROM Appointment a
        LEFT JOIN doctor d ON a.doctor_id = d.id
        LEFT JOIN patient p ON a.patient_id = p.id
        WHERE a.date = %s
        ORDER BY a.appointment_time ASC
        """,
        (today,)
    )
    today_appointments = cursor.fetchall()
    cursor.close()
    
    return render_template('assistant/assistant_home.html', 
                         assistant=assistant, 
                         today_appointments=today_appointments)

@assistant_bp.route('/tasks')
def manage_tasks():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('assistant/manage_tasks.html')

@assistant_bp.route('/profile/<username>')
def assistant_profile(username):
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    user = user_repo.get_by_username(username)
    if not user:
        flash("Assistant not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    assistant = assistant_repo.get_by_user_id(user.id)
    if not assistant:
        flash("Assistant profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    return render_template('assistant/assistant_profile.html', assistant=assistant, user=user)

@assistant_bp.route('/reports')
def view_reports():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('assistant/view_reports.html')

@assistant_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('assistant/assistant_schedule.html')

@assistant_bp.route('/search_patient', methods=['GET', 'POST'])
def search_patient():
    if not session.get("user_id") or session.get("role") not in ["assistant", "doctor"]:
        flash("Access denied. Assistant or Doctor access required.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('assistant/search_patient.html')

@assistant_bp.route('/patient_file/<int:pid>')
def patient_file(pid):
    # You can fetch patient data here using patient_repo
    patient = patient_repo.get_by_id(pid)
    if not patient:
        flash("Patient not found.", category="warning")
        return redirect(url_for('assistant.search_patient'))
    return render_template('assistant/patient_file.html', patient=patient)


@assistant_bp.route('/add_appointment', methods=['POST'])
def add_appointment():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    doctor_id = request.form.get("doctor_id", type=int)
    patient_id = request.form.get("patient_id", type=int)
    date = request.form.get("date")
    appointment_time = request.form.get("appointment_time")
    
    if not doctor_id or not patient_id or not date or not appointment_time:
        flash("Please fill in all fields.", category="danger")
        return redirect(url_for("assistant.assistant_home"))
    
    appointment = appointment_repo.create_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        date=date,
        appointment_time=appointment_time,
        assistant_id=assistant_repo.get_by_user_id(session.get("user_id")).id
    )
    
    if appointment:
        flash("Appointment added successfully!", category="success")
    else:
        flash("Failed to add appointment. The time slot may be taken.", category="danger")
    
    return redirect(url_for("assistant.assistant_home"))
