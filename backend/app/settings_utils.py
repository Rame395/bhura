from sqlalchemy.orm import Session

from . import models


def get_setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(models.SiteSetting).filter(models.SiteSetting.key == key).first()
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(models.SiteSetting).filter(models.SiteSetting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(models.SiteSetting(key=key, value=value))
