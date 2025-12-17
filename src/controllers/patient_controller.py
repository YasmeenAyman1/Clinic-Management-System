from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
import os

from repositories.repositories_factory import RepositoryFactory

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")
user_repo = RepositoryFactory.get_repository("user")
patient_repo = RepositoryFactory.get_repository("patient")
appointment_repo = RepositoryFactory.get_repository("appointment")
doctor_repo = RepositoryFactory.get_repository("doctor")


@patient_bp.route("/")
@patient_bp.route("/home")
def list_patients():
    if not session.get("user_id"):
        flash("Please log in to access the patient area.", category="info")
        return redirect(url_for("auth.login"))
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Get patient's appointments
    appointments = appointment_repo.get_by_patient_id(patient.id)
    
    return render_template("/patient/patient_home.html", 
                         patient=patient, 
                         appointments=appointments or [],
                         medical_history=[])  # TODO: Add medical history when implemented


@patient_bp.route("/appointments", methods=["GET", "POST"])
def appointments():
    if not session.get("user_id"):
        flash("Please log in to access appointments.", category="info")
        return redirect(url_for("auth.login"))
    
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    if request.method == "POST":
        if "book_appointment" in request.form:
            doctor_id = request.form.get("doctor_id", type=int)
            date = request.form.get("date")
            appointment_time = request.form.get("appointment_time")
            
            if not doctor_id or not date or not appointment_time:
                flash("Please fill in all fields.", category="danger")
                return redirect(url_for("patient.appointments"))

            # Server-side validation: ensure the requested slot is still available
            try:
                slots = appointment_repo.get_available_slots(doctor_id, date)
            except Exception:
                slots = []

            if appointment_time not in slots:
                flash("Selected time slot is no longer available. Please choose another slot.", category="danger")
                return redirect(url_for("patient.appointments"))

            appointment = appointment_repo.create_appointment(
                patient_id=patient.id,
                doctor_id=doctor_id,
                date=date,
                appointment_time=appointment_time
            )
            
            if appointment:
                # booking creates a PENDING appointment that needs doctor approval
                flash("Appointment request submitted and is pending approval.", category="success")
            else:
                flash("Failed to submit appointment request. The time slot may be taken.", category="danger")
            
            return redirect(url_for("patient.appointments"))
        
        elif "cancel_appointment" in request.form:
            appointment_id = request.form.get("appointment_id", type=int)
            if appointment_id:
                if appointment_repo.cancel_appointment(appointment_id, patient.id):
                    flash("Appointment cancelled successfully.", category="success")
                else:
                    flash("Failed to cancel appointment.", category="danger")
            return redirect(url_for("patient.appointments"))
    
    # Get patient's appointments
    patient_appointments = appointment_repo.get_by_patient_id(patient.id)
    
    # Get all doctors for booking
    doctors = doctor_repo.list_all()
    
    # Get available slots for selected doctor (if any)
    available_slots = []
    selected_doctor_id = request.args.get("doctor_id", type=int)
    selected_date = request.args.get("date", "")
    
    if selected_doctor_id and selected_date:
        available_slots = appointment_repo.get_available_slots(selected_doctor_id, selected_date)

    # Render the appointments page (GET) with computed data
    return render_template(
        "/patient/appointments.html",
        appointments=patient_appointments,
        doctors=doctors,
        available_slots=available_slots,
        selected_doctor_id=selected_doctor_id,
        selected_date=selected_date
    )


@patient_bp.route('/api/doctor/<int:doctor_id>/slots')
def doctor_slots_api(doctor_id):
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date parameter required'}), 400
    try:
        slots = appointment_repo.get_available_slots(doctor_id, date)
    except Exception:
        slots = []
    return jsonify({'slots': slots})


@patient_bp.route("/diagnosis")
def diagnosis():
    if not session.get("user_id"):
        flash("Please log in to access medical history.", category="info")
        return redirect(url_for("auth.login"))
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    # Load medical records
    medical_repo = RepositoryFactory.get_repository("medical_record")
    uploaded_repo = RepositoryFactory.get_repository("uploaded_file")
    doctor_repo = RepositoryFactory.get_repository("doctor")

    records = medical_repo.get_records_by_patient(patient.id)
    diagnosis_list = []
    for r in records:
        doc = doctor_repo.get_by_id(r.doctor_id) if r.doctor_id else None
        files = uploaded_repo.get_files_by_record(r.id) if r.id else []
        files_data = [{"filename": os.path.basename(f.file_path), "file_path": f.file_path} for f in files]
        diagnosis_list.append({
            "id": r.id,
            "date": r.upload_date,
            "doctor_name": f"{doc.firstName} {doc.lastName}" if doc else "Unknown",
            "text": r.diagnoisis,
            "treatment": r.treatment,
            "followup": r.follow_up_date,
            "files": files_data,
        })

    return render_template("/patient/diagnosis.html", patient=patient, diagnosis=diagnosis_list)

@patient_bp.route("/profile/<username>")
def patient_profile(username):
    user = user_repo.get_by_username(username)
    if not user:
        flash("Patient not found.", category="warning")
        return redirect(url_for("home"))
    patient = patient_repo.get_by_user_id(user.id)
    return render_template("profile.html", patient=patient, user=user)