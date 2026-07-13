# seed.py
from database import init_db, SessionLocal
from models.user import User, UserRole
from models.smtp_profile import SMTPProfile
from models.setting import Setting

def seed():
    init_db()
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter_by(email="admin@automation.studio").first()
    if not admin:
        admin = User(
            email="admin@automation.studio",
            password_hash="hashed_placeholder",
            full_name="Admin User",
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created.")
    else:
        print("Admin already exists.")
    
    db.close()

if __name__ == "__main__":
    seed()