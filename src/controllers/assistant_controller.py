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
    # التحقق من تسجيل الدخول أولاً
    if "user_id" not in session:
        flash("Please log in first.", category="info")
        return redirect(url_for("auth.login"))
    
    # التحقق من دور المستخدم
    user_role = session.get("role")
    if user_role != "assistant":
        flash("Access denied. Assistant access required.", category="danger")
        # إعادة التوجيه حسب الدور
        if user_role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        elif user_role == "patient":
            return redirect(url_for("patient.dashboard"))
        else:
            return redirect(url_for("auth.dashboard"))
    
    # الحصول على بيانات المساعد
    try:
        assistant = assistant_repo.get_by_user_id(session["user_id"])
    except Exception as e:
        flash(f"Error loading assistant profile: {str(e)}", category="danger")
        return redirect(url_for("auth.dashboard"))
    
    if not assistant:
        flash("Assistant profile not found.", category="warning")
        return redirect(url_for("auth.dashboard"))
    
    # الحصول على مواعيد اليوم
    today = date.today().strftime("%Y-%m-%d")
    
    # استعلام قاعدة البيانات
    today_appointments = []
    try:
        cursor = assistant_repo.db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                a.id, 
                TIME_FORMAT(a.appointment_time, '%%H:%%i') as appointment_time,
                a.status, 
                a.date, 
                a.doctor_id, 
                a.patient_id,
                CONCAT(d.firstName, ' ', d.lastName) as doctor_name,
                CONCAT(p.firstName, ' ', p.lastName) as patient_name, 
                p.phone
            FROM Appointment a
            LEFT JOIN doctor d ON a.doctor_id = d.id
            LEFT JOIN patient p ON a.patient_id = p.id
            WHERE a.date = %s
            ORDER BY a.appointment_time ASC
            """,
            (today,)
        )
        today_appointments = cursor.fetchall()
    except Exception as e:
        flash(f"Error loading appointments: {str(e)}", category="danger")
    finally:
        if 'cursor' in locals():
            cursor.close()
    
    return render_template(
        'assistant/assistant_home.html', 
        assistant=assistant, 
        today_appointments=today_appointments,
        today_date=today
    )

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
# def search_patient():
#     if not session.get("user_id") or session.get("role") not in ["assistant", "doctor"]:
#         flash("Access denied. Assistant or Doctor access required.", category="danger")
#         return redirect(url_for("auth.login"))
#     return render_template('assistant/search_patient.html')
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
            # البحث باستخدام repository
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

# @assistant_bp.route('/patient_file/<int:pid>')
# def patient_file(pid):
#     # You can fetch patient data here using patient_repo
#     patient = patient_repo.get_by_id(pid)
#     if not patient:
#         flash("Patient not found.", category="warning")
#         return redirect(url_for('assistant.search_patient'))
#     return render_template('assistant/patient_file.html', patient=patient)
@assistant_bp.route('/patient_file/<int:pid>')
def patient_file(pid):
    if not session.get("user_id") or session.get("role") not in ["assistant", "doctor"]:
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    try:
        # جلب بيانات المريض
        patient = patient_repo.get_by_id(pid)
        
        if not patient:
            flash("Patient not found", category="danger")
            return redirect(url_for("assistant.search_patient"))
        
        # جلب المواعيد
        appointments = appointment_repo.get_patient_appointments(pid)
        
        # جلب السجلات الطبية
        medical_records = []  # تحتاج لدالة في medical_record_repository
        
        return render_template('assistant/patient_file.html',
                             patient=patient,
                             appointments=appointments,
                             medical_records=medical_records)
        
    except Exception as e:
        flash(f"Error loading patient file: {str(e)}", category="danger")
        return redirect(url_for("assistant.search_patient"))


@assistant_bp.route('/add_appointment', methods=['POST'])

def add_appointment():
    if not session.get("user_id") or session.get("role") != "assistant":
        flash("Access denied.", category="danger")
        return redirect(url_for("auth.login"))
    
    # الحصول على البيانات من الفورم - بأسماء الحقول الصحيحة
    doctor_id = request.form.get("doctor_id", type=int)
    appointment_date = request.form.get("appointment_date")  # تم التصحيح من "date" إلى "appointment_date"
    appointment_time = request.form.get("appointment_time")
    
    print(f"DEBUG - doctor_id: {doctor_id}")
    print(f"DEBUG - appointment_date: {appointment_date}")
    print(f"DEBUG - appointment_time: {appointment_time}")
    
    # التحقق من البيانات المطلوبة
    if not doctor_id or not appointment_date or not appointment_time:
        flash("Please fill in all fields: Doctor, Date, and Time.", category="danger")
        return redirect(url_for("assistant.assistant_home"))
    
    try:
        # الحصول على Assistant ID
        assistant = assistant_repo.get_by_user_id(session.get("user_id"))
        if not assistant:
            flash("Assistant not found.", category="danger")
            return redirect(url_for("auth.login"))
        
        # إضافة الموعد كموعد متاح (بدون patient_id)
        appointment = appointment_repo.create_appointment(
            patient_id=None,  # موعد متاح بدون مريض
            doctor_id=doctor_id,
            date=appointment_date,  # استخدم نفس الاسم المخزن في الدالة
            appointment_time=appointment_time,
            assistant_id=assistant.id
        )
        
        if appointment:
            flash("Appointment slot added successfully!", category="success")
        else:
            flash("Failed to add appointment. The time slot may be taken.", category="danger")
    
    except Exception as e:
        flash(f"Error adding appointment: {str(e)}", category="danger")
        print(f"Error in add_appointment: {e}")
    
    return redirect(url_for("assistant.assistant_home"))
