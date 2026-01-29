from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app
import os
from datetime import date, datetime, timedelta
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
    
    session['doctor_name'] = f"{doctor.firstName} {doctor.lastName}"

    # Get today's appointments
    today = date.today().isoformat()
    raw_appointments = appointment_repo.get_by_doctor_id(doctor.id, today)
    pending = appointment_repo.list_pending_by_doctor(doctor.id)
    
    # Transform appointments to include patient info for template
    appointments = []
    for apt in raw_appointments:
        patient = patient_repo.get_by_id(apt.patient_id) if apt.patient_id else None
        patient_name = f"{patient.firstName} {patient.lastName}" if patient else "Unknown"
        
        appointments.append({
            'id': apt.id,
            'patient_id': apt.patient_id,
            'patient': patient_name,
            'time': apt.appointment_time,
            'status': apt.status,
            'date': apt.date
        })
    
    return render_template('doctor/doctor_home.html', doctor=doctor, appointments=appointments, pending=pending)


@doctor_bp.route('/appointment/<int:appointment_id>/approve', methods=['POST'])
def approve_appointment(appointment_id):
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    # Get the current doctor
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    # Approve the appointment
    success = appointment_repo.update_appointment_status(appointment_id, 'APPROVED')
    
    if success:
        flash('Appointment approved successfully!', category='success')
        
        # Optional: Send notification to patient
        try:
            appointment = appointment_repo.get_by_id(appointment_id)
            if appointment and appointment.patient_id:
                # You could add notification logic here
                pass
        except Exception:
            pass
            
    else:
        flash('Failed to approve appointment.', category='danger')
    
    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/appointment/<int:appointment_id>/reject', methods=['POST'])
def reject_appointment(appointment_id):
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    # Get the current doctor
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    # Reject the appointment
    success = appointment_repo.update_appointment_status(appointment_id, 'REJECTED')
    
    if success:
        flash('Appointment rejected.', category='warning')
    else:
        flash('Failed to reject appointment.', category='danger')
    
    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel an approved/booked appointment"""
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    # Get the current doctor
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    # Cancel the appointment
    success = appointment_repo.update_appointment_status(appointment_id, 'CANCELLED')
    
    if success:
        flash('Appointment cancelled.', category='warning')
    else:
        flash('Failed to cancel appointment.', category='danger')
    
    return redirect(url_for('doctor.schedule'))


@doctor_bp.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
def complete_appointment(appointment_id):
    """Mark appointment as completed after consultation"""
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

    # Get the current doctor
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    # Complete the appointment
    success = appointment_repo.update_appointment_status(appointment_id, 'COMPLETED')
    
    if success:
        flash('Appointment marked as completed.', category='success')
    else:
        flash('Failed to mark appointment as completed.', category='danger')
    
    return redirect(url_for('doctor.schedule'))

@doctor_bp.route('/prescriptions')
def prescriptions():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    
    return render_template('doctor/prescriptions.html', doctor=doctor)
    
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

    # Get doctor's appointments with this patient
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    patient_appointments = []
    if doctor:
        # Get appointments for this patient with the current doctor
        patient_appointments = appointment_repo.get_appointments_by_patient_and_doctor(
            patient_id=pid, 
            doctor_id=doctor.id
        )
        if not patient_appointments:
            # Try to get any appointments if repository method doesn't exist
            try:
                cursor = appointment_repo.db.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, appointment_date, status FROM appointment WHERE patient_id = %s AND doctor_id = %s ORDER BY appointment_date DESC",
                    (pid, doctor.id)
                )
                patient_appointments = cursor.fetchall()
                cursor.close()
            except Exception:
                patient_appointments = []

    records = medical_repo.get_records_by_patient(pid)
    diagnosis_list = []
    
    print(f"\n=== DEBUG: Processing patient {pid} medical records ===")
    
    for r in records:
        doc = doctor_repo.get_by_id(r.doctor_id) if r.doctor_id else None
        files = uploaded_repo.get_files_by_record(r.id) if r.id else []
        
        print(f"\nRecord ID: {r.id}")
        print(f"  Number of files: {len(files)}")
        
        files_data = []
        for f in files:
            if f.file_path:
                # Clean path for web
                file_path = f.file_path.replace('\\', '/')
                
                # Get filename from the UploadedFile object
                filename = f.filename if hasattr(f, 'filename') and f.filename else os.path.basename(file_path)
                
                # Check if file exists
                full_path = os.path.join(current_app.static_folder, file_path)
                file_exists = os.path.exists(full_path)
                
                print(f"  - File: {filename}")
                print(f"    Path: {file_path}")
                print(f"    Exists: {file_exists}")
                
                files_data.append({
                    "filename": filename,
                    "file_path": file_path,
                    "exists": file_exists
                })
        
        diagnosis_list.append({
            "id": r.id,
            "date": r.upload_date,
            "doctor_name": f"{doc.firstName} {doc.lastName}" if doc else "Unknown",
            "text": r.diagnosis,
            "treatment": r.treatment,
            "followup": r.follow_up_date,
            "files": files_data,
        })

    print(f"\n=== DEBUG: Summary ===")
    print(f"Total records: {len(diagnosis_list)}")
    total_files = sum(len(d['files']) for d in diagnosis_list)
    print(f"Total files: {total_files}")

    return render_template('doctor/medical_file.html', 
                         patient=patient, 
                         diagnosis=diagnosis_list,
                         appointments=patient_appointments)

@doctor_bp.route('/add_patient', methods=['POST'])
def add_patient():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    # Get form data
    first_name = request.form.get('firstName', '').strip()
    last_name = request.form.get('lastName', '').strip()
    gender = request.form.get('gender', '').strip()
    phone = request.form.get('phone', '').strip()
    birth_date = request.form.get('birth_date', '').strip() or None
    address = request.form.get('address', '').strip() or None
    notes = request.form.get('notes', '').strip() or None
    
    print(f"DEBUG add_patient: firstName={first_name}, lastName={last_name}, gender={gender}, phone={phone}")
    
    # Validate required fields
    if not all([first_name, last_name, gender, phone]):
        flash('Please fill all required fields (First Name, Last Name, Gender, Phone)', category='danger')
        return redirect(url_for('doctor.manage_patients'))
    
    # Format phone number (add + prefix if missing and it's all digits)
    def format_phone(phone_str):
        if not phone_str:
            return phone_str
        
        # Remove all non-digit characters first
        digits = ''.join(filter(str.isdigit, phone_str))
        
        if not digits:
            return phone_str
        
        # Add + prefix if not present
        if not phone_str.startswith('+'):
            # If it looks like an Egyptian number (starts with 20 or 10 digits)
            if digits.startswith('20') and len(digits) == 11:  # +20xxxxxxxxx
                return f"+{digits}"
            elif len(digits) == 10:  # 10-digit local number
                return f"+20{digits}"  # Assume Egypt country code
            else:
                return f"+{digits}"
        return phone_str
    
    phone_formatted = format_phone(phone)
    print(f"DEBUG: Original phone: {phone}, Formatted: {phone_formatted}")
    
    # Check if phone already exists BEFORE trying to create
    try:
        cursor = patient_repo.db.cursor(dictionary=True)
        cursor.execute("SELECT id, firstName, lastName FROM patient WHERE phone = %s", (phone_formatted,))
        existing_patient = cursor.fetchone()
        cursor.close()
        
        if existing_patient:
            flash(f'Phone number {phone_formatted} is already registered to patient #{existing_patient["id"]} ({existing_patient["firstName"]} {existing_patient["lastName"]}). Please use a different phone number.', category='danger')
            return redirect(url_for('doctor.manage_patients'))
    except Exception as e:
        print(f"Error checking phone existence: {e}")
        # Continue anyway, the create_patient will catch it
    
    # Add patient to database
    try:
        patient = patient_repo.create_patient(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            phone=phone_formatted,  # Use formatted phone
            birth_date=birth_date,
            address=address,
            user_id=None
        )
        
        print(f"DEBUG: Patient creation result: {patient}")
        
        if patient:
            print(f"DEBUG: Patient created successfully with ID: {patient.id}")
            
            # If there are notes, create a medical record
            if notes:
                doctor = doctor_repo.get_by_user_id(session.get('user_id'))
                if doctor:
                    try:
                        medical_repo.create_record(
                            patient_id=patient.id,
                            doctor_id=doctor.id,
                            diagnosis="Initial Consultation Notes",
                            treatment=notes,
                            follow_up_date=None,
                            appointment_id=None,
                            uploaded_by_user_id=session.get('user_id')
                        )
                        print(f"DEBUG: Medical record created for patient {patient.id}")
                    except Exception as e:
                        print(f"Error creating medical record: {e}")
                        # Don't fail the whole operation
            
            flash(f'Patient {first_name} {last_name} added successfully! (ID: #{patient.id})', category='success')
        else:
            flash('Failed to add patient. The phone number might already exist or there was a database error.', category='danger')
    
    except Exception as e:
        print(f"Error in add_patient: {e}")
        flash(f'Failed to create patient profile. Error: {str(e)}', category='danger')
    
    return redirect(url_for('doctor.manage_patients'))

@doctor_bp.route('/search_patient')
def search_patient():
    """Allow doctors to search for patients."""
    if not session.get("user_id"):
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    if session.get("role") != "doctor":
        flash("Access denied. Doctor access required.", category="danger")
        return redirect(url_for("auth.dashboard"))
    
    # Check if there's a search query
    search_query = request.args.get('search', '').strip()
    
    # Get doctor info
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    
    # Initialize patients list
    patients = []
    
    # If there's a search query, search for patients
    if search_query:
        # Use the repository search method
        patients = patient_repo.search_patients(search_query)
        
        if not patients:
            flash(f'No patients found for "{search_query}"', category='info')
    
    # Also get medical record counts for each patient
    patient_records_count = {}
    patient_last_visits = {}
    
    for patient in patients:
        records_count = medical_repo.get_patient_records_count(patient.id)
        patient_records_count[patient.id] = records_count
        
        last_visit = medical_repo.get_last_visit(patient.id)
        patient_last_visits[patient.id] = last_visit
    
    # Get recent patients for the "initial state" section
    recent_patients = []
    if not search_query:  # Only get recent patients when not searching
        recent_patients = patient_repo.get_all_patients()[:5] if hasattr(patient_repo, 'get_all_patients') else []
    
    return render_template('doctor/search_patient.html', 
                         search_query=search_query, 
                         patients=patients, 
                         doctor=doctor,
                         patient_records_count=patient_records_count,
                         patient_last_visits=patient_last_visits,
                         recent_patients=recent_patients)  # Add this

@doctor_bp.route('/patients')
def manage_patients():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    # Get all patients from repository
    all_patients = patient_repo.get_all_patients()
    
    # Get statistics using repository methods
    total_patients = len(all_patients) if all_patients else 0
    
    # Get new patients this month using repository method
    new_this_month = patient_repo.get_new_patients_this_month()
    
    # Get today's date
    today = date.today()
    today_str = today.isoformat()
    
    # Get doctor info
    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    
    # Get appointments for today
    appointments_today = []
    active_today = 0
    appointments_count = 0
    appointment_ids_today = set()
    
    if doctor:
        appointments_today = appointment_repo.get_by_doctor_id(doctor.id, today_str)
        appointments_count = len(appointments_today) if appointments_today else 0
        if appointments_today:
            for app in appointments_today:
                if hasattr(app, 'patient_id') and app.patient_id:
                    appointment_ids_today.add(app.patient_id)
            active_today = len(appointment_ids_today)
    
    # Get medical records data for each patient using repository methods
    patient_records_count = {}
    patient_last_visits = {}
    
    if all_patients:
        for patient in all_patients:
            # Get medical records count using repository method
            records_count = medical_repo.get_patient_records_count(patient.id)
            patient_records_count[patient.id] = records_count
            
            # Get last visit date using repository method
            last_visit = medical_repo.get_last_visit(patient.id)
            patient_last_visits[patient.id] = last_visit
    
    return render_template('doctor/manage_patients.html', 
                         patients=all_patients,
                         total_patients=total_patients,
                         active_today=active_today,
                         appointments_count=appointments_count,
                         new_this_month=new_this_month,
                         appointment_ids_today=appointment_ids_today,
                         patient_records_count=patient_records_count,
                         patient_last_visits=patient_last_visits,
                         doctor=doctor)


@doctor_bp.route('/availability/add', methods=['POST'])
def add_availability():
    if not session.get('user_id') or session.get('role') != 'doctor':
        flash('Access denied.', category='danger')
        return redirect(url_for('auth.login'))

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
    
    success = availability_repo.delete_availability(av_id)
    if success:
        flash('Availability removed.', category='success')
    else:
        flash('Failed to remove availability.', category='danger')
    return redirect(url_for('doctor.schedule'))

from datetime import datetime, date, timedelta

@doctor_bp.route('/schedule', methods=['GET'])
def schedule():
    if not session.get("user_id") or session.get("role") != "doctor":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))

    doctor = doctor_repo.get_by_user_id(session.get('user_id'))
    if not doctor:
        flash('Doctor profile not found.', category='warning')
        return redirect(url_for('auth.dashboard'))

    # -----------------------------
    # Dates
    # -----------------------------
    today = date.today()

    week_start = request.args.get('week_start')
    filter_date = request.args.get('filter_date')
    status_filter = request.args.get('status', 'all')

    if week_start:
        try:
            week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            week_start_date = today
    else:
        week_start_date = today

    week_end_date = week_start_date + timedelta(days=6)

    if filter_date:
        try:
            filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
        except ValueError:
            filter_date = None

    # -----------------------------
    # Week days
    # -----------------------------
    week_days = []
    for i in range(6):
        day_date = week_start_date + timedelta(days=i)
        week_days.append({
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A')
        })

    # -----------------------------
    # Data
    # -----------------------------
    availability = availability_repo.list_by_doctor(doctor.id) or []
    all_appointments = appointment_repo.get_by_doctor_id(doctor.id, None)

    # -----------------------------
    # Filter appointments
    # -----------------------------
    appointments = []
    for appointment in all_appointments:
        # Case-insensitive status filter
        if status_filter != 'all' and appointment.status and appointment.status.lower() != status_filter.lower():
            continue
        if filter_date and appointment.date != filter_date:
            continue

        patient = patient_repo.get_by_id(appointment.patient_id) if appointment.patient_id else None

        appointments.append({
            'id': appointment.id,
            'date': appointment.date,
            'time': getattr(appointment, 'appointment_time', None),
            'patient_id': appointment.patient_id,
            'patient': {
                'firstName': patient.firstName,
                'lastName': patient.lastName,
                'phone': patient.phone
            } if patient else None,
            'type': getattr(appointment, 'type', 'regular'),
            'status': appointment.status
        })

    # -----------------------------
    # Statistics
    # -----------------------------
    today_appointments_count = sum(
        1 for a in all_appointments if a.date == today
    )

    week_appointments_count = sum(
        1 for a in all_appointments
        if week_start_date <= a.date <= week_end_date
    )

    # -----------------------------
    # Time slots
    # -----------------------------
    time_slots = []
    for hour in range(9, 17):
        for minute in (0, 30):
            time_slots.append(f"{hour:02d}:{minute:02d}")

    weekly_schedule = {}

    # -----------------------------
    # Availability
    # -----------------------------
    for slot in availability:
        # Convert date to ISO string format to match week_days keys
        slot_date = slot.date.isoformat() if hasattr(slot.date, 'isoformat') else str(slot.date)
        weekly_schedule.setdefault(slot_date, {})

        # SAFE time parsing (HH:MM or HH:MM:SS)
        try:
            start_time = datetime.strptime(slot.start_time, "%H:%M:%S")
        except ValueError:
            start_time = datetime.strptime(slot.start_time, "%H:%M")

        try:
            end_time = datetime.strptime(slot.end_time, "%H:%M:%S")
        except ValueError:
            end_time = datetime.strptime(slot.end_time, "%H:%M")

        current = start_time
        while current < end_time:
            time_str = current.strftime("%H:%M")
            weekly_schedule[slot_date][time_str] = {
                'type': 'available',
                'slot_id': slot.id
            }
            current += timedelta(minutes=30)

    # -----------------------------
    # Appointments on schedule (exclude cancelled/rejected - they should show as available)
    # -----------------------------
    for appointment in all_appointments:
        # Skip cancelled/rejected appointments - slot should be available again
        if appointment.status and appointment.status.upper() in ['CANCELLED', 'REJECTED']:
            continue
        
        # Convert date to ISO string format to match week_days keys
        app_date = appointment.date.isoformat() if hasattr(appointment.date, 'isoformat') else str(appointment.date)
        weekly_schedule.setdefault(app_date, {})

        app_time = getattr(appointment, 'appointment_time', None)
        if app_time:
            # Ensure time is in HH:MM format to match time_slots
            if hasattr(app_time, 'strftime'):
                app_time = app_time.strftime('%H:%M')
            elif isinstance(app_time, str) and len(app_time) > 5:
                # Trim seconds if present (HH:MM:SS -> HH:MM)
                app_time = app_time[:5]
            
            patient = patient_repo.get_by_id(appointment.patient_id) if appointment.patient_id else None
            patient_name = f"{patient.firstName} {patient.lastName}" if patient else "Unknown"

            weekly_schedule[app_date][app_time] = {
                'type': 'appointment',
                'appointment_id': appointment.id,
                'patient_name': patient_name,
                'status': appointment.status
            }

    pending_appointments_count = sum(
        1 for a in all_appointments if a.status and a.status.upper() == 'PENDING'
    )

    return render_template(
        'doctor/schedule.html',
        doctor=doctor,
        availability=availability,
        appointments=appointments,
        today=today.isoformat(),
        week_start=week_start_date.isoformat(),
        week_days=week_days,
        time_slots=time_slots,
        weekly_schedule=weekly_schedule,
        filter_date=filter_date.isoformat() if filter_date else None,
        status_filter=status_filter,
        today_appointments_count=today_appointments_count,
        week_appointments_count=week_appointments_count,
        available_slots_count=len(availability),
        pending_appointments_count=pending_appointments_count
    )

@doctor_bp.app_template_filter('get_day_name')
def get_day_name(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A')
    except Exception:
        return "Unknown"

@doctor_bp.app_template_filter('time_to_minutes')
def time_to_minutes(time_str):
    try:
        if ':' in time_str:
            hours, minutes = time_str.split(':')
            return int(hours) * 60 + int(minutes)
        return 0
    except Exception:
        return 0

@doctor_bp.app_template_filter('is_past_date')
def is_past_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_obj < datetime.today().date()
    except Exception:
        return False
    

@doctor_bp.route('/diagnose/<int:pid>', methods=['POST'])
def diagnose(pid):
    if not session.get("user_id") or session.get("role") not in ["doctor", "assistant"]:
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))

    diagnosis_text = request.form.get('diagnosis', '').strip()
    treatment_text = request.form.get('treatment', '').strip()
    followup = request.form.get('followup') or None
    # REMOVE appointment_id or make it optional
    appointment_id = request.form.get('appointment_id', type=int) or None

    if not diagnosis_text or not treatment_text:
        flash("Diagnosis and treatment are required.", category="danger")
        return redirect(url_for('doctor.medical_file', pid=pid))

    # Resolve doctor ID
    if session.get('role') == 'assistant':
        assistant = RepositoryFactory.get_repository('assistant').get_by_user_id(session.get('user_id'))
        doctor_id = assistant.doctor_id if assistant else None
    else:
        doctor = doctor_repo.get_by_user_id(session.get('user_id'))
        doctor_id = doctor.id if doctor else None

    # CREATE RECORD WITH OPTIONAL APPOINTMENT_ID
    record = medical_repo.create_record(
        patient_id=pid,
        doctor_id=doctor_id,
        diagnosis=diagnosis_text,
        treatment=treatment_text,
        follow_up_date=followup,
        appointment_id=appointment_id,  # This can be None
        uploaded_by_user_id=session.get('user_id')
    )

    if record and 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            uploads_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Use forward slashes for URL compatibility
            filepath = os.path.join(uploads_dir, filename)
            # Save the file
            file.save(filepath)
            
            # Use forward slash for the relative path
            rel_path = 'uploads/' + filename  # Use forward slash
            
            uploaded_repo.save_file(
                filename, 
                rel_path,  # Now uses forward slash
                session.get('user_id'), 
                record_id=record.id, 
                patient_id=pid, 
                file_type=file.mimetype
            )

    if record:
        flash("Diagnosis saved successfully.", category="success")
    else:
        flash("Failed to save diagnosis.", category="danger")

    return redirect(url_for('doctor.medical_file', pid=pid))