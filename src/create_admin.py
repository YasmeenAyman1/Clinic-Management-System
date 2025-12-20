# from werkzeug.security import generate_password_hash
# from repositories.repositories_factory import RepositoryFactory

# user_repo = RepositoryFactory.get_repository("user")


# def prompt(prompt_text, default=None):
#     val = input(f"{prompt_text}{' ['+default+']' if default else ''}: ").strip()
#     return val if val else default


# def create_admin(email: str, password: str):
#     existing = user_repo.get_by_username(email)
#     if existing:
#         print(f"User with email {email} already exists (id={existing.id}).")
#         return existing
#     hashed = generate_password_hash(password)
#     return user_repo.create_user(email, hashed, role='admin', status='active')


# def main():
#     print("--- Create Admin Account ---")
#     email = prompt("Admin email")
#     password = prompt("Password (will be hashed)")

#     if not email or not password:
#         print("Email and password required.")
#         return

#     admin = create_admin(email, password)
#     if admin:
#         print(f"Created admin {admin.username} (id={admin.id})")
#     else:
#         print("Failed to create admin account.")

# if __name__ == '__main__':
#     main()
"""
Script to create an admin user in the database
Run this: python create_admin.py
"""

from werkzeug.security import generate_password_hash
from repositories.repositories_factory import RepositoryFactory

def create_admin_user():
    """Create an admin user"""
    
    print("=" * 50)
    print("CREATE ADMIN USER")
    print("=" * 50)
    
    # Get admin details
    email = input("Enter admin email (e.g., admin@clinic.com): ").strip()
    if not email:
        email = "admin@clinic.com"
    
    password = input("Enter admin password (min 6 chars): ").strip()
    if not password or len(password) < 6:
        password = "admin123"
        print(f"Using default password: {password}")
    
    try:
        user_repo = RepositoryFactory.get_repository("user")
        
        # Check if admin already exists
        existing = user_repo.get_by_username(email)
        if existing:
            print(f"\n❌ ERROR: User with email '{email}' already exists!")
            print("Try a different email or delete the existing user first.")
            return
        
        # Create admin user
        hashed_password = generate_password_hash(password)
        admin_user = user_repo.create_user(
            username=email,
            password_hash=hashed_password,
            role="admin",
            status="active"
        )
        
        if admin_user:
            print("\n✅ SUCCESS! Admin user created successfully!")
            print(f"\nLogin Credentials:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"\nYou can now login at: http://localhost:5000/auth/login")
        else:
            print("\n❌ ERROR: Failed to create admin user!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("1. Your database is running")
        print("2. Database credentials in db_singleton.py are correct")
        print("3. All tables are created")


if __name__ == "__main__":
    create_admin_user()