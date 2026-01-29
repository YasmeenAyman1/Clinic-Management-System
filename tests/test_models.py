import pytest
from datetime import datetime
from models.user_model import User
from models.patient_model import Patient
from models.doctor_model import Doctor
from models.appointment_model import Appointment


def test_user_model():
    """Test User model creation"""
    now = datetime.now()
    user = User(
        id=1,
        username='testuser',
        password='hashed_password',
        role='patient',
        status='active',
        updated_at=now,
        created_at=now
    )
    
    assert user.id == 1
    assert user.username == 'testuser'
    assert user.password == 'hashed_password'
    assert user.role == 'patient'
    assert user.status == 'active'


def test_patient_model():
    """Test Patient model creation"""
    now = datetime.now()
    patient = Patient(
        id=1,
        firstName='John',
        lastName='Doe',
        gender='Male',
        birth_date='1990-01-01',
        phone='+1234567890',
        address='123 Main St',
        user_id=1,
        created_at=now
    )
    
    assert patient.id == 1
    assert patient.firstName == 'John'
    assert patient.lastName == 'Doe'
    assert patient.gender == 'Male'
    assert patient.phone == '+1234567890'


def test_doctor_model():
    """Test Doctor model creation"""
    now = datetime.now()
    doctor = Doctor(
        id=1,
        firstName='Jane',
        lastName='Smith',
        phone='+0987654321',
        schedule='Mon-Fri 9-5',
        user_id=2,
        specialization='Cardiology',
        create_at=now
    )
    
    assert doctor.id == 1
    assert doctor.firstName == 'Jane'
    assert doctor.lastName == 'Smith'
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