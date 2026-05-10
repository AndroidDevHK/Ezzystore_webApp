class Brand:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS brands (
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
            INSERT INTO brands (shop_id, name)
            VALUES (?, ?);
        """, (shop_id, name.strip()))

    @staticmethod
    def update(db, shop_id: int, brand_id: int, name: str):
        db.execute("""
            UPDATE brands
            SET name=?
            WHERE id=? AND shop_id=?;
        """, (name.strip(), brand_id, shop_id))

    @staticmethod
    def all_by_shop(db, shop_id: int):
        return db.execute("""
            SELECT *
            FROM brands
            WHERE shop_id=?
            ORDER BY name ASC;
        """, (shop_id,)).fetchall()

    @staticmethod
    def get_by_id(db, shop_id: int, brand_id: int):
        return db.execute("""
            SELECT *
            FROM brands
            WHERE id=? AND shop_id=?
            LIMIT 1;
        """, (brand_id, shop_id)).fetchone()
