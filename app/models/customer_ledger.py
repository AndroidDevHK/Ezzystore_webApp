import sqlite3

class CustomerLedger:
    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS customer_ledgers (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id        INTEGER NOT NULL,
          customer_id    INTEGER NOT NULL,
          sale_id        INTEGER,
          amount_due     REAL NOT NULL DEFAULT 0 CHECK(amount_due >= 0),
          amount_paid    REAL NOT NULL DEFAULT 0 CHECK(amount_paid >= 0),
          note           TEXT,
          created_at     TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
          FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
          FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL
        );
        """)

    @staticmethod
    def record_pending_amount(db, shop_id: int, customer_id: int, sale_id: int, amount_due: float):
        if amount_due <= 0:
            return
        db.execute("""
            INSERT INTO customer_ledgers (shop_id, customer_id, sale_id, amount_due, note)
            VALUES (?, ?, ?, ?, 'Pending from Sale');
        """, (shop_id, customer_id, sale_id, float(amount_due)))

    @staticmethod
    def record_payment(db, shop_id: int, customer_id: int, amount_paid: float, note: str = "Payment Received"):
        if amount_paid <= 0:
            return
        db.execute("""
            INSERT INTO customer_ledgers (shop_id, customer_id, sale_id, amount_paid, note)
            VALUES (?, ?, NULL, ?, ?);
        """, (shop_id, customer_id, float(amount_paid), note.strip()))

    @staticmethod
    def get_balance(db, shop_id: int, customer_id: int):
        row = db.execute("""
            SELECT SUM(amount_due) - SUM(amount_paid) AS balance
            FROM customer_ledgers
            WHERE shop_id = ? AND customer_id = ?;
        """, (shop_id, customer_id)).fetchone()
        return float(row["balance"] or 0.0)

    @staticmethod
    def get_history(db, shop_id: int, customer_id: int):
        rows = db.execute("""
            SELECT cl.*, s.total_amount AS sale_total_amount
            FROM customer_ledgers cl
            LEFT JOIN sales s ON s.id = cl.sale_id
            WHERE cl.shop_id = ? AND cl.customer_id = ?
            ORDER BY cl.created_at DESC;
        """, (shop_id, customer_id)).fetchall()
        
        history = []
        for row in rows:
            record = dict(row)
            # If this is tied to a sale, get the items
            sale_items = []
            if record["sale_id"]:
                items = db.execute("""
                    SELECT si.quantity, p.name
                    FROM sale_items si
                    JOIN products p ON p.id = si.product_id
                    WHERE si.sale_id = ?
                """, (record["sale_id"],)).fetchall()
                sale_items = [{"quantity": i["quantity"], "name": i["name"]} for i in items]
            
            record["sale_items"] = sale_items
            history.append(record)
        return history
