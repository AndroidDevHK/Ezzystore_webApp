class Shop:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS shops (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          name        TEXT NOT NULL UNIQUE,
          created_by  INTEGER NOT NULL,
          created_at  TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

    @staticmethod
    def create(db, name: str, created_by: int):
        db.execute(
            "INSERT INTO shops (name, created_by) VALUES (?, ?);",
            (name.strip(), created_by)
        )

    @staticmethod
    def all(db):
        return db.execute("SELECT * FROM shops ORDER BY id DESC;").fetchall()
