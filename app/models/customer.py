class Customer:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS customers (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id    INTEGER NOT NULL,
          name       TEXT NOT NULL,
          phone      TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
          UNIQUE (shop_id, name)
        );
        """)

    @staticmethod
    def all_by_shop(db, shop_id: int):
        return db.execute("""
            SELECT *
            FROM customers
            WHERE shop_id = ?
            ORDER BY name COLLATE NOCASE ASC;
        """, (shop_id,)).fetchall()

    @staticmethod
    def get_for_shop(db, shop_id: int, customer_id: int):
        return db.execute("""
            SELECT *
            FROM customers
            WHERE id = ? AND shop_id = ?
            LIMIT 1;
        """, (customer_id, shop_id)).fetchone()

    @staticmethod
    def get_by_name(db, shop_id: int, name: str):
        return db.execute("""
            SELECT *
            FROM customers
            WHERE shop_id = ? AND name = ?
            LIMIT 1;
        """, (shop_id, name.strip())).fetchone()

    @staticmethod
    def create(db, shop_id: int, name: str, phone: str | None = None):
        cursor = db.execute("""
            INSERT INTO customers (shop_id, name, phone)
            VALUES (?, ?, ?);
        """, (shop_id, name.strip(), phone.strip() if phone else None))
        return cursor.lastrowid

    @staticmethod
    def delete(db, shop_id: int, customer_id: int):
        db.execute("""
            DELETE FROM customers
            WHERE id = ? AND shop_id = ?;
        """, (customer_id, shop_id))
