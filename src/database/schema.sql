create database clinic;
use clinic;

create table user(
    id int auto_increment primary key,
    username varchar(150) NOT NULL unique,
    password varchar(150) NOT NULL,
    update_at  Timestamp DEFAULT  CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    role varchar(15) NOT NULL
);

create table patient(
    id int auto_increment primary key,
    firstName varchar(150) NOT null,
    lastName varchar(150) NOT null,
    gender varchar(10) NOT NULL,
    phone varchar(15) NOT NULL unique,
    user_id int NULL unique,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    foreign key (user_id) references user(id) ON DELETE CASCADE
);

create table doctor(
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

create table assistant(
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

create table Doctor_schedule(
    id int auto_increment primary key,
    day_of_week varchar(50) NOT NULL,
    startTime TIME NOT NULL,
    endTime TIME NOT NULL,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    doctor_id int NOT NULL,
    foreign key (doctor_id) references doctor(id) ON DELETE CASCADE
);

create table Appointment(
    id int auto_increment primary key,
    date date NOT null,
    appointment_time time NOT NULL,
    status varchar(50) NOT NULL DEFAULT "BOOKED",
    follow_up_date DATE NULL,
    create_at  Timestamp DEFAULT  CURRENT_TIMESTAMP,
    assistant_id int NULL,
    doctor_id int NULL,
    patient_id int NULL,
    foreign key (doctor_id) references doctor(id) ON DELETE CASCADE,
    foreign key (patient_id) references patient(id) ON DELETE CASCADE,
    foreign key (assistant_id) references assistant(id) ON DELETE SET NULL,
    CONSTRAINT appointment_slot unique (doctor_id, date, appointment_time)
);
 
create table MedicalRecord(
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

CREATE TABLE UploadedFile(
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

CREATE TABLE Admin_Audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_user_id INT NULL,
    target_type VARCHAR(50) NULL,
    details VARCHAR(500) NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES user(id) ON DELETE SET NULL
);
