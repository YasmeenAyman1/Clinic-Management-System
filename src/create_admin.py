from werkzeug.security import generate_password_hash
from repositories.repositories_factory import RepositoryFactory
user_repo = RepositoryFactory.get_repository("user")

def create_admin_user():
    """Create an admin user"""

    email = "admin@gmail.com"  # استخدمي الايميل اللي تحبي
    password = "admin123"       # كلمة السر اللي تحبي

    try:
        user_repo = RepositoryFactory.get_repository("user")

        # تأكدي إذا المستخدم موجود
        existing = user_repo.get_by_username(email)
        if existing:
            print(f"User {email} already exists. Updating password...")
            # حدثي كلمة السر بالمشفرة الصحيحة
            hashed_password = generate_password_hash(password, method='scrypt')
            user_repo.update_password(existing.id, hashed_password)
            print("Password updated successfully!")
            return

        # لو المستخدم مش موجود، أنشئيه
        hashed_password = generate_password_hash(password, method='scrypt')
        admin_user = user_repo.create_user(
            username=email,
            password_hash=hashed_password,
            role="admin",
            status="active"
        )

        if admin_user:
            print("✅ Admin user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
        else:
            print("❌ Failed to create admin user!")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    create_admin_user()