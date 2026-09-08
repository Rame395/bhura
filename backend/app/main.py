import os
import sys
from contextlib import asynccontextmanager, contextmanager

from dotenv import load_dotenv
# Load backend/.env before importing config/database — those modules read os.environ
# at import time, so this must happen first or every .env setting is silently ignored.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import models, config
from .database import engine, SessionLocal
from .seed import seed_if_empty, ensure_unisex_category, ensure_default_departments
from .routers import products, cart, orders, admin

FRONTEND_DIR = os.path.join(os.path.dirname(config.BASE_DIR), "frontend")

# fcntl is Unix-only (Linux/macOS) — not available on Windows. The lock only matters
# when running multiple worker processes (`uvicorn --workers N`); on Windows, or any
# platform without fcntl, we fall back to no locking at all, which is exactly correct
# for the default single-process run and just means multi-worker startup on Windows
# would need its own coordination (e.g. seed the DB once before starting workers).
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


@contextmanager
def _startup_lock():
    if not HAS_FCNTL:
        yield
        return
    lock_path = os.path.join(config.BASE_DIR, ".startup.lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Guards schema creation + seeding with a cross-process file lock on platforms
    # that support it. Needed because `uvicorn --workers N` starts N processes that
    # each run this lifespan concurrently; without the lock, two workers can both see
    # "table doesn't exist yet" and race to CREATE TABLE, crashing every worker but
    # the first. Under a single process (the default `uvicorn app.main:app`) this is
    # uncontended and adds no real delay.
    with _startup_lock():
        models.Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_if_empty(db)
            ensure_unisex_category(db)
            ensure_default_departments(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BHURA API", lifespan=lifespan)

# Allows the API to be called from a separate local dev server (e.g. VS Code's Live
# Server on :5500) instead of only from this same FastAPI process. Harmless in
# production since it's restricted to these specific local origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000", "http://localhost:8000",
        "http://127.0.0.1:5500", "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "BHURA API"}

os.makedirs(config.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")

# Serves the whole static frontend (index.html, men.html, cart.html, admin/, ...).
# Mounted last so it never shadows the /api/* and /media/* routes above.
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
