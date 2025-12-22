-- Clinic Management System Database Schema
-- This script creates the database and all required tables
-- Safe to run multiple times (uses IF NOT EXISTS)

CREATE DATABASE IF NOT EXISTS clinic;
USE clinic;

-- User table
CREATE TABLE IF NOT EXISTS user(
    id int auto_increment primary key,
    username varchar(150) NOT NULL unique,
    password varchar(255) NOT NULL,
    update_at  Timestamp DEFAULT  CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    role varchar(15) NOT NULL,
    status varchar(15) NOT NULL DEFAULT 'active'
);

-- Patient table
CREATE TABLE IF NOT EXISTS patient(
    id int auto_increment primary key,
    firstName varchar(150) NOT null,
    lastName varchar(150) NOT null,
    gender varchar(10) NOT NULL,
    phone varchar(15) NOT NULL unique,
    birth_date DATE NULL,
    address VARCHAR(255) NULL,
    user_id int NULL unique,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    foreign key (user_id) references user(id) ON DELETE CASCADE
);

    -- Doctor table
    CREATE TABLE IF NOT EXISTS doctor(
        id int auto_increment primary key,
        firstName VARCHAR(150) NOT NULL,
        lastName VARCHAR(150) NOT NULL,
        phone varchar(15) NOT NULL unique,
        schedule VARCHAR(255) NULL,
        specialization VARCHAR(150) NOT NULL,
        create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
        user_id int NULL unique,
        foreign key (user_id) references user(id) ON DELETE CASCADE
    );

-- Assistant table
CREATE TABLE IF NOT EXISTS assistant(
    id int auto_increment primary key,
    firstName varchar(150) NOT NULL,
    lastName VARCHAR(150) NOT NULL,
    phone varchar(15) NOT NULL unique,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    user_id int  NULL unique,
    doctor_id int,
    foreign key (user_id) references user(id) ON DELETE SET NULL,
    foreign key (doctor_id) references doctor(id) ON DELETE SET NULL
);

-- Doctor Schedule table
CREATE TABLE IF NOT EXISTS Doctor_schedule(
    id int auto_increment primary key,
    day_of_week varchar(50) NOT NULL,
    startTime TIME NOT NULL,
    endTime TIME NOT NULL,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    doctor_id int NOT NULL,
    foreign key (doctor_id) references doctor(id) ON DELETE CASCADE
);

-- Doctor explicit availability table (for specific dates and time ranges)
CREATE TABLE IF NOT EXISTS doctor_availability(
    id int auto_increment primary key,
    doctor_id int NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    create_at Timestamp DEFAULT CURRENT_TIMESTAMP,
    foreign key (doctor_id) references doctor(id) ON DELETE CASCADE,
    CONSTRAINT availability_unique UNIQUE (doctor_id, date, start_time, end_time)
);

-- Appointment table
CREATE TABLE IF NOT EXISTS Appointment(
    id int auto_increment primary key,
    date date NOT null,
    appointment_time time NOT NULL,
    status varchar(50) NOT NULL DEFAULT "BOOKED",
    follow_up_date DATE NULL,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    assistant_id int NULL,
    doctor_id int NULL,
    patient_id int NULL,
    note varchar(1000) NULL,
    foreign key (doctor_id) references doctor(id) ON DELETE CASCADE,
    foreign key (patient_id) references patient(id) ON DELETE CASCADE,
    foreign key (assistant_id) references assistant(id) ON DELETE SET NULL,
);

-- Medical Record table
CREATE TABLE IF NOT EXISTS MedicalRecord(
    id int auto_increment primary key,
    diagnosis varchar(1000) NOT NULL,
    treatment varchar(1000) NOT  NULL,
    uploaded_by_user_id INT NULL,
    upload_date DATE NOT NULL,
    follow_up_date DATE NULL,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    doctor_id int NULL,
    patient_id int NOT NULL,
    appointment_id int NOT NULL ,
    foreign key (doctor_id) references doctor(id) ON DELETE SET NULL,
    foreign key (patient_id) references patient(id) ON DELETE CASCADE,
    foreign key (appointment_id) references Appointment(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_user_id) REFERENCES user(id) ON DELETE SET NULL
);

-- Uploaded File table
CREATE TABLE IF NOT EXISTS UploadedFile(
    id int auto_increment primary key,
    file_path VARCHAR(500) NOT NULL,
    file_type varchar(50)NOT NULL,
    uploaded_by_user_id INT NULL,
    upload_date date NOT Null,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    record_id int NULL,
    patient_id int NULL,
    appointment_id int NULL,
    foreign key(record_id) references MedicalRecord(id) ON DELETE CASCADE,
    foreign key (patient_id) references patient(id) ON DELETE CASCADE,
    foreign key (appointment_id) references Appointment(id) ON DELETE CASCADE,
    foreign key (uploaded_by_user_id) REFERENCES user(id) ON DELETE SET NULL
);
-- Contact Table
CREATE Table IF NOT EXISTS Contact(
    id int auto_increment primary key,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    create_at Timestamp DEFAULT CURRENT_TIMESTAMP
);

-- Admin audit trail table
CREATE TABLE IF NOT EXISTS admin_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    target_user_id INT NULL,
    target_type VARCHAR(50) NULL,
    details VARCHAR(500) NULL,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
    category VARCHAR(50),
    due_date DATE,
    assigned_to INT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES assistant(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_due_date (due_date),
    INDEX idx_assigned_to (assigned_to)
);