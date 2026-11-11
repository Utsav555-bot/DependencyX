import logging
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.entities import ActivityLog

# Standard Python logger
logger = logging.getLogger("dependencyx")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def log_activity(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = "127.0.0.1"
) -> ActivityLog:
    """
    Persists security audit event to the database and standard logging output.
    """
    logger.info(f"AUDIT_LOG: user={user_id} action={action} entity={entity_type}:{entity_id} details={details}")
    try:
        activity = ActivityLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    except Exception as e:
        logger.error(f"Failed to record activity log: {str(e)}")
        db.rollback()
        return None
