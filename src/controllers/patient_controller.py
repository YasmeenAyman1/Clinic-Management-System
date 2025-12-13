from flask import Blueprint, render_template, url_for, redirect, request
# from repositories.repositories_factory import RepositoryFactory

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/')
def list_patients():
    return "List of patients will be displayed here."
    # patients = User.get_all()
    # return render_template('patient_home.html', patients=patients)



@patient_bp.route('/appointments', methods=['GET', 'POST'])
def appointments():
    return render_template('/patient/appointments.html')
    # if request.method == 'POST':
    #     # Handle appointment booking logic here
    #     pass
    # appointments = Appointment.get_by_patient(current_user.id)
    # return render_template('appointments.html', appointments=appointments)    

@patient_bp.route('/profile/<username>')
def patient_profile(username):
    patient = User.get_by_username(username)
    if patient:
        return redirect('profile.html', patient=patient)
    else:
        return "Patient not found", 404