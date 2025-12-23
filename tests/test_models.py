import pytest
from datetime import datetime
from src.models.User_model import User
from src.models.Patient_model import Patient
from src.models.Doctor_model import Doctor
from src.models.Appointment_model import Appointment

def test_user_model():
    """Test User model creation"""
    user = User(
        id=1,
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password',
        role='patient',
        is_active=True
    )
    
    assert user.id == 1
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.role == 'patient'
    assert user.is_active == True
    assert user.check_password('hashed_password') is False  # This is hashed, not plain

def test_patient_model():
    """Test Patient model creation"""
    patient = Patient(
        id=1,
        firstName='John',
        lastName='Doe',
        gender='Male',
        phone='+1234567890',
        birth_date='1990-01-01',
        address='123 Main St',
        user_id=1
    )
    
    assert patient.id == 1
    assert patient.firstName == 'John'
    assert patient.lastName == 'Doe'
    assert patient.full_name == 'John Doe'
    assert patient.gender == 'Male'
    assert patient.phone == '+1234567890'

def test_doctor_model():
    """Test Doctor model creation"""
    doctor = Doctor(
        id=1,
        firstName='Jane',
        lastName='Smith',
        specialization='Cardiology',
        phone='+0987654321',
        user_id=2
    )
    
    assert doctor.id == 1
    assert doctor.firstName == 'Jane'
    assert doctor.lastName == 'Smith'
    assert doctor.full_name == 'Jane Smith'
    assert doctor.specialization == 'Cardiology'

def test_appointment_model():
    """Test Appointment model creation"""
    appointment = Appointment(
        id=1,
        patient_id=1,
        doctor_id=1,
        date='2024-01-15',
        appointment_time='10:30',
        status='PENDING'
    )
    
    assert appointment.id == 1
    assert appointment.patient_id == 1
    assert appointment.doctor_id == 1
    assert appointment.date == '2024-01-15'
    assert appointment.appointment_time == '10:30'
    assert appointment.status == 'PENDING'