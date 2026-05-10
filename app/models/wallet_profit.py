class WalletProfit:
    WALLET_CHANNELS = ("easypaisa", "jazzcash")
    LOAD_CHANNELS = ("zong", "jazz", "ufone", "telenor")
    VALID_CHANNELS = WALLET_CHANNELS + LOAD_CHANNELS
    LOAD_RATES = {
        "zong": 24.0,
        "jazz": 26.0,
        "ufone": 20.0,
        "telenor": 20.0,
    }
    DISPLAY_NAMES = {
        "easypaisa": "Easypaisa",
        "jazzcash": "JazzCash",
        "zong": "Zong",
        "jazz": "Jazz/Warid",
        "ufone": "Ufone",
        "telenor": "Telenor",
    }

    @staticmethod
    def create_table(db):
        existing_sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'wallet_profits';"
        ).fetchone()
        table_sql = (existing_sql["sql"] if existing_sql else "") or ""
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(wallet_profits);").fetchall()
        } if existing_sql else set()
        needs_rebuild = (
            "CHECK(channel IN ('easypaisa', 'jazzcash'))" in table_sql
            or "source_amount" not in columns
            or "rate_per_1000" not in columns
            or "credited_amount" not in columns
        )

        if needs_rebuild and existing_sql:
            db.execute("ALTER TABLE wallet_profits RENAME TO wallet_profits_legacy;")
            db.execute(
                """
                CREATE TABLE wallet_profits (
                  id            INTEGER PRIMARY KEY AUTOINCREMENT,
                  shop_id       INTEGER NOT NULL,
                  channel       TEXT NOT NULL,
                  amount        REAL NOT NULL CHECK(amount > 0),
                  source_amount REAL,
                  rate_per_1000 REAL,
                  credited_amount REAL,
                  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                  FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
                );
                """
            )
            legacy_columns = {
                row["name"]
                for row in db.execute("PRAGMA table_info(wallet_profits_legacy);").fetchall()
            }
            source_amount_expr = "source_amount" if "source_amount" in legacy_columns else "NULL"
            rate_expr = "rate_per_1000" if "rate_per_1000" in legacy_columns else "NULL"
            credited_expr = (
                "credited_amount"
                if "credited_amount" in legacy_columns
                else "CASE WHEN source_amount IS NOT NULL THEN source_amount + amount ELSE amount END"
            )
            db.execute(
                f"""
                INSERT INTO wallet_profits (id, shop_id, channel, amount, source_amount, rate_per_1000, credited_amount, created_at)
                SELECT id, shop_id, channel, amount, {source_amount_expr}, {rate_expr}, {credited_expr}, created_at
                FROM wallet_profits_legacy;
                """
            )
            db.execute("DROP TABLE wallet_profits_legacy;")
        else:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS wallet_profits (
                  id            INTEGER PRIMARY KEY AUTOINCREMENT,
                  shop_id       INTEGER NOT NULL,
                  channel       TEXT NOT NULL,
                  amount        REAL NOT NULL CHECK(amount > 0),
                  source_amount REAL,
                  rate_per_1000 REAL,
                  credited_amount REAL,
                  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                  FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
                );
                """
            )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_wallet_profits_shop_channel_created
              ON wallet_profits (shop_id, channel, created_at DESC);
            """
        )

    @staticmethod
    def add_entry(
        db,
        shop_id: int,
        channel: str,
        amount: float,
        source_amount: float | None = None,
        rate_per_1000: float | None = None,
        credited_amount: float | None = None,
    ):
        if channel not in WalletProfit.VALID_CHANNELS:
            raise ValueError("Invalid wallet channel.")
        db.execute(
            """
            INSERT INTO wallet_profits (shop_id, channel, amount, source_amount, rate_per_1000, credited_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'));
            """,
            (shop_id, channel, amount, source_amount, rate_per_1000, credited_amount),
        )

    @staticmethod
    def calculate_load_profit(channel: str, source_amount: float):
        if channel not in WalletProfit.LOAD_RATES:
            raise ValueError("Invalid load channel.")
        return round((source_amount / 1000.0) * WalletProfit.LOAD_RATES[channel], 2)

    @staticmethod
    def calculate_load_credited_amount(channel: str, source_amount: float):
        profit_amount = WalletProfit.calculate_load_profit(channel, source_amount)
        return round(source_amount + profit_amount, 2)

    @staticmethod
    def totals_by_channel(db, shop_id: int):
        rows = db.execute(
            """
            SELECT
              channel,
              COALESCE(SUM(amount), 0) AS profit_total,
              COALESCE(SUM(amount), 0) AS system_cash_total,
              COALESCE(SUM(CASE
                WHEN channel IN ('zong', 'jazz', 'ufone', 'telenor') THEN COALESCE(credited_amount, COALESCE(source_amount, 0) + amount)
                ELSE amount
              END), 0) AS credited_total
            FROM wallet_profits
            WHERE shop_id = ?
            GROUP BY channel;
            """,
            (shop_id,),
        ).fetchall()
        totals = {
            channel: {"profit_total": 0.0, "system_cash_total": 0.0, "credited_total": 0.0}
            for channel in WalletProfit.VALID_CHANNELS
        }
        for row in rows:
            totals[row["channel"]] = {
                "profit_total": float(row["profit_total"] or 0),
                "system_cash_total": float(row["system_cash_total"] or 0),
                "credited_total": float(row["credited_total"] or 0),
            }
        totals["system_cash"] = sum(item["system_cash_total"] for item in totals.values())
        return totals

    @staticmethod
    def daily_history_with_entries(db, shop_id: int, channel: str):
        if channel not in WalletProfit.VALID_CHANNELS:
            return []
        rows = db.execute(
            """
            SELECT
              id,
              amount,
              source_amount,
              rate_per_1000,
              credited_amount,
              created_at,
              date(datetime(created_at, 'localtime')) AS local_day
            FROM wallet_profits
            WHERE shop_id = ? AND channel = ?
            ORDER BY created_at DESC, id DESC;
            """,
            (shop_id, channel),
        ).fetchall()

        grouped = {}
        ordered_days = []
        for row in rows:
            created_at = row["created_at"] or ""
            day = row["local_day"] or (created_at[:10] if len(created_at) >= 10 else created_at)
            if day not in grouped:
                grouped[day] = {
                    "day": day,
                    "day_total": 0.0,
                    "day_profit_total": 0.0,
                    "day_credited_total": 0.0,
                    "entries": [],
                }
                ordered_days.append(day)
            amount = float(row["amount"] or 0)
            credited_amount = float(row["credited_amount"] or 0) if row["credited_amount"] is not None else amount
            grouped[day]["day_total"] += amount
            grouped[day]["day_profit_total"] += amount
            grouped[day]["day_credited_total"] += credited_amount
            grouped[day]["entries"].append(
                {
                    "id": row["id"],
                    "amount": amount,
                    "source_amount": float(row["source_amount"] or 0) if row["source_amount"] is not None else None,
                    "rate_per_1000": float(row["rate_per_1000"] or 0) if row["rate_per_1000"] is not None else None,
                    "credited_amount": credited_amount,
                    "created_at": created_at,
                }
            )

        return [grouped[day] for day in ordered_days]
