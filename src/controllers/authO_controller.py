from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

from repositories.repositories_factory import RepositoryFactory

authO_bp = Blueprint("auth", __name__, url_prefix="/authO")

# Initialize all repositories at module level
user_repo = RepositoryFactory.get_repository("user")
patient_repo = RepositoryFactory.get_repository("patient")
doctor_repo = RepositoryFactory.get_repository("doctor")
assistant_repo = RepositoryFactory.get_repository("assistant")
doctorAvailability_repo = RepositoryFactory.get_repository("doctor_availability")


@authO_bp.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("confirm_password", "")

        # Validation
        if len(full_name.strip().split(" ")) < 2:
            flash("Please enter first and last name.", category="danger")
            return redirect(url_for("auth.signup"))
        if len(email) < 4:
            flash("Email must be at least 4 characters.", category="danger")
            return redirect(url_for("auth.signup"))
        if not phone or len(phone) < 10:
            flash("Please enter a valid phone number (at least 10 digits).", category="danger")
            return redirect(url_for("auth.signup"))
        if password != password_confirm:
            flash("Passwords do not match.", category="danger")
            return redirect(url_for("auth.signup"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", category="danger")
            return redirect(url_for("auth.signup"))
        
        # Check if email already exists
        existing_user = user_repo.get_by_username(email)
        if existing_user:
            flash("Email is already registered.", category="warning")
            return redirect(url_for("auth.signup"))
        
        # Create user and profile based on role
        first_name, last_name = full_name.strip().split(" ", 1)
        role_choice = request.form.get("role", "patient")
        specialization = request.form.get("specialization", "General")
        hashed_pw = generate_password_hash(password)

        try:
            # Patients created active immediately
            if role_choice == "patient":

                print(f"DEBUG: Creating patient user with email: {email}")
                user = user_repo.create_user(email, hashed_pw, role="patient", status="active")

                if user:
                    print(f"DEBUG: User created successfully with ID: {user.id}")
                    print(f"DEBUG: Attempting to create patient with phone: {phone}")
                    # Try different phone formats
                    phone_formats_to_try = [
                        f"+{phone}",           # +201234567890
                        phone,                 # 201234567890
                        f"+20{phone[-10:]}",  # +20 + last 10 digits
                        phone[-10:]           # Last 10 digits only
                    ]
                    
                    patient = None
                    last_error = None
                    
                    for phone_format in phone_formats_to_try:
                        try:
                            print(f"DEBUG: Trying phone format: {phone_format}")
                            patient = patient_repo.create_patient(
                                first_name=first_name, 
                                last_name=last_name, 
                                phone=phone_format, 
                                user_id=user.id, 
                                gender="other",
                                birth_date=None,
                                address=None
                            )
                            if patient:
                                print(f"DEBUG: Patient created successfully with phone: {phone_format}")
                                break
                        except Exception as format_error:
                            last_error = format_error
                            print(f"DEBUG: Failed with format {phone_format}: {format_error}")
                            continue
                    
                    if patient:
                        flash("Account created successfully! Please log in.", category="success")
                        return redirect(url_for("auth.login"))
                    else:
                        # Rollback user creation if patient creation fails
                        print(f"DEBUG: Patient creation failed, rolling back user {user.id}")
                        print(f"DEBUG: Last error: {last_error}")
                        
                        # Try to delete the user
                        try:
                            delete_result = user_repo.delete_user(user.id)
                            print(f"DEBUG: User deletion result: {delete_result}")
                        except Exception as delete_error:
                            print(f"DEBUG: Error deleting user: {delete_error}")
                        
                        # Show specific error message
                        error_msg = "Failed to create patient profile. "
                        if last_error:
                            import mysql.connector
                            if isinstance(last_error, mysql.connector.Error):
                                if last_error.errno == 1062:  # Duplicate entry
                                    error_msg += "Phone number already exists."
                                else:
                                    error_msg += f"Database error: {last_error.msg}"
                            else:
                                error_msg += str(last_error)
                        else:
                            error_msg += "Phone number might already exist or there was a database error."
                        
                        flash(error_msg, category="danger")
                        return redirect(url_for("auth.signup"))
                else:
                    flash("Unable to create user account. Please try again.", category="danger")
                    return redirect(url_for("auth.signup"))

            elif role_choice == "doctor":
                # Doctor signups create a pending user
                user = user_repo.create_user(email, hashed_pw, role="doctor", status="pending")
                if user:
                    doctor = doctor_repo.create_doctor(
                        first_name, 
                        last_name, 
                        phone, 
                        user.id, 
                        specialization=specialization
                    )
                    if doctor:
                        flash("Account created and sent for approval. You will be notified once approved.", category="info")
                        return redirect(url_for("auth.login"))
                    else:
                        user_repo.delete_user(user.id)
                        flash("Failed to create doctor profile. Please try again.", category="danger")
                else:
                    flash("Unable to create account. Please try again.", category="danger")

            elif role_choice == "assistant":
                # Assistant signups create a pending user
                user = user_repo.create_user(email, hashed_pw, role="assistant", status="pending")
                if user:
                    assistant = assistant_repo.create_assistant(
                        first_name, 
                        last_name, 
                        phone, 
                        user.id
                    )
                    if assistant:
                        flash("Account created and sent for approval. An admin will assign you to a doctor.", category="info")
                        return redirect(url_for("auth.login"))
                    else:
                        user_repo.delete_user(user.id)
                        flash("Failed to create assistant profile. Please try again.", category="danger")
                else:
                    flash("Unable to create account. Please try again.", category="danger")
                    
        except Exception as e:
            print(f"Signup error: {e}")
            flash("An error occurred during registration. Please try again.", category="danger")
            
    return render_template("signup.html")

# ADD THIS LINE TO CLOSE THE FUNCTION
# This was likely missing in your code

@authO_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Please enter both email and password.", category="danger")
            return redirect(url_for("auth.login"))
        
        # Get user from database
        user = user_repo.get_by_username(email)
        if not user:
            flash("Invalid email or password.", category="danger")
            return redirect(url_for("auth.login"))
        
        # Check password
        if not check_password_hash(user.password, password):
            flash("Invalid email or password.", category="danger")
            return redirect(url_for("auth.login"))
        
        # Check if account is active
        if user.status != "active":
            flash("Your account is pending approval. Please wait for admin approval.", category="warning")
            return redirect(url_for("auth.login"))
        
        # Set session variables
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        session["status"] = user.status 
        
        # Get user's name based on role
        if user.role == "patient":
            patient = patient_repo.get_by_user_id(user.id)
            if patient:
                session["name"] = f"{patient.firstName} {patient.lastName}"
        elif user.role == "doctor":
            doctor = doctor_repo.get_by_user_id(user.id)
            if doctor:
                session["name"] = f"Dr. {doctor.firstName} {doctor.lastName}"
        elif user.role == "assistant":
            assistant = assistant_repo.get_by_user_id(user.id)
            if assistant:
                session["name"] = f"{assistant.firstName} {assistant.lastName}"
        
        # Generate CSRF token for form protection
        session["csrf_token"] = secrets.token_hex(16)
        
        flash(f"Welcome back, {session.get('name', session.get('username'))}!", category="success")
        
        # Redirect based on role
        if user.role == "patient":
            return redirect(url_for("patient.list_patients"))
        elif user.role == "doctor":
            return redirect(url_for("doctor.doctor_home"))
        elif user.role == "assistant":
            return redirect(url_for("assistant.assistant_home"))
        elif user.role == "admin":
            return redirect(url_for("admin.admin_home"))
        else:
            return redirect(url_for("home"))
    
    return render_template("login.html")


@authO_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", category="success")
    return redirect(url_for("auth.login"))

@authO_bp.route("/debug_patient")
def debug_patient():
    """Debug patient creation"""
    results = []
    
    # Test 1: Check existing patients
    try:
        cursor = patient_repo.db.cursor(dictionary=True)
        cursor.execute("SELECT id, firstName, lastName, phone, user_id FROM patient ORDER BY id DESC LIMIT 5")
        existing = cursor.fetchall()
        cursor.close()
        
        results.append(f"Existing patients (last 5): {existing}")
    except Exception as e:
        results.append(f"Error checking existing: {e}")
    
    # Test 2: Try to create a test patient
    try:
        import time
        test_phone = f"+20test{int(time.time()) % 10000}"
        test_phone_digits = ''.join(filter(str.isdigit, test_phone))
        
        results.append(f"\nTest phone: {test_phone}, Digits only: {test_phone_digits}")
        
        test_patient = patient_repo.create_patient(
            first_name="Debug",
            last_name="Test",
            phone=test_phone_digits,
            user_id=None,
            gender="male",
            birth_date=None,
            address=None
        )
        
        if test_patient:
            results.append(f"Test patient created! ID: {test_patient.id}")
            
            # Clean up
            cursor = patient_repo.db.cursor()
            cursor.execute("DELETE FROM patient WHERE id = %s", (test_patient.id,))
            patient_repo.db.commit()
            cursor.close()
            results.append("Test patient cleaned up")
        else:
            results.append("Test patient creation returned None")
            
    except Exception as e:
        results.append(f"Error in test: {e}")
        import traceback
        results.append(f"Traceback: {traceback.format_exc()}")
    
    return "<br>".join(results)

@authO_bp.route("/dashboard")
def dashboard():
    role = session.get("role")
    if not role:
        flash("You must log in first.", category="error")
        return redirect(url_for("auth.login"))

    # Populate dynamic metrics
    data = {}
    try:
        appointment_repo = RepositoryFactory.get_repository('appointment')
        
        if role == 'patient':
            patient = patient_repo.get_by_user_id(session.get('user_id'))
            appts = appointment_repo.get_by_patient_id(patient.id) if patient else []
            data = {
                'patient_appointments': len(appts),
                'upcoming_appointments': sum(1 for a in appts if getattr(a, 'status', '').upper() in ['BOOKED', 'PENDING'])
            }
        elif role == 'doctor':
            doc = doctor_repo.get_by_user_id(session.get('user_id'))
            today = None
            try:
                from datetime import date
                today = date.today().isoformat()
            except Exception:
                pass
            todays = appointment_repo.get_by_doctor_id(doc.id, today) if doc and today else []
            pending = appointment_repo.list_pending_by_doctor(doc.id) if doc else []
            data = {
                'doctor_patients': len(set(getattr(a, 'patient_id', None) for a in todays)) if todays else 0,
                'today_appointments': len(todays) if todays else 0,
                'total_appointments': len(appointment_repo.get_by_doctor_id(doc.id) or []) if doc else 0,
                'pending_tasks': len(pending) if pending else 0
            }
        elif role == 'assistant':
            assistant = assistant_repo.get_by_user_id(session.get('user_id'))
            if assistant:
                doc_id = assistant.doctor_id
                todays = appointment_repo.get_by_doctor_id(doc_id) or [] if doc_id else []
                data = {
                    'total_patients': 0,
                    'today_appointments': len(todays),
                    'assigned_doctor': doc_id
                }
        elif role == 'admin':
            pending = user_repo.list_pending_users() or []
            audit_repo = RepositoryFactory.get_repository('admin_audit')
            recent = []
            try:
                recent = audit_repo.list_recent(5)
            except Exception:
                recent = []
            data = {
                'pending_users': len(pending),
                'recent_audits': recent
            }
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Fallback to simple placeholders
        if role == 'patient':
            data = {'patient_appointments': 0, 'upcoming_appointments': 0}
        elif role == 'doctor':
            data = {'doctor_patients': 0, 'today_appointments': 0, 'total_appointments': 0, 'pending_tasks': 0}
        elif role == 'assistant':
            data = {'total_patients': 0, 'today_appointments': 0, 'total_doctors': 0}

    return render_template("dashboard.html", user=session, **data)


@authO_bp.route("/profile", methods=['GET', 'POST'])
def profile():
    if "username" not in session:
        flash("You must log in first.", category="danger")
        return redirect(url_for("auth.login"))
    
    user = user_repo.get_by_username(session.get("username"))
    if not user:
        flash("User not found.", category="danger")
        return redirect(url_for("auth.login"))
    
    # Load patient/doctor/assistant data based on role
    patient = None
    doctor = None
    assistant = None
    
    if session.get("role") == "patient":
        patient = patient_repo.get_by_user_id(user.id)
        if patient:
            session["name"] = f"{patient.firstName} {patient.lastName}"
            session["phone"] = patient.phone
            session["birth_date"] = str(patient.birth_date) if patient.birth_date else ""
            session["address"] = patient.address if patient.address else ""
            
    elif session.get("role") == "doctor":
        doctor = doctor_repo.get_by_user_id(user.id)
        if doctor:
            session["name"] = f"{doctor.firstName} {doctor.lastName}"
            session["phone"] = doctor.phone
            session["specialization"] = doctor.specialization

    elif session.get("role") == "assistant":
        assistant = assistant_repo.get_by_user_id(user.id)
        if assistant:
            session["name"] = f"{assistant.firstName} {assistant.lastName}"
            session["phone"] = assistant.phone
    
    if request.method == "POST":
        # Handle profile update
        if "update_profile" in request.form:
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            birth_date = request.form.get("birth_date", "").strip()
            address = request.form.get("address", "").strip()
            specialization = request.form.get("specialization", "").strip()
            
            if not name:
                flash("Name is required.", category="danger")
                return redirect(url_for("auth.profile"))
            
            # Update user email if provided
            if email and email != user.username:
                # Check if email is already taken
                existing = user_repo.get_by_username(email)
                if existing and existing.id != user.id:
                    flash("Email is already taken.", category="danger")
                    return redirect(url_for("auth.profile"))
                user_repo.update_username(user.id, email)
                session["username"] = email
                flash("Email updated successfully.", category="success")
            
            # Update patient/doctor/assistant info
            if session.get("role") == "patient" and patient:
                first_name, last_name = name.split(" ", 1) if " " in name else (name, "")
                patient_repo.update_patient(patient.id, first_name, last_name, phone, birth_date, address)
                session["name"] = name
                session["phone"] = phone
                session["birth_date"] = birth_date
                session["address"] = address
                flash("Profile updated successfully!", category="success")

            elif session.get("role") == "doctor" and doctor:
                first_name, last_name = name.split(" ", 1) if " " in name else (name, "")
                doctor_repo.update_doctor(doctor.id, first_name, last_name, phone, specialization)
                session["name"] = name
                session["phone"] = phone
                session["specialization"] = specialization
                flash("Profile updated successfully!", category="success")

            elif session.get("role") == "assistant" and assistant:
                first_name, last_name = name.split(" ", 1) if " " in name else (name, "")
                cursor = assistant_repo.db.cursor()
                cursor.execute(
                    "UPDATE assistant SET firstName = %s, lastName = %s, phone = %s WHERE id = %s",
                    (first_name, last_name, phone, assistant.id)
                )
                assistant_repo.db.commit()
                cursor.close()
                session["name"] = name
                session["phone"] = phone
                flash("Profile updated successfully!", category="success")
        
        return redirect(url_for("auth.profile"))
    
    return render_template("profile.html", patient=patient, doctor=doctor, assistant=assistant, user=user)


@authO_bp.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if "username" not in session:
        flash("You must log in first.", category="danger")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", category="danger")
            return redirect(url_for("auth.profile"))
        
        if new_password != confirm_password:
            flash("New passwords do not match.", category="danger")
            return redirect(url_for("auth.profile"))
        
        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", category="danger")
            return redirect(url_for("auth.profile"))
        
        user = user_repo.get_by_username(session.get("username"))
        if not user:
            flash("User not found.", category="danger")
            return redirect(url_for("auth.login"))
        
        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect.", category="danger")
            return redirect(url_for("auth.profile"))
        
        # Update password
        hashed_pw = generate_password_hash(new_password)
        cursor = user_repo.db.cursor()
        cursor.execute(
            "UPDATE user SET password = %s WHERE id = %s",
            (hashed_pw, user.id)
        )
        user_repo.db.commit()
        cursor.close()
        
        flash("Password changed successfully!", category="success")
        return redirect(url_for("auth.profile"))
    
    return render_template("change_password.html")


@authO_bp.route("/delete_account", methods=['POST'])
def delete_account():
    if "username" not in session:
        flash("You must log in first.", category="danger")
        return redirect(url_for("auth.login"))
    
    user = user_repo.get_by_username(session.get("username"))
    if not user:
        flash("User not found.", category="danger")
        return redirect(url_for("auth.login"))
    
    # Delete user (cascade will handle patient/doctor/assistant records)
    user_repo.delete_user(user.id)
    
    session.clear()
    flash("Your account has been deleted successfully.", category="success")
    return redirect(url_for("auth.login"))