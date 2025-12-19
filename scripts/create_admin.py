from werkzeug.security import generate_password_hash
from repositories.repositories_factory import RepositoryFactory

user_repo = RepositoryFactory.get_repository("user")


def prompt(prompt_text, default=None):
    val = input(f"{prompt_text}{' ['+default+']' if default else ''}: ").strip()
    return val if val else default


def create_admin(email: str, password: str):
    existing = user_repo.get_by_username(email)
    if existing:
        print(f"User with email {email} already exists (id={existing.id}).")
        return existing
    hashed = generate_password_hash(password)
    return user_repo.create_user(email, hashed, role='admin', status='active')


def main():
    print("--- Create Admin Account ---")
    email = prompt("Admin email")
    password = prompt("Password (will be hashed)")

    if not email or not password:
        print("Email and password required.")
        return

    admin = create_admin(email, password)
    if admin:
        print(f"Created admin {admin.username} (id={admin.id})")
    else:
        print("Failed to create admin account.")

if __name__ == '__main__':
    main()
