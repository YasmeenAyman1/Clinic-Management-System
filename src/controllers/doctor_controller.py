from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app
import os
from werkzeug.utils import secure_filename

from repositories.repositories_factory import RepositoryFactory

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')
user_repo = RepositoryFactory.get_repository("user")
doctor_repo = RepositoryFactory.get_repository("doctor")
appointment_repo = RepositoryFactory.get_repository("appointment")
medical_repo = RepositoryFactory.get_repository("medical_record")
uploaded_repo = RepositoryFactory.get_repository("uploaded_file")
patient_repo = RepositoryFactory.get_repository("patient")
availability_repo = RepositoryFactory.get_repository("doctor_availability")
# Audit repository for recording approvals/rejections
audit_repo = RepositoryFactory.get_repository("admin_audit")

@doctor_bp.route('/')
def doctor_home():
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    if session.get("role") != "doctor":
        flash("Access denied. Doctor access required.", category="danger")
        return redirect(url_for("auth.dashboard"))
    
    doctor = doctor_repo.get_by_user_id(session.get("user_id"))
    if not doctor:
        flash("Doctor profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Get today's appointments
    from datetime import date
    today = date.today().isoformat()
    appointments = appointment_repo.get_by_doctor_id(doctor.id, today)
    pending = appointment_repo.list_pending_by_doctor(doctor.id)
    
    return render_template('doctor/doctor_home.html', doctor=doctor, appointments=appointments, pending=pending)


@doctor_bp.route('/appointment/<int:appointment_id>/approve', methods=['POST'])
def approve_appointment(appointment_id):
    if not session.get('user_id') or session.get('role') not in ['doctor', 'assistant']:
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('doctor.doctor_home'))

    # Resolve acting doctor's id
    if session.get('role') == 'doctor':
        doctor = doctor_repo.get_by_user_id(session.get('user_id'))
        doctor_id = doctor.id if doctor else None
    else:
        assistant = RepositoryFactory.get_repository('assistant').get_by_user_id(session.get('user_id'))
        doctor_id = assistant.doctor_id if assistant else None

    if not doctor_id:
        flash('Unable to resolve doctor for approval.', category='danger')
        return redirect(url_for('doctor.doctor_home'))

    success = appointment_repo.approve_appointment(appointment_id, doctor_id)
    if success:
        # record audit of approval by current session user
        try:
            audit_repo.create_entry(session.get('user_id'), 'approve_appointment', target_user_id=appointment_id, target_type='appointment', details=f'doctor_id={doctor_id}')
        except Exception:
            pass
        flash('Appointment approved.', category='success')
    else:
        flash('Failed to approve appointment.', category='danger')
    return redirect(url_for('doctor.doctor_home'))


@doctor_bp.route('/appointment/<int:appointment_id>/reject', methods=['POST'])
def reject_appointment(appointment_id):
    if not session.get('user_id') or session.get('role') not in ['doctor', 'assistant']:
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('doctor.doctor_home'))

    # Resolve acting doctor's id
    if session.get('role') == 'doctor':
        doctor = doctor_repo.get_by_user_id(session.get('user_id'))
        doctor_id = doctor.id if doctor else None
    else:
        assistant = RepositoryFactory.get_repository('assistant').get_by_user_id(session.get('user_id'))
        doctor_id = assistant.doctor_id if assistant else None

    if not doctor_id:
        flash('Unable to resolve doctor for rejection.', category='danger')
        return redirect(url_for('doctor.doctor_home'))

    success = appointment_repo.reject_appointment(appointment_id, doctor_id)
    if success:
        try:
            audit_repo.create_entry(session.get('user_id'), 'reject_appointment', target_user_id=appointment_id, target_type='appointment', details=f'doctor_id={doctor_id}')
        except Exception:
            pass
        flash('Appointment rejected.', category='warning')
    else:
        flash('Failed to reject appointment.', category='danger')
    return redirect(url_for('doctor.doctor_home'))

@doctor_bp.route('/patient/<int:pid>/medical_file')
def medical_file(pid):
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    if session.get("role") != "doctor":
        flash("Access denied. Doctor access required.", category="danger")
        return redirect(url_for("auth.dashboard"))

    patient = patient_repo.get_by_id(pid)
    if not patient:
        flash("Patient not found.", category="warning")
        return redirect(url_for("doctor.doctor_home"))

    records = medical_repo.get_records_by_patient(pid)
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

    return render_template('doctor/medical_file.html', patient=patient, diagnosis=diagnosis_list)

@doctor_bp.route('/patients')
def manage_patients():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('doctor/manage_patients.html')

@doctor_bp.route('/schedule', methods=['GET'])
def schedule():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    try:
        availability = availability_repo.list_by_doctor(doctor.id)
    except Exception:
        availability = []

    return render_template('doctor/availability.html', doctor=doctor, availability=availability)


@doctor_bp.route('/availability/add', methods=['POST'])
def add_availability():
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('doctor.schedule'))

    date = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')

    if not date or not start_time or not end_time:
        flash('All fields are required.', category='danger')
        return redirect(url_for('doctor.schedule'))

    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    av = availability_repo.create_availability(doctor.id, date, start_time, end_time)
    if av:
        flash('Availability added.', category='success')
    else:
        flash('Failed to add availability (may conflict).', category='danger')
    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/availability/<int:av_id>/delete', methods=['POST'])
def delete_availability(av_id):
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('doctor.schedule'))

    success = availability_repo.delete_availability(av_id)
    if success:
        flash('Availability removed.', category='success')
    else:
        flash('Failed to remove availability.', category='danger')
    return redirect(url_for('doctor.schedule'))

@doctor_bp.route('/profile/<username>')
def doctor_profile(username):
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    user = user_repo.get_by_username(username)
    if not user:
        flash("Doctor not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    doctor = doctor_repo.get_by_user_id(user.id)
    if not doctor:
        flash("Doctor profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    return render_template('doctor/doctor_profile.html', doctor=doctor, user=user)

@doctor_bp.route('/reports')
def view_reports():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    return render_template('doctor/view_reports.html')

@doctor_bp.route('/diagnose/<int:pid>', methods=['POST'])
def diagnose(pid):
    # Compatibility: doctors and assistants (with access) can add diagnoses
    if not session.get("user_id") or session.get("role") not in ["doctor", "assistant"]:
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))

    # If assistant, ensure assistant is assigned to doctor's patients (basic check)
    if session.get('role') == 'assistant':
        assistant = RepositoryFactory.get_repository('assistant').get_by_user_id(session.get('user_id'))
        if not assistant:
            flash('Assistant profile not found.', category='warning')
            return redirect(url_for('auth.dashboard'))

    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))

    diagnosis_text = request.form.get('diagnosis', '').strip()
    treatment_text = request.form.get('treatment', '').strip()
    followup = request.form.get('followup') or None

    if not diagnosis_text or not treatment_text:
        flash("Diagnosis and treatment are required.", category="danger")
        return redirect(url_for('doctor.medical_file', pid=pid))

    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    # if assistant, resolve to the assigned doctor's id
    if session.get('role') == 'assistant':
        assistant = RepositoryFactory.get_repository('assistant').get_by_user_id(session.get('user_id'))
        doctor_id = assistant.doctor_id if assistant else None
    else:
        doctor_id = doctor.id if doctor else None

    record = medical_repo.create_record(
        patient_id=pid,
        doctor_id=doctor_id,
        diagnosis=diagnosis_text,
        treatment=treatment_text,
        follow_up_date=followup,
        uploaded_by_user_id=session.get('user_id')
    )

    # Handle file upload
    if record and 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            uploads_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filepath = os.path.join(uploads_dir, filename)
            file.save(filepath)
            # store relative path
            rel_path = os.path.join('uploads', filename)
            uploaded_repo.save_file(filename, rel_path, session.get('user_id'), record_id=record.id, patient_id=pid, file_type=file.mimetype)

    if record:
        flash("Diagnosis saved successfully.", category="success")
    else:
        flash("Failed to save diagnosis.", category="danger")

    return redirect(url_for('doctor.medical_file', pid=pid))