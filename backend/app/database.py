import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# .as_posix() always gives forward slashes, even on Windows — plain os.path.join()
# gives backslashes there (e.g. C:\Users\...), which breaks the sqlite:/// URI format.
_default_db_path = (Path(BASE_DIR) / "bhura.db").as_posix()
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{_default_db_path}"

# NOTE: DATABASE_URL can be swapped for a PostgreSQL URL, e.g.
#   postgresql://user:password@localhost:5432/bhura
# with zero code changes elsewhere, since all queries go through SQLAlchemy's ORM.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
