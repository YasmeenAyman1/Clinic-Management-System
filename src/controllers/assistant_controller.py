from flask import Flask, Blueprint, render_template, redirect, url_for
# from repositories.repositories_factory import RepositoryFactory

assistant_bp = Blueprint('assistant', __name__, url_prefix='/assistant')

@assistant_bp.route('/')
def assistant_home():
    return render_template('assistant_home.html')
@assistant_bp.route('/tasks')
def manage_tasks():
    return "Manage tasks will be displayed here."
    # tasks = Task.get_all_tasks()
    # return render_template('manage_tasks.html', tasks=tasks)
@assistant_bp.route('/profile/<username>')
def assistant_profile(username):
    assistant = User.get_by_username(username)
    if assistant:
        return render_template('assistant_profile.html', assistant=assistant)
    else:
        return "Assistant not found", 404
@assistant_bp.route('/reports')
def view_reports():
    return "Assistant reports will be displayed here."

@assistant_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    return render_template('assistant_schedule.html')
    # if request.method == 'POST':
    #     # Handle schedule update logic here
    #     pass
    # schedule
