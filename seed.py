# seed.py
from database import init_db, SessionLocal
from models import User, UserRole, SMTPProfile, Setting

def seed():
    init_db()
    db = SessionLocal()
    
    # Admin user
    admin = db.query(User).filter_by(email="admin@automation.studio").first()
    if not admin:
        admin = User(
            email="admin@automation.studio",
            password_hash=User.hash_password("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created (admin@automation.studio / admin123)")
    
    # Manager user
    manager = db.query(User).filter_by(email="manager@automation.studio").first()
    if not manager:
        manager = User(
            email="manager@automation.studio",
            password_hash=User.hash_password("manager123"),
            full_name="Manager",
            role=UserRole.MANAGER
        )
        db.add(manager)
        db.commit()
        print("✅ Manager user created (manager@automation.studio / manager123)")
    
    # Viewer user
    viewer = db.query(User).filter_by(email="viewer@automation.studio").first()
    if not viewer:
        viewer = User(
            email="viewer@automation.studio",
            password_hash=User.hash_password("viewer123"),
            full_name="Viewer",
            role=UserRole.VIEWER
        )
        db.add(viewer)
        db.commit()
        print("✅ Viewer user created (viewer@automation.studio / viewer123)")
    
    db.close()

if __name__ == "__main__":
    seed()