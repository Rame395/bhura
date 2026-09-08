import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models, config
from .database import get_db


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_session(db: Session, admin_id: int) -> str:
    token = secrets.token_hex(32)
    expires = datetime.now(timezone.utc) + timedelta(days=config.SESSION_TTL_DAYS)
    db.add(models.AdminSession(token=token, admin_id=admin_id, expires_at=expires))
    db.commit()
    return token


def destroy_session(db: Session, token: str) -> None:
    db.query(models.AdminSession).filter(models.AdminSession.token == token).delete()
    db.commit()


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> models.AdminUser:
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = db.query(models.AdminSession).filter(models.AdminSession.token == token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    admin = db.query(models.AdminUser).filter(models.AdminUser.id == session.admin_id).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return admin
