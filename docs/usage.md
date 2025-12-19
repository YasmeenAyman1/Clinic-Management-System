# Clinic Management System — Usage Guide

This guide describes how to use the Clinic Management System from the perspective of each role and how to run and test the project locally.

## Roles & Capabilities

- Admin
  - Approve or reject signup requests for doctors and assistants.
  - Assign approved assistants to a doctor.
  - View pending accounts, search and filter pending list.

- Doctor
  - Log in and view the doctor dashboard (today's appointments and pending approvals).
  - Manage availability (add/remove time ranges for bookings).
  - View patient medical files and add diagnoses (with an optional file upload).
  - Approve or reject pending appointment requests.

- Assistant
  - After admin assignment to a doctor, share the doctor's workload (approve/reject appointments, add diagnosis on behalf of the doctor when allowed).

- Patient
  - Create an account (patient accounts are active immediately).
  - Search for doctors and book an appointment; bookings are created as `PENDING` and require approval by the doctor (or assigned assistant).
  - View own appointments and medical records uploaded by doctors.

## How to run locally

1. Create a virtual environment and install dependencies: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
2. Initialize the DB (MySQL) using `src/database/schema.sql` or adapt the DB code to your environment.
3. Start the app: `python src/app.py`.
4. Open http://localhost:5000 and use the UI.

## Workflow examples

- Doctor signup → Admin approval
  1. Doctor signs up (role = doctor) → status: `pending`.
  2. Admin visits the Admin Dashboard → Approves the doctor → status becomes `active`.
  3. Doctor logs in and configures availability.

- Patient booking → Doctor approval
  1. Patient books an available slot → appointment is created with status `PENDING`.
  2. Doctor or assigned assistant sees pending approvals on their dashboard and approves/rejects the appointment.

## Tests

- Run unit tests with `pytest -q`.
- Tests use a shim when `TESTING=1` to avoid connecting to a real MySQL instance.

## Notes & Security

- CSRF protection: session-based tokens are generated at login and required on sensitive POSTs (admin approvals, appointment approval, availability changes).
- Permissions: endpoints enforce role checks and status checks (active only) where relevant.

If you'd like, I can add step-by-step screenshots, an example seed dataset, or expand the admin audit trail and notification system next.
