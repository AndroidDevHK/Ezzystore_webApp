class BaseModel:
    table_name = ""

    @classmethod
    def create_table(cls, db):
        db.execute(f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id    INTEGER NOT NULL,
          name       TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
          UNIQUE(shop_id, name)
        );
        """)

    @classmethod
    def create(cls, db, shop_id: int, name: str):
        db.execute(f"""
            INSERT INTO {cls.table_name} (shop_id, name)
            VALUES (?, ?);
        """, (shop_id, name.strip()))

    @classmethod
    def update(cls, db, shop_id: int, record_id: int, name: str):
        db.execute(f"""
            UPDATE {cls.table_name}
            SET name=?
            WHERE id=? AND shop_id=?;
        """, (name.strip(), record_id, shop_id))

    @classmethod
    def all_by_shop(cls, db, shop_id: int):
        return db.execute(f"""
            SELECT *
            FROM {cls.table_name}
            WHERE shop_id=?
            ORDER BY name ASC;
        """, (shop_id,)).fetchall()

    @classmethod
    def get_by_id(cls, db, shop_id: int, record_id: int):
        return db.execute(f"""
            SELECT *
            FROM {cls.table_name}
            WHERE id=? AND shop_id=?
            LIMIT 1;
        """, (record_id, shop_id)).fetchone()
