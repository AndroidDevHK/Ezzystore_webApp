class ShopSettings:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS shop_settings (
          shop_id          INTEGER PRIMARY KEY,
          expense_percent  REAL NOT NULL DEFAULT 0,
          hide_sale_prices INTEGER NOT NULL DEFAULT 1,
          updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
        );
        """)
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(shop_settings);").fetchall()
        }
        if "hide_sale_prices" not in columns:
            db.execute(
                "ALTER TABLE shop_settings ADD COLUMN hide_sale_prices INTEGER NOT NULL DEFAULT 1;"
            )

    @staticmethod
    def get_for_shop(db, shop_id: int):
        row = db.execute(
            "SELECT shop_id, expense_percent, hide_sale_prices FROM shop_settings WHERE shop_id = ?;",
            (shop_id,),
        ).fetchone()
        return row

    @staticmethod
    def set_values(db, shop_id: int, expense_percent: float, hide_sale_prices: bool):
        db.execute(
            """
            INSERT INTO shop_settings (shop_id, expense_percent, hide_sale_prices, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(shop_id)
            DO UPDATE SET expense_percent = excluded.expense_percent,
                          hide_sale_prices = excluded.hide_sale_prices,
                          updated_at = datetime('now');
            """,
            (shop_id, expense_percent, 1 if hide_sale_prices else 0),
        )

    @staticmethod
    def set_expense_percent(db, shop_id: int, expense_percent: float):
        current = ShopSettings.get_for_shop(db, shop_id)
        hide_sale_prices = bool(current["hide_sale_prices"]) if current else True
        ShopSettings.set_values(db, shop_id, expense_percent, hide_sale_prices)
