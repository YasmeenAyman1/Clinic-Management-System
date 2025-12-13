from flask import Flask, render_template, redirect, url_for, Blueprint, request, flash, session
# from repositories.repositories_factory import RepositoryFactory

authO_bp = Blueprint('auth', __name__, url_prefix='/auth')
users = {
    "doctor1": {"password": "doc123", "role": "doctor"},
    "assistant1": {"password": "assist123", "role": "assistant"},
    "patient1": {"password": "patient123", "role": "patient"}
}


@authO_bp.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        email = request.form.get("email")
        password = request.form.get("pswd")
        password_confirm = request.form.get("pswd2")
        if len(first_name) < 2 or len(last_name) < 2:
            flash("First and Last names must be at least 2 characters.", category="error")
            return redirect(url_for("auth.signup"))
        elif len(email) < 4 :
            flash("Email must be greater than 3 characters.", category="error")
            return redirect(url_for("auth.signup"))
        elif len(password) < 1 :
            flash("Password must be at least 1 characters.", category="error")
            return redirect(url_for("auth.signup"))
        elif password != password_confirm :
            flash("Passwords don't match.", category="error")
            return redirect(url_for("auth.signup"))
        else:
            # Here you would typically add the user to your database
            users[email] = {"password": password, "role": "patient"}  # default role patient
            flash("Account created successfully!", category="success")
            return redirect(url_for("auth.login"))
    return render_template("signup.html")

@authO_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.get(username) # Simulated user lookup

        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']  # store role in session
            flash("Logged in successfully!", category="success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Invalid username or password.", category="error")
            return redirect(url_for("auth.login"))
    return render_template("login.html")
    
@authO_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", category="success")
    return redirect(url_for("auth.login"))

@authO_bp.route("/dashboard")
def dashboard():
    role = session.get('role')
    if not role:
        flash("You must log in first.", category="error")
        return redirect(url_for("auth.login"))

    # Dummy data for display
    data = {}
    if role == "patient":
        data = {
            "patient_appointments": 5,
            "upcoming_appointments": 2
        }
    elif role == "doctor":
        data = {
            "doctor_patients": 20,
            "today_appointments": 4,
            "total_appointments": 50,
            "pending_tasks": 3
        }
    elif role == "assistant":
        data = {
            "total_patients": 100,
            "today_appointments": 10,
            "total_doctors": 5
        }

    return render_template("dashboard.html", user=session, **data)

@authO_bp.route("/profile")
def profile():
    if 'username' not in session:
        flash("You must log in first.", category="error")
        return redirect(url_for("auth.login"))
    return render_template("profile.html")

@authO_bp.route("/settings")
def settings():
    return render_template("settings.html")
#=============================================
@authO_bp.route("/reset_password")
def reset_password():
    return render_template("reset_password.html")


@authO_bp.route("/change_password")
def change_password():
    return render_template("change_password.html")