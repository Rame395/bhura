import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

# --- Store / brand settings that aren't editable from the admin UI ---
WHATSAPP_DEFAULT = os.environ.get("BHURA_WHATSAPP_NUMBER", "9779768785693")
SESSION_COOKIE_NAME = "bhura_admin_session"
CART_COOKIE_NAME = "bhura_cart"
SESSION_TTL_DAYS = 7

# --- Default admin account (only used the first time the DB is seeded) ---
DEFAULT_ADMIN_USERNAME = os.environ.get("BHURA_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("BHURA_ADMIN_PASSWORD", "bhura-admin-2026")

# --- SMTP (optional; order emails are skipped gracefully if unset) ---
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "orders@bhura.example")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "BHURA")

