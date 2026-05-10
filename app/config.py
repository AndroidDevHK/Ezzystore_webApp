import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    INITIAL_ADMIN_USERNAME = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
    INITIAL_ADMIN_PASSWORD = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
    INITIAL_ADMIN_FULL_NAME = os.environ.get("INITIAL_ADMIN_FULL_NAME", "System Admin").strip() or "System Admin"

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    # Database file name
    DB_PATH = os.path.join(INSTANCE_DIR, "ezzystore.db")
