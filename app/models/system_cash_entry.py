class SystemCashEntry:
    VALID_ENTRY_TYPES = ("add", "expense")
    VALID_CASH_BUCKETS = ("counter", "online")

    @staticmethod
    def _column_names(db, table_name: str):
        return {
            row["name"]
            for row in db.execute(f"PRAGMA table_info({table_name});").fetchall()
        }

    @staticmethod
    def create_table(db):
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS system_cash_entries (
              id         INTEGER PRIMARY KEY AUTOINCREMENT,
              shop_id    INTEGER NOT NULL,
              amount     REAL NOT NULL CHECK(amount > 0),
              entry_type TEXT NOT NULL DEFAULT 'add' CHECK(entry_type IN ('add', 'expense')),
              cash_bucket TEXT NOT NULL DEFAULT 'counter' CHECK(cash_bucket IN ('counter', 'online')),
              expense_name TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
            );
            """
        )
        columns = SystemCashEntry._column_names(db, "system_cash_entries")
        if "entry_type" not in columns:
            db.execute(
                "ALTER TABLE system_cash_entries ADD COLUMN entry_type TEXT NOT NULL DEFAULT 'add' CHECK(entry_type IN ('add', 'expense'));"
            )
        if "cash_bucket" not in columns:
            db.execute(
                "ALTER TABLE system_cash_entries ADD COLUMN cash_bucket TEXT NOT NULL DEFAULT 'counter' CHECK(cash_bucket IN ('counter', 'online'));"
            )
        if "expense_name" not in columns:
            db.execute("ALTER TABLE system_cash_entries ADD COLUMN expense_name TEXT;")
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_system_cash_entries_shop_created
              ON system_cash_entries (shop_id, created_at DESC);
            """
        )

    @staticmethod
    def add_entry(db, shop_id: int, amount: float, entry_type: str = "add", expense_name: str | None = None, cash_bucket: str = "counter"):
        if entry_type not in SystemCashEntry.VALID_ENTRY_TYPES:
            raise ValueError("Invalid system cash entry type.")
        if cash_bucket not in SystemCashEntry.VALID_CASH_BUCKETS:
            raise ValueError("Invalid cash bucket.")
        clean_expense_name = (expense_name or "").strip()
        if not clean_expense_name:
            raise ValueError("Message is required.")
        db.execute(
            """
            INSERT INTO system_cash_entries (shop_id, amount, entry_type, cash_bucket, expense_name, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'));
            """,
            (shop_id, amount, entry_type, cash_bucket, clean_expense_name),
        )

    @staticmethod
    def total_for_shop(db, shop_id: int, cash_bucket: str | None = None):
        params = [shop_id]
        bucket_filter = ""
        if cash_bucket:
            bucket_filter = " AND cash_bucket = ?"
            params.append(cash_bucket)
        row = db.execute(
            f"""
            SELECT COALESCE(SUM(
              CASE
                WHEN entry_type = 'expense' THEN -amount
                ELSE amount
              END
            ), 0) AS total
            FROM system_cash_entries
            WHERE shop_id = ?{bucket_filter};
            """,
            tuple(params),
        ).fetchone()
        return float(row["total"] or 0)

    @staticmethod
    def totals_by_bucket(db, shop_id: int):
        rows = db.execute(
            """
            SELECT
              cash_bucket,
              COALESCE(SUM(CASE WHEN entry_type = 'expense' THEN -amount ELSE amount END), 0) AS total
            FROM system_cash_entries
            WHERE shop_id = ?
            GROUP BY cash_bucket;
            """,
            (shop_id,),
        ).fetchall()
        totals = {bucket: 0.0 for bucket in SystemCashEntry.VALID_CASH_BUCKETS}
        for row in rows:
            totals[row["cash_bucket"] or "counter"] = float(row["total"] or 0)
        return totals

    @staticmethod
    def daily_history_with_entries(db, shop_id: int):
        rows = db.execute(
            """
            SELECT
              id,
              amount,
              entry_type,
              cash_bucket,
              expense_name,
              created_at,
              date(datetime(created_at, 'localtime')) AS local_day
            FROM system_cash_entries
            WHERE shop_id = ?
            ORDER BY created_at DESC, id DESC;
            """,
            (shop_id,),
        ).fetchall()

        grouped = {}
        ordered_days = []
        for row in rows:
            created_at = row["created_at"] or ""
            day = row["local_day"] or (created_at[:10] if len(created_at) >= 10 else created_at)
            if day not in grouped:
                grouped[day] = {"day": day, "day_total": 0.0, "entries": []}
                ordered_days.append(day)
            amount = float(row["amount"] or 0)
            signed_amount = -amount if row["entry_type"] == "expense" else amount
            grouped[day]["day_total"] += signed_amount
            grouped[day]["entries"].append(
                {
                    "id": row["id"],
                    "amount": amount,
                    "signed_amount": signed_amount,
                    "entry_type": row["entry_type"] or "add",
                    "cash_bucket": row["cash_bucket"] or "counter",
                    "expense_name": row["expense_name"] or "",
                    "created_at": created_at,
                }
            )

        return [grouped[day] for day in ordered_days]
