from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
import os
from datetime import datetime

from repositories.repositories_factory import RepositoryFactory

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

user_repo = RepositoryFactory.get_repository("user")
patient_repo = RepositoryFactory.get_repository("patient")
appointment_repo = RepositoryFactory.get_repository("appointment")
doctor_repo = RepositoryFactory.get_repository("doctor")


@patient_bp.route("/")
def patient_home():
    if not session.get("user_id"):
        flash("Please log in to access the patient area.", category="info")
        return redirect(url_for("auth.login"))
    
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Get all appointments
    all_appointments = appointment_repo.get_by_patient_id(patient.id)
    
    # Or get specific types
    upcoming_appointments = appointment_repo.get_upcoming_appointments(patient.id)
    completed_appointments = appointment_repo.get_completed_appointments(patient.id)
    
    # Get medical history/records
    medical_history = []  # For now, empty list
    
    # Debug: Print appointment statuses
    print(f"DEBUG: Found {len(all_appointments) if all_appointments else 0} total appointments")
    print(f"DEBUG: Found {len(upcoming_appointments)} upcoming appointments")
    print(f"DEBUG: Found {len(completed_appointments)} completed appointments")
    
    return render_template("patient/patient_home.html", 
                         patient=patient, 
                         appointments=all_appointments or [],  # Use all_appointments
                         upcoming_appointments=upcoming_appointments or [],
                         completed_appointments=completed_appointments or [],
                         medical_history=medical_history)

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

            # Server-side validation using get_available_slots()
            try:
                available_slots = appointment_repo.get_available_slots(doctor_id, date)
                
                # Normalize time format (remove seconds if present)
                if appointment_time and len(appointment_time) > 5:
                    appointment_time = appointment_time[:5]  # Keep only HH:MM
                
                if appointment_time not in available_slots:
                    error_msg = f"Selected time slot ({appointment_time}) is not available."
                    if available_slots:
                        error_msg += f" Available slots: {', '.join(available_slots)}"
                    else:
                        error_msg += " No slots available for this date."
                    
                    flash(error_msg, category="danger")
                    return redirect(url_for("patient.appointments"))
                    
            except Exception:
                flash("Error checking availability. Please try again.", category="danger")
                return redirect(url_for("patient.appointments"))

            # FIX: Add assistant_id parameter (try None first, then 0 if needed)
            try:
                appointment = appointment_repo.create_appointment(
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    date=date,
                    appointment_time=appointment_time,
                    status="PENDING",
                    assistant_id=None  # Try None first
                )
            except TypeError:
                # If None doesn't work, try 0
                appointment = appointment_repo.create_appointment(
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    date=date,
                    appointment_time=appointment_time,
                    status="PENDING",
                    assistant_id=0  # Try 0 if None fails
                )
            
            if appointment:
                flash("Appointment request submitted and is pending approval.", category="success")
            else:
                flash("Failed to submit appointment request. Please try again.", category="danger")
            
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
        try:
            available_slots = appointment_repo.get_available_slots(selected_doctor_id, selected_date)
        except Exception:
            available_slots = []

    return render_template(
        "patient/appointments.html",
        appointments=patient_appointments,
        doctors=doctors,
        available_slots=available_slots,
        selected_doctor_id=selected_doctor_id,
        selected_date=selected_date,
        now=datetime.now()
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
        
        # Get files for this record
        files = []
        if r.id:
            try:
                files = uploaded_repo.get_files_by_record(r.id) or []
            except Exception as e:
                print(f"Error getting files for record {r.id}: {e}")
        
        # Get diagnosis text
        diagnosis_text = r.diagnosis if hasattr(r, 'diagnosis') else "No diagnosis provided"
        
        # Get upload date
        if hasattr(r, 'upload_date'):
            upload_date = r.upload_date
        elif hasattr(r, 'created_at'):
            upload_date = r.created_at
        else:
            upload_date = "Unknown date"
        
        # Prepare file data - FIXED HERE
        files_data = []
        for f in files:
            if hasattr(f, 'file_path'):
                # Extract filename from path
                filename = os.path.basename(f.file_path)
                # Always use static URL for files
                file_url = url_for('static', filename='uploads/' + filename)
                
                files_data.append({
                    "filename": filename,
                    "file_path": file_url  # This will be /static/uploads/filename.jpg
                })
        
        diagnosis_list.append({
            "id": r.id if hasattr(r, 'id') else None,
            "date": upload_date,
            "doctor_name": f"Dr. {doc.firstName} {doc.lastName}" if doc else "Unknown Doctor",
            "text": diagnosis_text,
            "treatment": r.treatment if hasattr(r, 'treatment') else "",
            "followup": r.follow_up_date if hasattr(r, 'follow_up_date') else None,
            "files": files_data,
        })
    
    return render_template("patient/diagnosis.html", 
                         patient=patient, 
                         diagnosis=diagnosis_list)

@patient_bp.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Please log in to access profile.", category="info")
        return redirect(url_for("auth.login"))
    
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Store patient info in session for the auth profile page
    session["patient_profile"] = {
        "id": patient.id,
        "firstName": patient.firstName,
        "lastName": patient.lastName,
        "phone": patient.phone,
        "birth_date": patient.birth_date,
        "address": patient.address,
        "gender": patient.gender
    }
    
    return redirect(url_for("auth.profile"))


@patient_bp.route("/cancel_appointment/<int:id>")  # ADDED: Cancel appointment route
def cancel_appointment(id):
    if not session.get("user_id"):
        flash("Please log in.", category="info")
        return redirect(url_for("auth.login"))
    
    patient = patient_repo.get_by_user_id(session.get("user_id"))
    if not patient:
        flash("Patient profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    if appointment_repo.cancel_appointment(id, patient.id):
        flash("Appointment cancelled successfully.", category="success")
    else:
        flash("Failed to cancel appointment.", category="danger")
    
    return redirect(url_for("patient.appointments"))




# @patient_bp.route("/debug_availability")
# @patient_bp.route("/debug_availability_full")
# def debug_availability_full():
#     """Debug availability and template rendering"""
#     doctor_id = 1
#     date = "2025-12-20"
    
#     # Get doctors
#     doctors = doctor_repo.list_all()
    
#     # Get available slots
#     available_slots = appointment_repo.get_available_slots(doctor_id, date)
    
#     # Get appointments for patient 1 (for testing)
#     patient = patient_repo.get_by_user_id(session.get("user_id"))
#     if patient:
#         appointments = appointment_repo.get_by_patient_id(patient.id)
#     else:
#         appointments = []
    
#     # Render template with debug info
#     return render_template(
#         "patient/appointments.html",
#         appointments=appointments,
#         doctors=doctors,
#         available_slots=available_slots,
#         selected_doctor_id=doctor_id,
#         selected_date=date,
#         now=datetime.now()
#     )