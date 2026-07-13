# services/audit_service.py
from database import SessionLocal
from models.audit_log import AuditLog
from datetime import datetime

def log_action(action: str, entity_type: str = "", entity_id: int = None, details: str = ""):
    """Quick audit log helper"""
    try:
        db = SessionLocal()
        log = AuditLog(
            user_id=1,  # Default until login is added
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=str(details)[:500],
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.close()
    except:
        pass  # Don't crash if audit logging fails