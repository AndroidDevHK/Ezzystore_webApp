class ServiceTransaction:
    PROFIT_TO_COUNTER_MARKER = "[counter_transfer]"
    WALLET_CHANNELS = ("easypaisa", "jazzcash")
    EASYLOAD_CHANNELS = ("zong", "jazz", "ufone", "telenor")
    VALID_CHANNELS = WALLET_CHANNELS + EASYLOAD_CHANNELS
    WALLET_PROFIT_RATE_PER_1000 = {
        "easypaisa": 10.0,
        "jazzcash": 10.0,
    }

    ENTRY_TYPES = ("cash_in", "cash_out", "profit_in", "purchase_in", "out", "adjust_in", "adjust_out")
    BALANCE_IN_TYPES = ("cash_in", "profit_in", "purchase_in", "adjust_in")
    BALANCE_OUT_TYPES = ("cash_out", "out", "adjust_out")

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

    ENTRY_LABELS = {
        "cash_in": "Cash In",
        "cash_out": "Cash Out",
        "profit_in": "Profit In",
        "purchase_in": "Purchase In",
        "out": "Out",
        "adjust_in": "Adjustment In",
        "adjust_out": "Adjustment Out",
    }

    @staticmethod
    def build_profit_note(note: str | None = None, destination: str = "wallet"):
        clean_note = (note or "").strip()
        if destination == "counter":
            return f"{ServiceTransaction.PROFIT_TO_COUNTER_MARKER} {clean_note}".strip()
        return clean_note

    @staticmethod
    def is_profit_to_counter(note: str | None):
        return (note or "").strip().startswith(ServiceTransaction.PROFIT_TO_COUNTER_MARKER)

    @staticmethod
    def display_note(note: str | None):
        clean_note = (note or "").strip()
        if ServiceTransaction.is_profit_to_counter(clean_note):
            clean_note = clean_note[len(ServiceTransaction.PROFIT_TO_COUNTER_MARKER):].strip()
        return clean_note

    @staticmethod
    def create_table(db):
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS service_transactions (
              id            INTEGER PRIMARY KEY AUTOINCREMENT,
              shop_id       INTEGER NOT NULL,
              channel       TEXT NOT NULL,
              entry_type    TEXT NOT NULL,
              amount        REAL NOT NULL CHECK(amount > 0),
              profit_amount REAL NOT NULL DEFAULT 0,
              note          TEXT,
              created_at    TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
            );
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_service_transactions_shop_channel_created
              ON service_transactions (shop_id, channel, created_at DESC);
            """
        )

    @staticmethod
    def effective_amount(entry_type: str, amount: float, profit_amount: float = 0.0):
        if entry_type == "purchase_in":
            return round(float(amount or 0) + float(profit_amount or 0), 2)
        return float(amount or 0)

    @staticmethod
    def calculate_easyload_profit(channel: str, amount: float):
        if channel not in ServiceTransaction.EASYLOAD_CHANNELS:
            return 0.0
        return round((amount / 1000.0) * ServiceTransaction.LOAD_RATES[channel], 2)

    @staticmethod
    def calculate_wallet_profit(channel: str, amount: float):
        if channel not in ServiceTransaction.WALLET_CHANNELS:
            return 0.0
        rate = ServiceTransaction.WALLET_PROFIT_RATE_PER_1000.get(channel, 0.0)
        return round((amount / 1000.0) * rate, 2)

    @staticmethod
    def add_entry(
        db,
        shop_id: int,
        channel: str,
        entry_type: str,
        amount: float,
        note: str | None = None,
    ):
        if channel not in ServiceTransaction.VALID_CHANNELS:
            raise ValueError("Invalid service channel.")
        if entry_type not in ServiceTransaction.ENTRY_TYPES:
            raise ValueError("Invalid entry type.")
        is_wallet = channel in ServiceTransaction.WALLET_CHANNELS
        if is_wallet and entry_type not in ("cash_in", "cash_out", "profit_in", "adjust_in", "adjust_out"):
            raise ValueError("Invalid wallet entry type.")
        if not is_wallet and entry_type not in ("purchase_in", "out", "adjust_in", "adjust_out"):
            raise ValueError("Invalid easyload entry type.")

        profit_amount = 0.0
        if channel in ServiceTransaction.EASYLOAD_CHANNELS and entry_type == "purchase_in":
            profit_amount = ServiceTransaction.calculate_easyload_profit(channel, amount)

        db.execute(
            """
            INSERT INTO service_transactions (shop_id, channel, entry_type, amount, profit_amount, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'));
            """,
            (shop_id, channel, entry_type, amount, profit_amount, (note or "").strip()),
        )

    @staticmethod
    def totals_by_channel(db, shop_id: int):
        rows = db.execute(
            """
            SELECT
              channel,
              COALESCE(SUM(CASE
                WHEN entry_type = 'purchase_in' THEN amount + profit_amount
                WHEN entry_type = 'cash_in' THEN amount
                WHEN entry_type = 'adjust_in' THEN amount
                WHEN entry_type = 'profit_in' AND note NOT LIKE '[counter_transfer]%' THEN amount
                ELSE 0
              END), 0) AS in_total,
              COALESCE(SUM(CASE WHEN entry_type IN ('cash_out', 'out', 'adjust_out') THEN amount ELSE 0 END), 0) AS out_total,
              COALESCE(SUM(CASE
                WHEN entry_type = 'purchase_in' THEN amount + profit_amount
                WHEN entry_type = 'cash_in' THEN amount
                WHEN entry_type = 'adjust_in' THEN amount
                WHEN entry_type = 'profit_in' AND note NOT LIKE '[counter_transfer]%' THEN amount
                WHEN entry_type IN ('cash_out', 'out', 'adjust_out') THEN -amount
                ELSE 0
              END), 0) AS balance_total,
              COALESCE(SUM(CASE
                WHEN entry_type = 'cash_in' THEN amount
                WHEN entry_type = 'cash_out' THEN -amount
                ELSE 0
              END), 0) AS cash_balance_total,
              COALESCE(SUM(CASE
                WHEN entry_type = 'profit_in' AND note NOT LIKE '[counter_transfer]%' THEN amount
                ELSE 0
              END), 0) AS profit_balance_total,
              COALESCE(SUM(CASE
                WHEN entry_type = 'profit_in' AND note LIKE '[counter_transfer]%' THEN amount
                ELSE 0
              END), 0) AS profit_to_counter_total,
              COALESCE(SUM(profit_amount), 0) AS profit_total
            FROM service_transactions
            WHERE shop_id = ?
            GROUP BY channel;
            """,
            (shop_id,),
        ).fetchall()

        totals = {
            channel: {
                "in_total": 0.0,
                "out_total": 0.0,
                "balance_total": 0.0,
                "cash_balance_total": 0.0,
                "profit_balance_total": 0.0,
                "profit_to_counter_total": 0.0,
                "profit_total": 0.0,
            }
            for channel in ServiceTransaction.VALID_CHANNELS
        }
        for row in rows:
            totals[row["channel"]] = {
                "in_total": float(row["in_total"] or 0),
                "out_total": float(row["out_total"] or 0),
                "balance_total": float(row["balance_total"] or 0),
                "cash_balance_total": float(row["cash_balance_total"] or 0),
                "profit_balance_total": float(row["profit_balance_total"] or 0),
                "profit_to_counter_total": float(row["profit_to_counter_total"] or 0),
                "profit_total": float(row["profit_total"] or 0),
            }
        return totals

    @staticmethod
    def current_balance(db, shop_id: int, channel: str):
        row = db.execute(
            """
            SELECT COALESCE(SUM(CASE
              WHEN entry_type = 'purchase_in' THEN amount + profit_amount
              WHEN entry_type = 'cash_in' THEN amount
              WHEN entry_type = 'adjust_in' THEN amount
              WHEN entry_type = 'profit_in' AND note NOT LIKE '[counter_transfer]%' THEN amount
              WHEN entry_type IN ('cash_out', 'out', 'adjust_out') THEN -amount
              ELSE 0
            END), 0) AS balance_total
            FROM service_transactions
            WHERE shop_id = ? AND channel = ?;
            """,
            (shop_id, channel),
        ).fetchone()
        return float(row["balance_total"] or 0)

    @staticmethod
    def daily_history_with_entries(db, shop_id: int, channel: str):
        if channel not in ServiceTransaction.VALID_CHANNELS:
            return []
        rows = db.execute(
            """
            SELECT
              id,
              entry_type,
              amount,
              profit_amount,
              note,
              created_at,
              date(datetime(created_at, 'localtime')) AS local_day
            FROM service_transactions
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
                    "day_in_total": 0.0,
                    "day_out_total": 0.0,
                    "day_net_total": 0.0,
                    "day_profit_total": 0.0,
                    "entries": [],
                }
                ordered_days.append(day)

            amount = float(row["amount"] or 0)
            profit_amount = float(row["profit_amount"] or 0)
            entry_type = row["entry_type"] or ""
            note = row["note"] or ""
            profit_to_counter = ServiceTransaction.is_profit_to_counter(note)
            effective_amount = ServiceTransaction.effective_amount(entry_type, amount, profit_amount)
            if entry_type == "profit_in" and profit_to_counter:
                signed_amount = 0.0
                entry_label = "Profit to Counter"
            else:
                signed_amount = effective_amount if entry_type in ServiceTransaction.BALANCE_IN_TYPES else -amount
                entry_label = ServiceTransaction.ENTRY_LABELS.get(entry_type, entry_type.title())
            if entry_type in ServiceTransaction.BALANCE_IN_TYPES and not profit_to_counter:
                grouped[day]["day_in_total"] += effective_amount
            else:
                if entry_type in ServiceTransaction.BALANCE_OUT_TYPES:
                    grouped[day]["day_out_total"] += amount
            grouped[day]["day_net_total"] += signed_amount
            grouped[day]["day_profit_total"] += profit_amount
            grouped[day]["entries"].append(
                {
                    "id": row["id"],
                    "entry_type": entry_type,
                    "entry_label": entry_label,
                    "amount": amount,
                    "effective_amount": effective_amount,
                    "signed_amount": signed_amount,
                    "profit_amount": profit_amount,
                    "note": ServiceTransaction.display_note(note),
                    "is_profit_to_counter": profit_to_counter,
                    "created_at": created_at,
                }
            )

        return [grouped[day] for day in ordered_days]
