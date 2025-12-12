from flask import Blueprint, render_template
# from repositories.repositories_factory import RepositoryFactory

user_bp = Blueprint("user", __name__, url_prefix="/users")

@user_bp.route("/")
def list_users():
    repo = RepositoryFactory.get_repository("user")
    users = repo.get_all()
    return render_template("user/list.html", users=users)

@user_bp.route("/<int:id>")
def view_user(id):
    repo = RepositoryFactory.get_repository("user")
    user = repo.get_by_id(id)
    return render_template("user/profile.html", user=user)