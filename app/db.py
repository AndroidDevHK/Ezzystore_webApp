import os
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_path = current_app.config["DB_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")

        g.db = conn
    return g.db


def close_db(_e=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
