import os
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          role           TEXT NOT NULL CHECK(role IN ('admin','manager')),
          full_name      TEXT NOT NULL,
          username       TEXT NOT NULL UNIQUE,
          password_hash  TEXT NOT NULL,
          is_active      INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
          created_at     TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        # Enforce only one admin user (partial unique index)
        db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_single_admin
        ON users(role)
        WHERE role = 'admin';
        """)

    @staticmethod
    def ensure_default_admin(db):
        row = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1;").fetchone()
        if row is None:
            username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
            password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
            full_name = os.environ.get("INITIAL_ADMIN_FULL_NAME", "System Admin").strip() or "System Admin"
            if not username or not password:
                return
            db.execute("""
                INSERT INTO users (role, full_name, username, password_hash)
                VALUES ('admin', ?, ?, ?);
            """, (full_name, username, generate_password_hash(password)))

    @staticmethod
    def authenticate(db, username: str, password: str):
        user = db.execute("""
            SELECT * FROM users
            WHERE username=? AND is_active=1
            LIMIT 1;
        """, (username.strip(),)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            return user
        return None

    @staticmethod
    def create_manager(db, full_name: str, username: str, password: str) -> int:
        db.execute("""
            INSERT INTO users (role, full_name, username, password_hash)
            VALUES ('manager', ?, ?, ?);
        """, (full_name.strip(), username.strip(), generate_password_hash(password)))

        return db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
