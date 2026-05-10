class Category:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id    INTEGER NOT NULL,
          name       TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
          UNIQUE(shop_id, name)
        );
        """)

    @staticmethod
    def create(db, shop_id: int, name: str):
        db.execute("""
            INSERT INTO categories (shop_id, name)
            VALUES (?, ?);
        """, (shop_id, name.strip()))

    @staticmethod
    def update(db, shop_id: int, category_id: int, name: str):
        db.execute("""
            UPDATE categories
            SET name=?
            WHERE id=? AND shop_id=?;
        """, (name.strip(), category_id, shop_id))

    @staticmethod
    def all_by_shop(db, shop_id: int):
        return db.execute("""
            SELECT *
            FROM categories
            WHERE shop_id=?
            ORDER BY name ASC;
        """, (shop_id,)).fetchall()

    @staticmethod
    def get_by_id(db, shop_id: int, category_id: int):
        return db.execute("""
            SELECT *
            FROM categories
            WHERE id=? AND shop_id=?
            LIMIT 1;
        """, (category_id, shop_id)).fetchone()
