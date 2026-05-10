class StockBatch:
    @staticmethod
    def _column_names(db, table_name: str):
        return {
            row["name"]
            for row in db.execute(f"PRAGMA table_info({table_name});").fetchall()
        }

    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS stock_batches (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id        INTEGER NOT NULL,
          product_id     INTEGER NOT NULL,
          quantity       INTEGER NOT NULL CHECK(quantity > 0),
          purchase_rate  REAL NOT NULL CHECK(purchase_rate >= 0),
          sale_price     REAL NOT NULL CHECK(sale_price >= 0),
          batch_date     TEXT NOT NULL,
          created_at     TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id)    REFERENCES shops(id) ON DELETE CASCADE,
          FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)

        columns = StockBatch._column_names(db, "stock_batches")
        if "purchase_rate" not in columns:
            db.execute("ALTER TABLE stock_batches ADD COLUMN purchase_rate REAL NOT NULL DEFAULT 0;")
        if "batch_date" not in columns:
            db.execute("ALTER TABLE stock_batches ADD COLUMN batch_date TEXT NOT NULL DEFAULT date('now');")
        if "sale_price" not in columns:
            db.execute("ALTER TABLE stock_batches ADD COLUMN sale_price REAL NOT NULL DEFAULT 0;")

    @staticmethod
    def create(db, shop_id: int, product_id: int, quantity: int, purchase_rate: float, sale_price: float, batch_date: str):
        db.execute(
            """
            INSERT INTO stock_batches (shop_id, product_id, quantity, purchase_rate, sale_price, batch_date)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (shop_id, product_id, quantity, purchase_rate, sale_price, batch_date),
        )

    @staticmethod
    def all_by_shop(db, shop_id: int):
        return db.execute(
            """
            SELECT sb.*, p.name AS product_name
            FROM stock_batches sb
            JOIN products p ON p.id = sb.product_id
            WHERE sb.shop_id = ?
            ORDER BY sb.batch_date DESC, sb.created_at DESC;
            """,
            (shop_id,),
        ).fetchall()

    @staticmethod
    def by_date(db, shop_id: int, batch_date: str):
        return db.execute(
            """
            SELECT sb.*, p.name AS product_name
            FROM stock_batches sb
            JOIN products p ON p.id = sb.product_id
            WHERE sb.shop_id = ? AND sb.batch_date = ?
            ORDER BY sb.created_at DESC;
            """,
            (shop_id, batch_date),
        ).fetchall()

    @staticmethod
    def by_product(db, shop_id: int, product_id: int):
        return db.execute(
            """
            SELECT sb.*, p.name AS product_name
            FROM stock_batches sb
            JOIN products p ON p.id = sb.product_id
            WHERE sb.shop_id = ? AND sb.product_id = ?
            ORDER BY sb.batch_date DESC, sb.created_at DESC;
            """,
            (shop_id, product_id),
        ).fetchall()

    @staticmethod
    def latest_for_product(db, shop_id: int, product_id: int):
        return db.execute(
            """
            SELECT sb.*
            FROM stock_batches sb
            WHERE sb.shop_id = ? AND sb.product_id = ?
            ORDER BY sb.batch_date DESC, sb.created_at DESC
            LIMIT 1;
            """,
            (shop_id, product_id),
        ).fetchone()

    @staticmethod
    def average_purchase_rate(db, shop_id: int, product_id: int):
        row = db.execute(
            """
            SELECT
              COALESCE(SUM(quantity * purchase_rate), 0) AS total_cost,
              COALESCE(SUM(quantity), 0) AS total_quantity
            FROM stock_batches
            WHERE shop_id = ? AND product_id = ?;
            """,
            (shop_id, product_id),
        ).fetchone()
        total_quantity = float(row["total_quantity"] or 0)
        if total_quantity <= 0:
            return 0.0
        total_cost = float(row["total_cost"] or 0)
        return round(total_cost / total_quantity, 4)
