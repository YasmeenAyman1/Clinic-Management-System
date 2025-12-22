from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
from datetime import date, datetime, timedelta

from repositories.repositories_factory import RepositoryFactory

assistant_bp = Blueprint('assistant', __name__, url_prefix='/assistant')
user_repo = RepositoryFactory.get_repository("user")
patient_repo = RepositoryFactory.get_repository("patient")  
assistant_repo = RepositoryFactory.get_repository("assistant")
appointment_repo = RepositoryFactory.get_repository("appointment")
doctor_repo = RepositoryFactory.get_repository("doctor")
availability_repo = RepositoryFactory.get_repository("doctor_availability")
task_repo = RepositoryFactory.get_repository("task")  # You'll need to create this repository

@assistant_bp.route('/')
def assistant_home():
    # Check login
    if "user_id" not in session:
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    # Check role
    user_role = session.get("role")
    if user_role != "assistant":
        flash("Access denied. Assistant access required.", category="danger")
        if user_role == "doctor":
            return redirect(url_for("doctor.doctor_home"))
        elif user_role == "patient":
            return redirect(url_for("patient.patient_home"))
        else:
            return redirect(url_for("auth.dashboard"))
    
    # Get assistant data
    try:
        assistant = assistant_repo.get_by_user_id(session["user_id"])
    except Exception as e:
        flash(f"Error loading assistant profile: {str(e)}", category="danger")
        return redirect(url_for("auth.dashboard"))
    
    if not assistant:
        flash("Assistant profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # Get today's date
    today = date.today().strftime("%Y-%m-%d")
    
    # Get today's appointments using repository
    today_appointments = []
    try:
        # Use the proper method to get appointments by doctor or assistant
        if assistant.doctor_id:
            today_appointments = appointment_repo.get_by_doctor_id(assistant.doctor_id, today)
        else:
            today_appointments = appointment_repo.get_today_appointments(today)
    except Exception as e:
        flash(f"Error loading appointments: {str(e)}", category="danger")
    
    # Get appointment stats
    stats = {
        'total_appointments': len(today_appointments) if today_appointments else 0,
        'booked_appointments': len([a for a in (today_appointments or []) if getattr(a, 'status', '') in ['BOOKED', 'CONFIRMED', 'PENDING']]),
        'completed_appointments': len([a for a in (today_appointments or []) if getattr(a, 'status', '') == 'COMPLETED'])
    }
    
    # Get doctors for dropdown - USE REPOSITORY
    doctors = []
    try:
        doctors = doctor_repo.list_all()  # This should work now
    except Exception as e:
        flash(f"Error loading doctors: {str(e)}", category="danger")
        doctors = []
    
    return render_template(
        'assistant/assistant_home.html', 
        assistant=assistant, 
        today_appointments=today_appointments,
        today=today,
        total_appointments=stats.get('total_appointments', 0),
        booked_appointments=stats.get('booked_appointments', 0),
        completed_appointments=stats.get('completed_appointments', 0),
        assistant_name=f"{assistant.firstName} {assistant.lastName}" if assistant else "Assistant",
        doctors=doctors
    )

@assistant_bp.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        assistant = assistant_repo.get_by_user_id(session["user_id"])
        
        if request.method == 'POST':
            # Handle task creation
            title = request.form.get('title')
            description = request.form.get('description')
            priority = request.form.get('priority', 'medium')
            category = request.form.get('category')
            due_date = request.form.get('due_date')
            
            if title:
                task = task_repo.create_task(
                    title=title,
                    description=description,
                    priority=priority,
                    category=category,
                    due_date=due_date,
                    status='pending',
                    assigned_to=assistant.id,
                    created_by=session['user_id']
                )
                if task:
                    flash("Task created successfully!", category="success")
                else:
                    flash("Failed to create task.", category="danger")
        
        # Get tasks
        tasks = task_repo.get_assistant_tasks(assistant.id)
        
        return render_template('assistant/manage_tasks.html', 
                             assistant=assistant,
                             tasks=tasks)
    except Exception as e:
        flash(f"Error loading tasks: {str(e)}", category="danger")
        return redirect(url_for("assistant.assistant_home"))
@assistant_bp.route('/reports')
def view_reports():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        assistant = assistant_repo.get_by_user_id(session["user_id"])
        
        # Get report data
        today = date.today().strftime("%Y-%m-%d")
        
        # Get appointments data
        appointments = []
        if assistant.doctor_id:
            # Get appointments for the doctor for the last 30 days
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = date.today().strftime("%Y-%m-%d")
            appointments = appointment_repo.get_appointments_by_date_range(
                assistant.doctor_id, start_date, end_date
            )
        
        # Calculate statistics
        stats = {
            'total_appointments': len(appointments) if appointments else 0,
            'completed': len([a for a in (appointments or []) if getattr(a, 'status', '') == 'COMPLETED']),
            'cancelled': len([a for a in (appointments or []) if getattr(a, 'status', '') == 'CANCELLED']),
            'no_show': len([a for a in (appointments or []) if getattr(a, 'status', '') == 'NO_SHOW']),
        }
        
        return render_template('assistant/view_reports.html',
                             assistant=assistant,
                             stats=stats,
                             appointments=appointments)
    except Exception as e:
        flash(f"Error loading reports: {str(e)}", category="danger")
        return redirect(url_for("assistant.assistant_home"))

@assistant_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        assistant = assistant_repo.get_by_user_id(session["user_id"])
        
        print(f"DEBUG: Assistant ID: {assistant.id}, Doctor ID: {assistant.doctor_id}")  # ADD THIS
        
        # Get doctor data if assistant is assigned to a doctor
        doctor = None
        availability = []
        appointments = []
        
        if assistant.doctor_id:
            print(f"DEBUG: Assistant is assigned to doctor {assistant.doctor_id}")  # ADD THIS

            # Get doctor - USE REPOSITORY
            try:
                doctor = doctor_repo.get_by_id(assistant.doctor_id)
                print(f"DEBUG: Doctor found: {doctor.firstName} {doctor.lastName}")  # ADD THIS
            except Exception as e:
                print(f"DEBUG: Error loading doctor: {e}")  # ADD THIS
                flash(f"Error loading doctor: {str(e)}", category="danger")
                doctor = None

            # Get availability
            availability = availability_repo.list_by_doctor(assistant.doctor_id)
            print(f"DEBUG: Availability data: {availability}")  # ADD THIS
            print(f"DEBUG: Number of availability entries: {len(availability)}")  # ADD THIS
            
            # Get appointments for next 7 days
            start_date = date.today().strftime("%Y-%m-%d")
            end_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
            appointments = appointment_repo.get_appointments_by_date_range(
                assistant.doctor_id, start_date, end_date
            )
            print(f"DEBUG: Number of appointments: {len(appointments)}")  # ADD THIS
        
        else:
            print(f"DEBUG: Assistant is NOT assigned to any doctor")  # ADD THIS
        
        return render_template('assistant/assistant_schedule.html',
                             assistant=assistant,
                             doctor=doctor,
                             availability=availability,
                             appointments=appointments,
                             today=date.today().strftime("%Y-%m-%d"))
    except Exception as e:
        flash(f"Error loading schedule: {str(e)}", category="danger")
        return redirect(url_for("assistant.assistant_home"))

@assistant_bp.route('/search_patient', methods=['GET', 'POST'])
def search_patient():
    if not session.get("user_id") or session.get("role") not in ["assistant", "doctor"]:
        flash("Access denied. Assistant or Doctor access required.", category="danger")
        return redirect(url_for("auth.login"))
    
    results = []
    query = ""
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        if query:
            # Search using repository
            results = patient_repo.search_patients(query)
            
            if not results:
                flash(f"No patients found for '{query}'", category="warning")
            else:
                flash(f"Found {len(results)} patient(s)", category="success")
        else:
            flash("Please enter a search term", category="danger")
    
    return render_template('assistant/search_patient.html', 
                         results=results, 
                         query=query)

@assistant_bp.route('/patient_file/<int:pid>')
def patient_file(pid):
    if not session.get("user_id") or session.get("role") not in ["assistant", "doctor"]:
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        # Get patient using repository
        patient = patient_repo.get_by_id(pid)
        
        if not patient:
            flash("Patient not found", category="danger")
            return redirect(url_for("assistant.search_patient"))
        
        # Get appointments using repository
        appointments = appointment_repo.get_by_patient_id(pid)
        
        doctors = []
        try:
            doctors = doctor_repo.list_all()
        except Exception as e:
            flash(f"Error loading doctors: {str(e)}", category="danger")
            doctors = []   

        return render_template('assistant/patient_file.html',
                             patient=patient,
                             appointments=appointments or [],
                             doctors=doctors)
        
    except Exception as e:
        flash(f"Error loading patient file: {str(e)}", category="danger")
        return redirect(url_for("assistant.search_patient"))

@assistant_bp.route('/add_appointment', methods=['POST'])
def add_appointment():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    # Get form data
    patient_id = request.form.get("patient_id", type=int)
    doctor_id = request.form.get("doctor_id", type=int)
    appointment_date = request.form.get("appointment_date")
    appointment_time = request.form.get("appointment_time")
    notes = request.form.get("notes", "")
    
    # Validate required fields
    if not doctor_id or not appointment_date or not appointment_time:
        flash("Please fill in all required fields: Doctor, Date, and Time.", category="danger")
        return redirect(request.referrer or url_for("assistant.assistant_home"))
    
    try:
        # Get Assistant ID using repository
        assistant = assistant_repo.get_by_user_id(session.get("user_id"))
        if not assistant:
            flash("Assistant not found.", category="danger")
            return redirect(url_for("auth.login"))
        
        # Add appointment using repository
        appointment = appointment_repo.create_appointment(
            patient_id=patient_id,  # Can be None for available slots
            doctor_id=doctor_id,
            date=appointment_date,
            appointment_time=appointment_time,
            assistant_id=assistant.id,
            status="AVAILABLE" if not patient_id else "BOOKED",
            notes=notes
        )
        
        if appointment:
            if patient_id:
                flash("Appointment booked successfully!", category="success")
            else:
                flash("Available slot added successfully!", category="success")
        else:
            flash("Failed to add appointment. The time slot may be taken.", category="danger")
    
    except Exception as e:
        flash(f"Error adding appointment: {str(e)}", category="danger")
    
    return redirect(request.referrer or url_for("assistant.assistant_home"))

@assistant_bp.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel/remove an appointment slot"""
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        # Get assistant info
        assistant = assistant_repo.get_by_user_id(session["user_id"])
        if not assistant:
            flash("Assistant profile not found.", category="danger")
            return redirect(request.referrer or url_for("assistant.assistant_home"))
        
        # Use appointment repository to cancel with assistant_id
        success = appointment_repo.cancel_appointment_by_assistant(
            appointment_id, 
            assistant.id  # Pass assistant.id
        )
        
        if success:
            flash("Appointment cancelled successfully.", category="success")
        else:
            flash("Failed to cancel appointment. You can only cancel appointments for your assigned doctor.", category="danger")
    
    except Exception as e:
        flash(f"Error cancelling appointment: {str(e)}", category="danger")
    
    return redirect(request.referrer or url_for("assistant.assistant_home"))

@assistant_bp.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    """Update appointment status (Confirm, Complete, etc.)"""
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    status = request.form.get("status")
    
    if not status:
        flash("No status specified.", category="danger")
        return redirect(request.referrer or url_for("assistant.assistant_home"))
    
    try:
        success = appointment_repo.update_appointment_status(appointment_id, status)
        
        if success:
            flash(f"Appointment status updated to {status}.", category="success")
        else:
            flash("Failed to update appointment status.", category="danger")
    
    except Exception as e:
        flash(f"Error updating appointment status: {str(e)}", category="danger")
    
    return redirect(request.referrer or url_for("assistant.assistant_home"))

@assistant_bp.route('/api/check_availability', methods=['POST'])
def check_availability():
    """Check doctor availability for a specific date and time"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    time = data.get('time')
    
    if not all([doctor_id, date, time]):
        return jsonify({"error": "Missing parameters"}), 400
    
    try:
        # Check if doctor has availability for this date
        availability = availability_repo.check_availability(doctor_id, date, time)
        
        # Check if appointment already exists for this time
        existing = appointment_repo.get_appointment_by_datetime(doctor_id, date, time)
        
        return jsonify({
            "available": availability and not existing,
            "availability": availability,
            "existing": existing is not None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@assistant_bp.route('/api/get_available_slots', methods=['POST'])
def get_available_slots():
    """Get available time slots for a doctor on a specific date"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    
    if not all([doctor_id, date]):
        return jsonify({"error": "Missing parameters"}), 400
    
    try:
        # Get doctor's availability for the date
        availability = availability_repo.get_availability_by_date(doctor_id, date)
        
        # Get existing appointments for the date
        appointments = appointment_repo.get_by_doctor_id(doctor_id, date)
        
        # Calculate available slots
        slots = []
        for avail in availability:
            # Generate time slots based on availability
            start = datetime.strptime(avail.start_time, "%H:%M")
            end = datetime.strptime(avail.end_time, "%H:%M")
            
            # Generate 30-minute slots
            current = start
            while current < end:
                slot_time = current.strftime("%H:%M")
                
                # Check if slot is already booked
                booked = any(
                    getattr(appt, 'appointment_time', '').strftime("%H:%M") == slot_time
                    for appt in appointments or []
                )
                
                if not booked:
                    slots.append(slot_time)
                
                current = current + timedelta(minutes=30)
        
        return jsonify({"slots": slots})
    except Exception as e:
        return jsonify({"error": str(e)}), 500