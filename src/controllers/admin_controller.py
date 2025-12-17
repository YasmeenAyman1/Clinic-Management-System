from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from repositories.repositories_factory import RepositoryFactory

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

user_repo = RepositoryFactory.get_repository('user')
doctor_repo = RepositoryFactory.get_repository('doctor')
assistant_repo = RepositoryFactory.get_repository('assistant')
audit_repo = RepositoryFactory.get_repository('admin_audit')

@admin_bp.before_request
def enforce_admin():
    # Ensure user is logged in and is an active admin for all admin routes
    if session.get('role') != 'admin' or session.get('status') != 'active':
        flash('Access denied. Admin only.', category='danger')
        return redirect(url_for('auth.login'))

    # Protect POST endpoints with a session-based CSRF token
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not csrf_token or csrf_token != session.get('csrf_token'):
            flash('Invalid CSRF token', category='danger')
            return redirect(url_for('admin.admin_home'))

def require_admin():
    if session.get('role') != 'admin' or session.get('status') != 'active':
        flash('Access denied. Admin only.', category='danger')
        return False
    return True


@admin_bp.route('/')
def admin_home():
    if not require_admin():
        return redirect(url_for('auth.login'))

    # Pagination for pending list
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    try:
        pending = user_repo.list_pending_users() or []
        doctors = doctor_repo.list_all() or []
    except Exception:
        pending = []
        doctors = []

    total = len(pending)
    pending_count = total
    # slice pending list for pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated = pending[start:end]
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    # fetch recent audits
    try:
        recent_audits = audit_repo.list_recent(20)
    except Exception:
        recent_audits = []

    return render_template('admin/index.html', pending=paginated, pending_count=pending_count, doctors=doctors, page=page, per_page=per_page, total_pages=total_pages, recent_audits=recent_audits)


@admin_bp.route('/pending/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    if not require_admin():
        return redirect(url_for('auth.login'))
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('admin.admin_home'))
    # fetch user
    user = user_repo.get_by_id(user_id)
    if not user or user.status != 'pending':
        flash('User not found or not pending.', category='warning')
        return redirect(url_for('admin.admin_home'))

    # For assistants, allow assignment to a doctor
    assign_doctor_id = request.form.get('assign_doctor', type=int)

    cursor = user_repo.db.cursor()
    cursor.execute("UPDATE user SET status = 'active' WHERE id = %s", (user_id,))
    user_repo.db.commit()
    cursor.close()

    # If assistant and doctor assignment provided, update assistant profile
    if user.role == 'assistant' and assign_doctor_id:
        cursor = assistant_repo.db.cursor()
        cursor.execute("UPDATE assistant SET doctor_id = %s WHERE user_id = %s", (assign_doctor_id, user_id))
        assistant_repo.db.commit()
        cursor.close()

    # Record audit entry
    try:
        audit_repo.create_entry(session.get('user_id'), 'approve_user', target_user_id=user_id, target_type=user.role, details=f'assign_doctor={assign_doctor_id}' if assign_doctor_id else None)
    except Exception:
        pass

    flash('User approved and activated.', category='success')
    return redirect(url_for('admin.admin_home'))


@admin_bp.route('/pending/<int:user_id>/reject', methods=['POST'])
def reject_user(user_id):
    if not require_admin():
        return redirect(url_for('auth.login'))
    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('csrf_token'):
        flash('Invalid CSRF token', category='danger')
        return redirect(url_for('admin.admin_home'))
    user = user_repo.get_by_id(user_id)
    if not user or user.status != 'pending':
        flash('User not found or not pending.', category='warning')
        return redirect(url_for('admin.admin_home'))

    # delete user and its profile
    user_repo.delete_user(user_id)

    # audit
    try:
        audit_repo.create_entry(session.get('user_id'), 'reject_user', target_user_id=user_id, target_type=user.role, details=None)
    except Exception:
        pass

    flash('User rejected and removed.', category='info')
    return redirect(url_for('admin.admin_home'))
