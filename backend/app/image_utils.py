"""Shared helpers for storing/serving uploaded photos as rows in the database
rather than files on disk — the single source of truth for every image the
site uses, so nothing can fall out of sync between the database and a
separate media folder. Used by every upload endpoint across admin.py and
orders.py (kept here, not in either router, to avoid a circular import
between them)."""

from sqlalchemy.orm import Session

from . import models


def save_image_to_db(db: Session, content: bytes, content_type: str | None) -> str:
    """Store uploaded photo bytes directly in the database and return the URL
    that serves them back."""
    image = models.Image(data=content, content_type=content_type or "image/jpeg")
    db.add(image)
    db.flush()  # assigns image.id without committing the caller's transaction yet
    return f"/api/media/image/{image.id}"


def delete_image_by_url(db: Session, url: str | None) -> None:
    """If this URL points to a DB-stored image, remove that row too."""
    if not url or "/api/media/image/" not in url:
        return
    try:
        image_id = int(url.rsplit("/", 1)[-1])
    except ValueError:
        return
    db.query(models.Image).filter(models.Image.id == image_id).delete()
