import sqlite3
from functools import wraps
from datetime import datetime, date, timedelta, timezone
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, current_app

from ..db import get_db
from ..models.product import Product
from ..models.brand import Brand
from ..models.category import Category
from ..models.stock_batch import StockBatch
from ..models.sale import Sale
from ..models.customer import Customer
from ..models.shop_settings import ShopSettings
from ..models.wallet_profit import WalletProfit
from ..models.system_cash_entry import SystemCashEntry
from ..models.service_transaction import ServiceTransaction
from ..time_utils import parse_utc_to_local

manager_bp = Blueprint("manager", __name__)
PACKAGE_PROFIT_MARKER = "[package_profit]"


def manager_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "manager":
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


def _get_manager_shop(db):
    return db.execute("""
        SELECT s.id, s.name, s.created_at
        FROM shops s
        JOIN shop_managers sm ON sm.shop_id = s.id
        WHERE sm.manager_user_id = ?
        LIMIT 1;
    """, (session.get("user_id"),)).fetchone()


def _url_for_page(page: str | None):
    mapping = {
        "overview": "manager.dashboard",
        "daily_report": "manager.daily_report_page",
        "products": "manager.product_management_page",
        "brands": "manager.product_management_page",
        "categories": "manager.product_management_page",
        "stock": "manager.stock_page",
        "sales": "manager.sales_page",
        "reports": "manager.reports_page",
        "wallet_history": "manager.wallet_history_page",
        "easyload_history": "manager.easyload_history_page",
        "cash_history": "manager.cash_history_page",
        "customers": "manager.customers_page",
        "settings": "manager.settings_page",
    }
    if page in mapping:
        if page in ("products", "brands", "categories"):
            return url_for(mapping[page], tab=page)
        return url_for(mapping[page])
    return url_for("manager.dashboard")


def _redirect_to_page(page: str | None = None):
    return redirect(_url_for_page(page))


def _build_sale_cash_summary(db, shop_id: int, sale_id: int):
    sale, items = Sale.get_with_items(db, shop_id, sale_id)
    if not sale:
        return None

    customer_name = (sale["customer_name"] or "").strip() or "Walk-in Customer"
    line_items = []
    sale_total = 0.0
    purchase_total = 0.0

    for item in items:
        quantity = int(item["quantity"] or 0)
        unit_price = float(item["unit_price"] or 0)
        line_total = round(quantity * unit_price, 2)
        purchase_rate = float(item.get("unit_cost") or 0)
        purchase_value = round(quantity * purchase_rate, 2)
        profit_value = round(line_total - purchase_value, 2)
        profit_percent = round((profit_value / purchase_value) * 100, 2) if purchase_value > 0 else None

        sale_total += line_total
        purchase_total += purchase_value
        line_items.append(
            {
                "product_name": item["product_name"],
                "quantity": quantity,
                "sale_price": round(unit_price, 2),
                "line_total": line_total,
                "purchase_rate": round(purchase_rate, 2),
                "purchase_total": purchase_value,
                "profit": profit_value,
                "profit_percent": profit_percent,
            }
        )

    total_profit = round(sale_total - purchase_total, 2)
    total_profit_percent = round((total_profit / purchase_total) * 100, 2) if purchase_total > 0 else None

    return {
        "sale_id": sale["id"],
        "sale_type": sale["sale_type"],
        "created_at": sale["created_at"],
        "customer_name": customer_name,
        "customer_phone": sale["customer_phone"] or "",
        "sale_total": round(sale_total, 2),
        "purchase_total": round(purchase_total, 2),
        "profit": total_profit,
        "profit_percent": total_profit_percent,
        "items": line_items,
    }

def _safe_manager_return_url(raw: str | None):
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("/manager"):
        return raw
    return None


def _build_package_profit_note(note: str | None):
    clean_note = (note or "").strip()
    return f"{PACKAGE_PROFIT_MARKER} {clean_note}".strip()


def _is_package_profit_note(note: str | None):
    return (note or "").strip().startswith(PACKAGE_PROFIT_MARKER)


def _display_package_profit_note(note: str | None):
    clean_note = (note or "").strip()
    if _is_package_profit_note(clean_note):
        clean_note = clean_note[len(PACKAGE_PROFIT_MARKER):].strip()
    return clean_note


def _build_wallet_refresh_sale_note(channel_label: str, system_balance: float, actual_balance: float):
    return (
        f"Wallet refresh sold amount from {channel_label}: "
        f"system PKR {system_balance:.2f}, actual PKR {actual_balance:.2f}"
    )


def _build_easyload_refresh_sale_note(channel_label: str, system_balance: float, actual_balance: float):
    return (
        f"Easyload refresh sold amount from {channel_label}: "
        f"system PKR {system_balance:.2f}, actual PKR {actual_balance:.2f}"
    )


def _is_internal_counter_movement_note(note: str):
    clean_note = (note or "").strip().lower()
    return (
        clean_note.startswith("cash transferred from counter to ")
        or clean_note.startswith("transferred to easypaisa:")
        or clean_note.startswith("transferred to jazzcash:")
        or clean_note.startswith("purchased zong load:")
        or clean_note.startswith("purchased jazz/warid load:")
        or clean_note.startswith("purchased jazz load:")
        or clean_note.startswith("purchased ufone load:")
        or clean_note.startswith("purchased telenor load:")
        or clean_note.startswith("wallet profit moved from ")
    )


def _cash_history_counter_entry_label(entry_type: str, note: str, cash_bucket: str = "counter"):
    clean_note = (note or "").strip().lower()
    if _is_package_profit_note(note):
        return "Package Profit Out" if entry_type == "expense" else "Package Profit In"
    if "sale restored #" in clean_note:
        return "Sale Restored"
    if "sale #" in clean_note:
        return "Sale Received"
    if cash_bucket == "online":
        return "Online Cash Spent" if entry_type == "expense" else "Online Cash Added"
    return "Counter Cash Spent" if entry_type == "expense" else "Counter Cash Added"


def _cash_history_service_entry_label(source_key: str, entry: dict):
    entry_type = entry.get("entry_type") or ""
    note = (entry.get("note") or "").strip().lower()
    if note.startswith("daily wallet balance refresh") or note.startswith("wallet balance updated"):
        return "Wallet Balance Refresh"
    if bool(entry.get("is_profit_to_counter")):
        return "Wallet Profit to Counter"
    if source_key == "wallet":
        if entry_type == "cash_in" and note.startswith("cash transferred from counter to "):
            return "Counter to Wallet"
        if entry_type == "cash_in":
            return "Wallet Cash Added"
        if entry_type == "cash_out":
            return "Wallet Cash Out"
    if source_key == "easyload":
        if entry_type == "purchase_in" and note.startswith("cash transferred from counter to "):
            return "Counter to Easyload"
        if entry_type == "purchase_in":
            return "Easyload Purchased"
        if entry_type == "out":
            return "Easyload Out"
    return entry.get("entry_label") or "Cash Entry"


def _cash_history_balance_deltas(entry: dict):
    amount = float(entry.get("amount") or 0)
    signed_amount = float(entry.get("signed_amount") or 0)
    entry_type = entry.get("entry_type") or ""
    note = (entry.get("note") or "").strip().lower()
    source = entry.get("source")
    channel_label = entry.get("channel_label") or "Cash"
    detail_kind = entry.get("detail_kind") or ""

    if detail_kind == "wallet_profit_transfer":
        return [("counter_cash", "Counter Cash", amount)]
    if source == "Counter Cash":
        bucket = entry.get("cash_bucket") or "counter"
        if bucket == "online":
            return [("online_cash", "Online Cash", signed_amount)]
        return [("counter_cash", "Counter Cash", signed_amount)]
    if source == "Wallet Cash":
        deltas = []
        if entry_type == "cash_in":
            if note.startswith("cash transferred from counter to "):
                deltas.append(("counter_cash", "Counter Cash", -amount))
            deltas.append((entry.get("channel_key") or channel_label, channel_label, amount))
        elif entry_type == "cash_out":
            deltas.append((entry.get("channel_key") or channel_label, channel_label, -amount))
        elif signed_amount:
            deltas.append((entry.get("channel_key") or channel_label, channel_label, signed_amount))
        return deltas
    if source == "Easyload":
        deltas = []
        if entry_type == "purchase_in":
            if note.startswith("cash transferred from counter to "):
                deltas.append(("counter_cash", "Counter Cash", -amount))
            deltas.append((entry.get("channel_key") or channel_label, channel_label, signed_amount or amount))
        elif entry_type == "out":
            deltas.append((entry.get("channel_key") or channel_label, channel_label, -amount))
        elif signed_amount:
            deltas.append((entry.get("channel_key") or channel_label, channel_label, signed_amount))
        return deltas
    return []


def _attach_cash_history_balance_snapshots(cash_history):
    balances = {}
    for day_group in reversed(cash_history):
        for entry in reversed(day_group.get("entries", [])):
            balance_changes = []
            for key, label, delta in _cash_history_balance_deltas(entry):
                before = float(balances.get(key, 0.0))
                after = before + float(delta or 0)
                balances[key] = after
                balance_changes.append(
                    {
                        "label": label,
                        "before": before,
                        "after": after,
                        "delta": float(delta or 0),
                    }
                )
            entry["balance_changes"] = balance_changes


def _normalize_cash_history_entries(system_cash_history, wallet_channels, easyload_channels):
    grouped = {}
    ordered_days = []

    def ensure_day(day: str):
        if day not in grouped:
            grouped[day] = {
                "day": day,
                "day_total": 0.0,
                "entries": [],
                "source_totals": {
                    "wallet": 0.0,
                    "easyload": 0.0,
                    "counter": 0.0,
                    "other": 0.0,
                },
            }
            ordered_days.append(day)
        return grouped[day]

    def add_entry(day: str, entry: dict):
        bucket = entry.get("bucket") or "other"
        filter_tags = entry.get("filter_tags") or [bucket]
        day_group = ensure_day(day)
        signed_amount = float(entry.get("signed_amount") or 0)
        day_group["day_total"] += signed_amount
        day_group["source_totals"][bucket] = day_group["source_totals"].get(bucket, 0.0) + signed_amount
        if "other" in filter_tags and bucket != "other":
            day_group["source_totals"]["other"] = day_group["source_totals"].get("other", 0.0) + signed_amount
        day_group["entries"].append(entry)

    for day_group in system_cash_history:
        day = day_group["day"]
        for entry in day_group["entries"]:
            note = (entry.get("expense_name") or "").strip()
            if _is_internal_counter_movement_note(note):
                continue
            note_lower = note.lower()
            bucket = "counter"
            if "sale #" not in note_lower and "sale restored #" not in note_lower:
                bucket = "other"
            add_entry(
                day,
                {
                    "id": entry.get("id"),
                    "source": "Counter Cash",
                    "channel_key": "counter_cash",
                    "channel_label": "Package Profit" if _is_package_profit_note(note) else "Counter Cash",
                    "bucket": "counter",
                    "filter_tags": ["counter", "other"] if bucket == "other" else ["counter"],
                    "entry_type": entry.get("entry_type") or "add",
                    "entry_label": _cash_history_counter_entry_label(
                        entry.get("entry_type") or "add",
                        note,
                        entry.get("cash_bucket") or "counter",
                    ),
                    "amount": float(entry.get("amount") or 0),
                    "signed_amount": float(entry.get("signed_amount") or 0),
                    "note": _display_package_profit_note(note) if _is_package_profit_note(note) else (note or "Counter cash entry"),
                    "meta": "Package Profit" if _is_package_profit_note(note) else ("Online Cash" if (entry.get("cash_bucket") or "counter") == "online" else "Counter Cash"),
                    "cash_bucket": entry.get("cash_bucket") or "counter",
                    "created_at": entry.get("created_at") or "",
                    "detail_kind": "package_profit" if _is_package_profit_note(note) else "counter",
                },
            )

    for channel in wallet_channels:
        for day_group in channel["history"]:
            day = day_group["day"]
            for entry in day_group["entries"]:
                profit_to_counter = bool(entry.get("is_profit_to_counter"))
                bucket = "wallet"
                if profit_to_counter:
                    bucket = "other"
                add_entry(
                    day,
                    {
                        "id": entry.get("id"),
                        "source": "Wallet Cash",
                        "channel_key": channel["key"],
                        "channel_label": channel["label"],
                        "bucket": bucket,
                        "filter_tags": ["wallet", "other"] if profit_to_counter else ["wallet"],
                        "entry_type": entry.get("entry_type") or "",
                        "entry_label": _cash_history_service_entry_label("wallet", entry),
                        "amount": float(entry.get("amount") or 0),
                        "signed_amount": float(entry.get("signed_amount") or 0),
                        "note": entry.get("note") or "",
                        "meta": "Counter Cash" if profit_to_counter else "Wallet",
                        "created_at": entry.get("created_at") or "",
                        "detail_kind": "wallet_profit_transfer" if profit_to_counter else "wallet",
                        "profit_amount": float(entry.get("profit_amount") or 0),
                    },
                )

    for channel in easyload_channels:
        for day_group in channel["history"]:
            day = day_group["day"]
            for entry in day_group["entries"]:
                add_entry(
                    day,
                    {
                        "id": entry.get("id"),
                        "source": "Easyload",
                        "channel_key": channel["key"],
                        "channel_label": channel["label"],
                        "bucket": "easyload",
                        "filter_tags": ["easyload"],
                        "entry_type": entry.get("entry_type") or "",
                        "entry_label": _cash_history_service_entry_label("easyload", entry),
                        "amount": float(entry.get("amount") or 0),
                        "signed_amount": float(entry.get("signed_amount") or 0),
                        "note": entry.get("note") or "",
                        "meta": "Easyload",
                        "created_at": entry.get("created_at") or "",
                        "detail_kind": "easyload",
                        "profit_amount": float(entry.get("profit_amount") or 0),
                    },
                )

    normalized = []
    for day in ordered_days:
        day_group = grouped[day]
        day_group["entries"].sort(
            key=lambda item: ((item.get("created_at") or ""), int(item.get("id") or 0)),
            reverse=True,
        )
        day_group["entry_count"] = len(day_group["entries"])
        normalized.append(day_group)
    _attach_cash_history_balance_snapshots(normalized)
    return normalized


def _flatten_finance_entries(channel_groups, source_key: str):
    entries = []
    for channel in channel_groups:
        for day_group in channel["history"]:
            for entry in day_group["entries"]:
                signed_amount = float(entry.get("signed_amount") or 0)
                entries.append(
                    {
                        "id": entry.get("id"),
                        "timestamp": entry.get("created_at") or "",
                        "channel_key": channel["key"],
                        "channel_label": channel["label"],
                        "source_key": source_key,
                        "entry_type": entry.get("entry_type") or "",
                        "entry_label": _cash_history_service_entry_label(source_key, entry),
                        "note": entry.get("note") or "",
                        "amount": float(entry.get("amount") or 0),
                        "profit_amount": float(entry.get("profit_amount") or 0),
                        "signed_amount": signed_amount,
                    }
                )
    entries.sort(key=lambda item: (item["timestamp"], int(item["id"] or 0)), reverse=True)
    return entries


def _flatten_counter_cash_entries(system_cash_history):
    entries = []
    for day_group in system_cash_history:
        for entry in day_group["entries"]:
            note = (entry.get("expense_name") or "").strip()
            if _is_internal_counter_movement_note(note):
                continue
            entries.append(
                {
                    "id": entry.get("id"),
                    "timestamp": entry.get("created_at") or "",
                    "entry_type": entry.get("entry_type") or "add",
                    "entry_label": _cash_history_counter_entry_label(
                        entry.get("entry_type") or "add",
                        note,
                        entry.get("cash_bucket") or "counter",
                    ),
                    "note": _display_package_profit_note(note) if _is_package_profit_note(note) else note,
                    "amount": float(entry.get("amount") or 0),
                    "signed_amount": float(entry.get("signed_amount") or 0),
                    "cash_bucket": entry.get("cash_bucket") or "counter",
                }
            )
    entries.sort(key=lambda item: (item["timestamp"], int(item["id"] or 0)), reverse=True)
    return entries


def _combine_digital_history_entries(wallet_entries, easyload_entries):
    entries = list(wallet_entries) + list(easyload_entries)
    entries.sort(key=lambda item: (item["timestamp"], int(item["id"] or 0)), reverse=True)
    return entries


def _combine_all_cash_history_entries(digital_entries, counter_entries):
    normalized_counter_entries = [
        {
            "id": entry.get("id"),
            "timestamp": entry.get("timestamp") or "",
            "source_key": "counter",
            "channel_label": "Online Cash" if (entry.get("cash_bucket") or "counter") == "online" else "Counter Cash",
            "entry_label": entry.get("entry_label") or "",
            "note": entry.get("note") or "",
            "amount": float(entry.get("amount") or 0),
            "profit_amount": 0.0,
            "signed_amount": float(entry.get("signed_amount") or 0),
            "cash_bucket": entry.get("cash_bucket") or "counter",
        }
        for entry in counter_entries
    ]
    entries = list(digital_entries) + normalized_counter_entries
    entries.sort(key=lambda item: (item["timestamp"], int(item["id"] or 0)), reverse=True)
    return entries


def _find_cash_history_day(cash_history, day: str):
    for day_group in cash_history:
        if day_group.get("day") == day:
            return day_group
    return None


def _build_cash_history_day_breakdown(day_group: dict | None):
    breakdown = {
        "wallet": {
            "easypaisa": 0.0,
            "jazzcash": 0.0,
        },
        "easyload": {
            "zong": 0.0,
            "jazz": 0.0,
            "ufone": 0.0,
            "telenor": 0.0,
        },
        "counter": 0.0,
        "online": 0.0,
    }
    if not day_group:
        return breakdown

    for entry in day_group.get("entries", []):
        signed_amount = float(entry.get("signed_amount") or 0)
        source = entry.get("source")
        channel_key = entry.get("channel_key")
        if source == "Wallet Cash" and channel_key in breakdown["wallet"]:
            breakdown["wallet"][channel_key] += signed_amount
        elif source == "Easyload" and channel_key in breakdown["easyload"]:
            breakdown["easyload"][channel_key] += signed_amount
        elif source == "Counter Cash":
            if (entry.get("cash_bucket") or "counter") == "online":
                breakdown["online"] += signed_amount
            else:
                breakdown["counter"] += signed_amount

    return breakdown


def _add_profit_history_entry(grouped: dict, ordered_days: list, entry: dict):
    day = entry.get("day") or ""
    if not day:
        return
    if day not in grouped:
        grouped[day] = {
            "day": day,
            "total_profit": 0.0,
            "entry_count": 0,
            "source_totals": {
                "sales": 0.0,
                "wallet": 0.0,
                "easyload": 0.0,
                "package": 0.0,
            },
            "entries": [],
        }
        ordered_days.append(day)
    day_group = grouped[day]
    profit_amount = float(entry.get("profit_amount") or 0)
    source_key = entry.get("source_key") or "sales"
    day_group["total_profit"] += profit_amount
    day_group["entry_count"] += 1
    day_group["source_totals"][source_key] = day_group["source_totals"].get(source_key, 0.0) + profit_amount
    day_group["entries"].append(entry)


def _build_profit_history(db, shop_id: int):
    grouped = {}
    ordered_days = []

    sale_rows = db.execute(
        """
        SELECT
          s.id,
          s.sale_type,
          s.total_amount,
          s.created_at,
          date(datetime(s.created_at, 'localtime')) AS local_day
        FROM sales s
        WHERE s.shop_id = ?
        ORDER BY s.created_at DESC, s.id DESC;
        """,
        (shop_id,),
    ).fetchall()
    for sale in sale_rows:
        if sale["sale_type"] != "sale":
            continue
        sale_summary = _build_sale_cash_summary(db, shop_id, sale["id"])
        if not sale_summary:
            continue
        profit_amount = float(sale_summary.get("profit") or 0)
        if abs(profit_amount) < 0.01:
            continue
        day = sale["local_day"] or (sale["created_at"] or "")[:10]
        _add_profit_history_entry(
            grouped,
            ordered_days,
            {
                "id": f"sale-{sale['id']}",
                "record_id": sale["id"],
                "day": day,
                "created_at": sale["created_at"] or "",
                "source_key": "sales",
                "source_label": f"Sale #{sale['id']}",
                "profit_type": "Sale Profit",
                "profit_amount": profit_amount,
                "message": f"Sale profit from Sale #{sale['id']}",
                "detail_kind": "sale_profit",
                "sale_total": float(sale_summary.get("sale_total") or 0),
                "purchase_total": float(sale_summary.get("purchase_total") or 0),
                "profit_percent": sale_summary.get("profit_percent"),
            },
        )

    wallet_rows = db.execute(
        """
        SELECT
          id,
          channel,
          amount,
          note,
          created_at,
          date(datetime(created_at, 'localtime')) AS local_day
        FROM service_transactions
        WHERE shop_id = ?
          AND channel IN ('easypaisa', 'jazzcash')
          AND entry_type = 'profit_in'
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id,),
    ).fetchall()
    for row in wallet_rows:
        amount = float(row["amount"] or 0)
        if amount <= 0:
            continue
        note = ServiceTransaction.display_note(row["note"] or "")
        profit_to_counter = ServiceTransaction.is_profit_to_counter(row["note"] or "")
        channel_label = ServiceTransaction.DISPLAY_NAMES.get(row["channel"], row["channel"].title())
        day = row["local_day"] or (row["created_at"] or "")[:10]
        _add_profit_history_entry(
            grouped,
            ordered_days,
            {
                "id": f"wallet-{row['id']}",
                "record_id": row["id"],
                "day": day,
                "created_at": row["created_at"] or "",
                "source_key": "wallet",
                "source_label": channel_label,
                "profit_type": "Wallet Profit",
                "profit_amount": amount,
                "message": note or "Wallet profit added",
                "destination": "Counter Cash" if profit_to_counter else "Wallet",
                "detail_kind": "wallet_profit",
            },
        )

    easyload_rows = db.execute(
        """
        SELECT
          id,
          channel,
          amount,
          profit_amount,
          note,
          created_at,
          date(datetime(created_at, 'localtime')) AS local_day
        FROM service_transactions
        WHERE shop_id = ?
          AND channel IN ('zong', 'jazz', 'ufone', 'telenor')
          AND entry_type = 'purchase_in'
          AND profit_amount > 0
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id,),
    ).fetchall()
    for row in easyload_rows:
        profit_amount = float(row["profit_amount"] or 0)
        if profit_amount <= 0:
            continue
        channel_label = ServiceTransaction.DISPLAY_NAMES.get(row["channel"], row["channel"].title())
        amount = float(row["amount"] or 0)
        day = row["local_day"] or (row["created_at"] or "")[:10]
        _add_profit_history_entry(
            grouped,
            ordered_days,
            {
                "id": f"easyload-{row['id']}",
                "record_id": row["id"],
                "day": day,
                "created_at": row["created_at"] or "",
                "source_key": "easyload",
                "source_label": channel_label,
                "profit_type": "Easyload Profit",
                "profit_amount": profit_amount,
                "message": row["note"] or "Easyload profit",
                "detail_kind": "easyload_profit",
                "load_amount": amount,
                "rate_per_1000": ServiceTransaction.LOAD_RATES.get(row["channel"]),
                "credited_amount": round(amount + profit_amount, 2),
            },
        )

    package_profit_rows = db.execute(
        """
        SELECT
          id,
          amount,
          entry_type,
          expense_name,
          created_at,
          date(datetime(created_at, 'localtime')) AS local_day
        FROM system_cash_entries
        WHERE shop_id = ?
          AND expense_name LIKE '[package_profit]%'
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id,),
    ).fetchall()
    for row in package_profit_rows:
        amount = float(row["amount"] or 0)
        if amount <= 0:
            continue
        signed_amount = -amount if (row["entry_type"] or "") == "expense" else amount
        day = row["local_day"] or (row["created_at"] or "")[:10]
        _add_profit_history_entry(
            grouped,
            ordered_days,
            {
                "id": f"package-{row['id']}",
                "record_id": row["id"],
                "day": day,
                "created_at": row["created_at"] or "",
                "source_key": "package",
                "source_label": "Package Profit",
                "profit_type": "Package Profit Out" if (row["entry_type"] or "") == "expense" else "Package Profit In",
                "profit_amount": signed_amount,
                "message": _display_package_profit_note(row["expense_name"] or "") or "Package profit entry",
                "destination": "Counter Cash",
                "detail_kind": "package_profit",
            },
        )

    history = [grouped[day] for day in ordered_days]
    for day_group in history:
        day_group["total_profit"] = round(day_group["total_profit"], 2)
        for key, value in day_group["source_totals"].items():
            day_group["source_totals"][key] = round(float(value or 0), 2)
        day_group["entries"].sort(
            key=lambda item: ((item.get("created_at") or ""), str(item.get("id") or "")),
            reverse=True,
        )
    history.sort(key=lambda item: item["day"], reverse=True)
    return history


def _build_daily_report(db, shop_id: int, day_iso: str):
    report_sales = Sale.by_date_with_items(db, shop_id, day_iso, day_iso)
    sale_blocks = []
    for block in report_sales:
        sale_row = block.get("sale")
        sale = dict(sale_row) if sale_row else {}
        if sale.get("sale_type") == "sale":
            sale_blocks.append(
                {
                    "sale": sale,
                    "sale_items": block.get("sale_items") or [],
                }
            )

    total_sale_amount = 0.0
    total_sale_cost = 0.0
    total_sale_profit = 0.0
    sale_detail_entries = []
    for block in sale_blocks:
        sale = block.get("sale") or {}
        total_sale_amount += float(sale.get("total_amount") or 0)
        sale_cost = 0.0
        for item in block.get("sale_items") or []:
            quantity = int(item.get("quantity") or 0)
            sale_cost += quantity * float(item.get("unit_cost") or 0)
        total_sale_cost += sale_cost
        sale_profit = float(sale.get("total_amount") or 0) - sale_cost
        customer_name = sale.get("customer_name") or "Walk-in customer"
        payment_label = "Online Cash" if (sale.get("payment_method") or "counter") == "online" else "Counter Cash"
        sale_detail_entries.append(
            {
                "amount": round(float(sale.get("total_amount") or 0), 2),
                "created_at": sale.get("created_at") or "",
                "entry_label": f"Sale #{sale.get('id')}",
                "profit_amount": round(sale_profit, 2),
                "note": f"{customer_name} | {payment_label}",
            }
        )
    total_sale_profit = total_sale_amount - total_sale_cost
    sale_profit_percent = round((total_sale_profit / total_sale_cost) * 100, 2) if total_sale_cost > 0 else None

    wallet_profit_rows = db.execute(
        """
        SELECT id, channel, amount, note, created_at
        FROM service_transactions
        WHERE shop_id = ?
          AND channel IN ('easypaisa', 'jazzcash')
          AND entry_type = 'profit_in'
          AND date(datetime(created_at, 'localtime')) = date(?)
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id, day_iso),
    ).fetchall()
    wallet_profit = {
        "easypaisa": 0.0,
        "jazzcash": 0.0,
        "detail_entries": [],
        "detail_entries_by_channel": {
            "easypaisa": [],
            "jazzcash": [],
        },
    }
    for row in wallet_profit_rows:
        channel = row["channel"]
        amount = float(row["amount"] or 0)
        wallet_profit[channel] += amount
        detail_entry = {
            "amount": round(amount, 2),
            "created_at": row["created_at"] or "",
            "entry_label": f"{ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())} Profit",
            "note": row["note"] or "Wallet profit recorded",
        }
        wallet_profit["detail_entries"].append(detail_entry)
        wallet_profit["detail_entries_by_channel"][channel].append(detail_entry)
    wallet_profit["total"] = sum(
        wallet_profit[channel]
        for channel in ("easypaisa", "jazzcash")
    )

    easyload_profit_rows = db.execute(
        """
        SELECT id, channel, amount, profit_amount, note, created_at
        FROM service_transactions
        WHERE shop_id = ?
          AND channel IN ('zong', 'jazz', 'ufone', 'telenor')
          AND entry_type = 'purchase_in'
          AND date(datetime(created_at, 'localtime')) = date(?)
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id, day_iso),
    ).fetchall()
    easyload_profit = {
        channel: 0.0 for channel in ServiceTransaction.EASYLOAD_CHANNELS
    }
    easyload_profit["detail_entries"] = []
    easyload_profit["detail_entries_by_channel"] = {
        channel: [] for channel in ServiceTransaction.EASYLOAD_CHANNELS
    }
    for row in easyload_profit_rows:
        channel = row["channel"]
        profit_amount = float(row["profit_amount"] or 0)
        easyload_profit[channel] += profit_amount
        detail_entry = {
            "amount": round(profit_amount, 2),
            "created_at": row["created_at"] or "",
            "entry_label": f"{ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())} Profit",
            "note": (
                f"Load PKR {float(row['amount'] or 0):.2f}"
                + (f" | {row['note']}" if row["note"] else "")
            ),
        }
        easyload_profit["detail_entries"].append(detail_entry)
        easyload_profit["detail_entries_by_channel"][channel].append(detail_entry)
    easyload_profit["total"] = sum(
        easyload_profit[channel]
        for channel in ServiceTransaction.EASYLOAD_CHANNELS
    )

    package_profit_rows = db.execute(
        """
        SELECT
          expense_name,
          entry_type,
          amount,
          created_at
        FROM system_cash_entries
        WHERE shop_id = ?
          AND expense_name LIKE '[package_profit]%'
          AND date(datetime(created_at, 'localtime')) = date(?);
        """,
        (shop_id, day_iso),
    ).fetchall()
    package_profit_total = 0.0
    package_profit_entries = []
    for row in package_profit_rows:
        signed_amount = -float(row["amount"] or 0) if (row["entry_type"] or "") == "expense" else float(row["amount"] or 0)
        package_profit_total += signed_amount
        package_profit_entries.append(
            {
                "label": _display_package_profit_note(row["expense_name"] or "") or "General",
                "amount": signed_amount,
                "created_at": row["created_at"] if "created_at" in row.keys() else "",
                "entry_label": "Package Profit Out" if (row["entry_type"] or "") == "expense" else "Package Profit In",
                "note": _display_package_profit_note(row["expense_name"] or "") or "Package profit entry",
            }
        )

    online_cash_rows = db.execute(
        """
        SELECT id, amount, entry_type, expense_name, created_at
        FROM system_cash_entries
        WHERE shop_id = ?
          AND cash_bucket = 'online'
          AND date(datetime(created_at, 'localtime')) = date(?)
        ORDER BY created_at DESC, id DESC;
        """,
        (shop_id, day_iso),
    ).fetchall()
    online_cash_total = 0.0
    online_cash_entries = []
    for row in online_cash_rows:
        signed_amount = -float(row["amount"] or 0) if (row["entry_type"] or "") == "expense" else float(row["amount"] or 0)
        online_cash_total += signed_amount
        online_cash_entries.append(
            {
                "amount": round(signed_amount, 2),
                "created_at": row["created_at"] or "",
                "entry_label": "Online Cash Out" if (row["entry_type"] or "") == "expense" else "Online Cash In",
                "note": row["expense_name"] or "Online cash movement",
            }
        )

    return {
        "day": day_iso,
        "sales": {
            "total_sale_amount": round(total_sale_amount, 2),
            "total_sale_cost": round(total_sale_cost, 2),
            "total_sale_profit": round(total_sale_profit, 2),
            "sale_profit_percent": sale_profit_percent,
            "sale_count": len(sale_blocks),
            "detail_entries": sale_detail_entries,
        },
        "wallet_profit": wallet_profit,
        "easyload_profit": easyload_profit,
        "package_profit": {
            "entries": package_profit_entries,
            "total": round(package_profit_total, 2),
        },
        "online_cash": {
            "total": round(float(online_cash_total or 0), 2),
            "detail_entries": online_cash_entries,
        },
    }


def _daily_report_available_dates(db, shop_id: int, today_iso: str):
    rows = db.execute(
        """
        SELECT day
        FROM (
          SELECT date(datetime(created_at, 'localtime')) AS day
          FROM sales
          WHERE shop_id = ?
          UNION
          SELECT date(datetime(created_at, 'localtime')) AS day
          FROM service_transactions
          WHERE shop_id = ?
          UNION
          SELECT date(datetime(created_at, 'localtime')) AS day
          FROM system_cash_entries
          WHERE shop_id = ?
        )
        WHERE day IS NOT NULL AND day <> ''
        ORDER BY day DESC;
        """,
        (shop_id, shop_id, shop_id),
    ).fetchall()
    available = [row["day"] for row in rows if row["day"]]
    if today_iso not in available:
        available.insert(0, today_iso)
    return available


def _build_manager_context(db, shop, active_page: str, daily_report_day: str | None = None):
    products = Product.all_by_shop(db, shop["id"])
    brands = Brand.all_by_shop(db, shop["id"])
    categories = Category.all_by_shop(db, shop["id"])
    total_products = len(products)
    total_stock = sum(p["quantity"] for p in products)
    out_of_stock = sum(1 for p in products if p["quantity"] <= (p["reorder_level"] or 0))

    category_products = {c["id"]: [] for c in categories}
    brand_products = {b["id"]: [] for b in brands}
    for p in products:
        cid = p["category_id"]
        if cid in category_products:
            category_products[cid].append(p)
        bid = p["brand_id"]
        if bid in brand_products:
            brand_products[bid].append(p)

    category_counts = {cid: len(items) for cid, items in category_products.items()}
    brand_counts = {bid: len(items) for bid, items in brand_products.items()}
    stock_batches = StockBatch.all_by_shop(db, shop["id"])
    product_latest = {}
    product_purchase_summary = {}
    product_purchase_previews = {}
    product_sale_defaults = {}
    stock_batch_summary_map = {}
    for batch in stock_batches:
        pid = batch["product_id"]
        if pid not in product_latest:
            product_latest[pid] = {
                "purchase_rate": batch["purchase_rate"],
                "sale_price": batch["sale_price"],
            }
        summary = stock_batch_summary_map.setdefault(
            batch["batch_date"],
            {
                "batch_date": batch["batch_date"],
                "product_count": 0,
                "total_purchase": 0.0,
            },
        )
        summary["product_count"] += 1
        summary["total_purchase"] += (batch["purchase_rate"] * batch["quantity"])
        purchase_summary = product_purchase_summary.setdefault(
            pid,
            {
                "total_batches": 0,
                "total_quantity": 0,
                "total_spend": 0.0,
            },
        )
        purchase_summary["total_batches"] += 1
        purchase_summary["total_quantity"] += batch["quantity"]
        purchase_summary["total_spend"] += batch["quantity"] * batch["purchase_rate"]
        previews = product_purchase_previews.setdefault(pid, [])
        if len(previews) < 3:
            previews.append(
                {
                    "batch_date": batch["batch_date"],
                    "quantity": batch["quantity"],
                    "purchase_rate": batch["purchase_rate"],
                }
            )
    for batch in stock_batches:
        pid = batch["product_id"]
        if pid not in product_sale_defaults:
            product_sale_defaults[pid] = batch["sale_price"]
    stock_batch_summary = sorted(
        stock_batch_summary_map.values(),
        key=lambda item: item["batch_date"],
        reverse=True,
    )
    today = date.today()
    today_iso = today.isoformat()
    shop_settings = ShopSettings.get_for_shop(db, shop["id"])
    expense_percent = shop_settings["expense_percent"] if shop_settings else 0
    hide_sale_prices = bool(shop_settings["hide_sale_prices"]) if shop_settings else True
    service_totals = ServiceTransaction.totals_by_channel(db, shop["id"])
    cash_bucket_totals = SystemCashEntry.totals_by_bucket(db, shop["id"])
    manual_system_cash = cash_bucket_totals.get("counter", 0.0)
    online_cash_total = cash_bucket_totals.get("online", 0.0)
    system_cash_history = SystemCashEntry.daily_history_with_entries(db, shop["id"])
    wallet_channels = []
    easyload_channels = []
    for channel in ServiceTransaction.VALID_CHANNELS:
        channel_data = (
            {
                "key": channel,
                "label": ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title()),
                "type": "load" if channel in ServiceTransaction.EASYLOAD_CHANNELS else "wallet",
                "balance_total": service_totals.get(channel, {}).get("balance_total", 0.0),
                "in_total": service_totals.get(channel, {}).get("in_total", 0.0),
                "out_total": service_totals.get(channel, {}).get("out_total", 0.0),
                "profit_total": service_totals.get(channel, {}).get("profit_total", 0.0),
                "history": ServiceTransaction.daily_history_with_entries(db, shop["id"], channel),
                "rate_per_1000": ServiceTransaction.LOAD_RATES.get(channel),
            }
        )
        if channel in ServiceTransaction.EASYLOAD_CHANNELS:
            easyload_channels.append(channel_data)
        else:
            wallet_channels.append(channel_data)
    total_wallet_balance = sum(
        service_totals.get(channel["key"], {}).get("cash_balance_total", 0.0)
        for channel in wallet_channels
    )
    total_package_profit = 0.0
    for day_group in system_cash_history:
        for entry in day_group["entries"]:
            if _is_package_profit_note(entry.get("expense_name") or ""):
                total_package_profit += float(entry.get("signed_amount") or 0)
    total_wallet_profit_balance = sum(
        service_totals.get(channel["key"], {}).get("profit_balance_total", 0.0)
        for channel in wallet_channels
    )
    total_easyload_balance = sum(channel["balance_total"] for channel in easyload_channels)
    total_easyload_profit = sum(channel["profit_total"] for channel in easyload_channels)
    total_digital_system_cash = total_wallet_balance + total_wallet_profit_balance + total_easyload_balance
    easypaisa_cash = service_totals.get("easypaisa", {}).get("cash_balance_total", 0.0)
    jazzcash_cash = service_totals.get("jazzcash", {}).get("cash_balance_total", 0.0)
    easypaisa_profit = service_totals.get("easypaisa", {}).get("profit_balance_total", 0.0)
    jazzcash_profit = service_totals.get("jazzcash", {}).get("profit_balance_total", 0.0)
    cash_history = _normalize_cash_history_entries(system_cash_history, wallet_channels, easyload_channels)
    total_cash_movement = sum(day_group["day_total"] for day_group in cash_history)
    wallet_history_entries = _flatten_finance_entries(wallet_channels, "wallet")
    easyload_history_entries = _flatten_finance_entries(easyload_channels, "easyload")
    digital_history_entries = _combine_digital_history_entries(wallet_history_entries, easyload_history_entries)
    counter_history_entries = _flatten_counter_cash_entries(system_cash_history)
    all_cash_history_entries = _combine_all_cash_history_entries(digital_history_entries, counter_history_entries)
    profit_history = _build_profit_history(db, shop["id"])
    total_profit_history_amount = sum(day_group["total_profit"] for day_group in profit_history)
    selected_daily_report_day = daily_report_day or today_iso
    daily_report_available_dates = _daily_report_available_dates(db, shop["id"], today_iso)
    if selected_daily_report_day not in daily_report_available_dates:
        selected_daily_report_day = today_iso
    daily_report = _build_daily_report(db, shop["id"], selected_daily_report_day)

    report_start_iso = today_iso
    report_end_iso = today_iso
    report_sales = []
    report_daily_summary = []
    report_search_performed = False
    reports_available_dates = []
    reports_selected_day = ""

    def _parse_report_date(raw_value, default_value):
        if not raw_value:
            return default_value
        try:
            return datetime.strptime(raw_value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return default_value

    if active_page == "reports":
        reports_available_dates = _daily_report_available_dates(db, shop["id"], today_iso)
        
        # Check if day is explicitly provided via dropdown
        raw_day = request.args.get("day", "").strip()
        selected_day = None
        if raw_day:
            try:
                selected_day = datetime.strptime(raw_day, "%Y-%m-%d").date().isoformat()
            except ValueError:
                selected_day = None

        if not selected_day:
            start_param = request.args.get("sales_report_start")
            end_param = request.args.get("sales_report_end")
            if start_param or end_param:
                report_start_date = _parse_report_date(start_param, today)
                report_end_date = _parse_report_date(end_param, report_start_date)
                selected_day = report_start_date.isoformat()
            else:
                # Default to the most recent date from available_dates
                if reports_available_dates:
                    selected_day = reports_available_dates[0]
                else:
                    selected_day = today_iso
                report_start_date = datetime.strptime(selected_day, "%Y-%m-%d").date()
                report_end_date = report_start_date
        else:
            report_start_date = datetime.strptime(selected_day, "%Y-%m-%d").date()
            report_end_date = report_start_date

        report_search_performed = True
        reports_selected_day = selected_day

        if report_end_date < report_start_date:
            report_end_date = report_start_date

        report_start_iso = report_start_date.isoformat()
        report_end_iso = report_end_date.isoformat()
        report_sales = Sale.by_date_with_items(db, shop["id"], report_start_iso, report_end_iso)
        report_daily_summary = Sale.daily_summary(db, shop["id"], report_start_iso, report_end_iso)

    recent_sales = Sale.recent_with_items(db, shop["id"], limit=5)
    customers = Customer.all_by_shop(db, shop["id"])
    customers_serialized = [dict(customer) for customer in customers]

    customer_insights = []
    for customer in customers:
        sale_rows = db.execute("""
            SELECT s.created_at, si.product_id, si.quantity, si.unit_price, si.unit_cost
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.shop_id = ?
              AND s.customer_id = ?
              AND s.sale_type = 'sale';
        """, (shop["id"], customer["id"])).fetchall()

        total_items = 0
        sale_total = 0.0
        purchase_total = 0.0
        last_purchase = None

        for row in sale_rows:
            qty = row["quantity"] or 0
            price = row["unit_price"] or 0.0
            total_items += qty
            sale_total += qty * price
            latest_rates = product_latest.get(row["product_id"]) or {}
            unit_cost = float(row["unit_cost"] or 0) if "unit_cost" in row.keys() else float(latest_rates.get("purchase_rate") or 0.0)
            purchase_total += qty * unit_cost
            created_at = row["created_at"]
            if created_at and (last_purchase is None or created_at > last_purchase):
                last_purchase = created_at

        profit_pct = None
        if purchase_total > 0:
            profit_pct = ((sale_total - purchase_total) / purchase_total) * 100

        if total_items > 0:
            customer_insights.append(
                {
                    "id": customer["id"],
                    "name": customer["name"],
                    "phone": customer["phone"],
                    "item_count": total_items,
                    "sale_total": sale_total,
                    "purchase_total": purchase_total,
                    "last_purchase": last_purchase,
                    "profit_pct": profit_pct,
                }
            )

    return {
        "shop": shop,
        "products": products,
        "brands": brands,
        "categories": categories,
        "category_products": category_products,
        "category_counts": category_counts,
        "brand_counts": brand_counts,
        "stock_batches": stock_batches,
        "stock_batch_summary": stock_batch_summary,
        "product_latest": product_latest,
        "product_purchase_summary": product_purchase_summary,
        "product_purchase_previews": product_purchase_previews,
        "product_sale_defaults": product_sale_defaults,
        "recent_sales": recent_sales,
        "report_sales": report_sales,
        "report_daily_summary": report_daily_summary,
        "report_start": report_start_iso,
        "report_end": report_end_iso,
        "report_search_performed": report_search_performed,
        "reports_available_dates": reports_available_dates,
        "reports_selected_day": reports_selected_day,
        "customers": customers_serialized,
        "customer_insights": customer_insights,
        "today_iso": today_iso,
        "daily_report": daily_report,
        "daily_report_selected_day": selected_daily_report_day,
        "daily_report_available_dates": daily_report_available_dates,
        "total_products": total_products,
        "total_stock": total_stock,
        "out_of_stock": out_of_stock,
        "active_page": active_page,
        "expense_percent": expense_percent,
        "hide_sale_prices": hide_sale_prices,
        "total_system_cash": total_digital_system_cash + manual_system_cash + online_cash_total,
        "manual_system_cash_total": manual_system_cash,
        "counter_cash_total": manual_system_cash,
        "online_cash_total": online_cash_total,
        "digital_system_cash_total": total_digital_system_cash,
        "easypaisa_cash_total": easypaisa_cash,
        "jazzcash_cash_total": jazzcash_cash,
        "total_wallet_profit": total_wallet_balance,
        "total_wallet_profit_balance": total_wallet_profit_balance,
        "total_wallet_profit_to_counter": sum(
            service_totals.get(channel["key"], {}).get("profit_to_counter_total", 0.0)
            for channel in wallet_channels
        ),
        "total_package_profit": total_package_profit,
        "easypaisa_profit_total": easypaisa_profit,
        "jazzcash_profit_total": jazzcash_profit,
        "total_easyload_profit": total_easyload_balance,
        "total_easyload_commission": total_easyload_profit,
        "total_cash_resources": total_digital_system_cash + manual_system_cash + online_cash_total,
        "wallet_channels": wallet_channels,
        "easyload_channels": easyload_channels,
        "system_cash_history": system_cash_history,
        "cash_history": cash_history,
        "total_cash_movement": total_cash_movement,
        "wallet_history_entries": wallet_history_entries,
        "easyload_history_entries": easyload_history_entries,
        "digital_history_entries": digital_history_entries,
        "counter_history_entries": counter_history_entries,
        "all_cash_history_entries": all_cash_history_entries,
        "profit_history": profit_history,
        "total_profit_history_amount": total_profit_history_amount,
        "profit_modal_open": request.args.get("profit_modal", "").strip().lower(),
        "finance_modal_open": request.args.get("finance_modal", "").strip().lower(),
        "finance_category_open": request.args.get("finance_category", "").strip().lower(),
        "finance_network_open": request.args.get("finance_network", "").strip().lower(),
    }


@manager_bp.route("/", methods=["GET"])
@manager_required
def dashboard():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    page_param = request.args.get("page")
    report_params = request.args.get("sales_report_start") or request.args.get("sales_report_end")
    active_page = page_param or ("reports" if report_params else "overview")
    ctx = _build_manager_context(db, shop, active_page)
    return render_template("manager.html", **ctx)


@manager_bp.route("/product-management", methods=["GET"])
@manager_required
def product_management_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    manage_tab = request.args.get("tab", "products").strip().lower()
    if manage_tab not in {"products", "brands", "categories"}:
        manage_tab = "products"
    ctx = _build_manager_context(db, shop, "product_management")
    ctx["manage_tab"] = manage_tab
    return render_template("manager.html", **ctx)


@manager_bp.route("/products", methods=["GET"])
@manager_required
def products_page():
    return redirect(url_for("manager.product_management_page", tab="products"))


@manager_bp.route("/stock", methods=["GET"])
@manager_required
def stock_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    ctx = _build_manager_context(db, shop, "stock")
    return render_template("manager.html", **ctx)


@manager_bp.route("/sales", methods=["GET"])
@manager_required
def sales_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    selected_customer_id = None
    customer_id_raw = request.args.get("customer_id")
    if customer_id_raw:
        try:
            customer_id = int(customer_id_raw)
        except (TypeError, ValueError):
            flash("Invalid customer selection.", "error")
        else:
            customer = Customer.get_for_shop(db, shop["id"], customer_id)
            if customer:
                selected_customer_id = customer_id
            else:
                flash("Selected customer not found.", "error")
    ctx = _build_manager_context(db, shop, "sales")
    ctx["selected_customer_id"] = selected_customer_id
    return render_template("manager.html", **ctx)


@manager_bp.route("/reports", methods=["GET"])
@manager_required
def reports_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    ctx = _build_manager_context(db, shop, "reports")
    return render_template("manager.html", **ctx)


@manager_bp.route("/daily-report", methods=["GET"])
@manager_required
def daily_report_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    raw_day = request.args.get("day", "").strip()
    selected_day = None
    if raw_day:
        try:
            selected_day = datetime.strptime(raw_day, "%Y-%m-%d").date().isoformat()
        except ValueError:
            selected_day = None
    ctx = _build_manager_context(db, shop, "daily_report", daily_report_day=selected_day)
    return render_template("manager.html", **ctx)


@manager_bp.route("/customers", methods=["GET"])
@manager_required
def customers_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))
    ctx = _build_manager_context(db, shop, "customers")
    return render_template("manager.html", **ctx)


@manager_bp.route("/brands", methods=["GET"])
@manager_required
def brands_page():
    return redirect(url_for("manager.product_management_page", tab="brands"))


@manager_bp.route("/categories", methods=["GET"])
@manager_required
def categories_page():
    return redirect(url_for("manager.product_management_page", tab="categories"))


@manager_bp.route("/products/create", methods=["POST"])
@manager_required
def create_product():
    name = request.form.get("product_name", "").strip()
    brand_id_raw = request.form.get("product_brand_id")
    category_id_raw = request.form.get("product_category_id")
    reorder_level_raw = request.form.get("product_reorder_level", "3")
    return_to = request.form.get("return_to", "").strip().lower()

    def _redirect_after():
        if return_to.startswith("brand:"):
            try:
                brand_id = int(return_to.split(":", 1)[1])
            except (TypeError, ValueError, IndexError):
                return _redirect_to_page("products")
            return redirect(url_for("manager.brand_detail", brand_id=brand_id))
        if return_to.startswith("category:"):
            try:
                category_id = int(return_to.split(":", 1)[1])
            except (TypeError, ValueError, IndexError):
                return _redirect_to_page("products")
            return redirect(url_for("manager.category_detail", category_id=category_id))
        return _redirect_to_page("products")

    if not name:
        flash("Product name is required.", "error")
        return _redirect_after()

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    brand_id = None
    if brand_id_raw:
        try:
            brand_id = int(brand_id_raw)
        except ValueError:
            brand_id = None

    if brand_id:
        brand = Brand.get_by_id(db, shop["id"], brand_id)
        if not brand:
            flash("Invalid brand selected.", "error")
            return _redirect_after()

    category_id = None
    if category_id_raw:
        try:
            category_id = int(category_id_raw)
        except ValueError:
            category_id = None

    if category_id:
        category = Category.get_by_id(db, shop["id"], category_id)
        if not category:
            flash("Invalid category selected.", "error")
            return _redirect_after()
    else:
        flash("Please select a category.", "error")
        return _redirect_after()

    try:
        reorder_level = int(reorder_level_raw)
        if reorder_level < 0:
            raise ValueError
    except (TypeError, ValueError):
        flash("Enter a valid minimum stock level (0 or above).", "error")
        return _redirect_after()

    try:
        Product.create(db, shop["id"], name, 0.0, brand_id, category_id, reorder_level)
        db.commit()
        flash("Product registered successfully.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("This SKU already exists for your shop.", "error")

    return _redirect_after()


@manager_bp.route("/products/add_stock", methods=["POST"])
@manager_required
def add_stock():
    def parse_float(value_raw, label):
        try:
            value = float(value_raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            flash(f"Enter a valid {label}.", "error")
            return None

    entries = []
    multi_ids = request.form.getlist("batch_product_id[]")
    batch_date_group = request.form.get("batch_date_group", "").strip()

    if multi_ids:
        quantities = request.form.getlist("batch_quantity[]")
        purchase_rates = request.form.getlist("batch_purchase_rate[]")
        sale_prices = request.form.getlist("batch_sale_price[]")
        total = len(multi_ids)
        if not (len(quantities) == len(purchase_rates) == len(sale_prices) == total):
            flash("Missing restock fields for one of the products.", "error")
            return _redirect_to_page("stock")
        if batch_date_group:
            try:
                batch_date_common = datetime.strptime(batch_date_group, "%Y-%m-%d").date().isoformat()
            except ValueError:
                flash("Enter a valid restock date.", "error")
                return _redirect_to_page("stock")
        else:
            batch_date_common = date.today().isoformat()
        for idx in range(total):
            try:
                pid = int(multi_ids[idx])
            except (TypeError, ValueError):
                flash("Invalid product selected.", "error")
                return _redirect_to_page("stock")
            try:
                quantity = int(quantities[idx])
            except (TypeError, ValueError):
                flash("Enter a valid quantity.", "error")
                return _redirect_to_page("stock")
            purchase_rate = parse_float(purchase_rates[idx], "purchase rate")
            if purchase_rate is None:
                return _redirect_to_page("stock")
            sale_price = parse_float(sale_prices[idx], "sale price")
            if sale_price is None:
                return _redirect_to_page("stock")
            entries.append(
                {
                    "product_id": pid,
                    "quantity": quantity,
                    "purchase_rate": purchase_rate,
                    "sale_price": sale_price,
                    "batch_date": batch_date_common,
                }
            )
    else:
        product_id = request.form.get("product_id")
        quantity_raw = request.form.get("stock_quantity", "0").strip()
        purchase_rate_raw = request.form.get("purchase_rate", "0").strip()
        sale_price_raw = request.form.get("stock_sale_price", "0").strip()
        batch_date_raw = request.form.get("batch_date", "").strip()

        try:
            quantity = int(quantity_raw)
        except ValueError:
            quantity = -1

        purchase_rate = parse_float(purchase_rate_raw, "purchase rate")
        if purchase_rate is None:
            return _redirect_to_page("stock")
        sale_price = parse_float(sale_price_raw, "sale price")
        if sale_price is None:
            return _redirect_to_page("stock")

        if batch_date_raw:
            try:
                batch_date = datetime.strptime(batch_date_raw, "%Y-%m-%d").date().isoformat()
            except ValueError:
                flash("Enter a valid restock date.", "error")
                return _redirect_to_page("stock")
        else:
            batch_date = date.today().isoformat()

        if not product_id or quantity <= 0:
            flash("Select a product and enter a positive quantity.", "error")
            return _redirect_to_page("stock")

        entries.append(
            {
                "product_id": int(product_id),
                "quantity": quantity,
                "purchase_rate": purchase_rate,
                "sale_price": sale_price,
                "batch_date": batch_date,
            }
        )

    if not entries:
        flash("No restock data provided.", "error")
        return _redirect_to_page("stock")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    processed = []
    for entry in entries:
        if entry["quantity"] <= 0:
            flash("Quantity must be greater than zero.", "error")
            return _redirect_to_page("stock")
        product = Product.get_for_shop(db, shop["id"], entry["product_id"])
        if not product:
            flash("Invalid product selected.", "error")
            return _redirect_to_page("stock")
        Product.add_stock(db, product["id"], entry["quantity"], entry["sale_price"])
        StockBatch.create(
            db,
            shop["id"],
            product["id"],
            entry["quantity"],
            entry["purchase_rate"],
            entry["sale_price"],
            entry["batch_date"],
        )
        processed.append(product["name"])

    db.commit()
    if len(processed) == 1:
        flash(
            f"Restock recorded for {processed[0]} ({entries[0]['quantity']} units at PKR {entries[0]['purchase_rate']:.2f}).",
            "success",
        )
    else:
        flash(f"Restock recorded for {len(processed)} products.", "success")
    return _redirect_to_page("stock")


@manager_bp.route("/sales/record", methods=["POST"])
@manager_required
def record_sale():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
        (request.accept_mimetypes and request.accept_mimetypes.best == "application/json")

    def fail(message: str, code: int = 400):
        if is_ajax:
            return jsonify({"status": "failed", "error": message}), code
        flash(message, "error")
        return _redirect_to_page("sales")

    def parse_float(value_raw, label):
        try:
            value = float(value_raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            return None

    sale_type = request.form.get("sale_type", "sale")
    if sale_type != "sale":
        return fail("Direct return posting is disabled. Use the dedicated sale return flow.")

    product_ids = request.form.getlist("sale_product_id[]")
    quantities = request.form.getlist("sale_quantity[]")
    prices = request.form.getlist("sale_price[]")
    expense_flags = request.form.getlist("sale_expense[]")
    customer_id_raw = request.form.get("sale_customer_id")
    payment_method = request.form.get("sale_payment_method", "counter").strip().lower()

    if payment_method not in ("counter", "online"):
        return fail("Invalid payment method selected.")

    if not product_ids:
        return fail("Select at least one product to record a sale or return.")
    if not (len(product_ids) == len(quantities) == len(prices)):
        return fail("Missing sale fields for one of the products.")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    if expense_flags and len(expense_flags) != len(product_ids):
        return fail("Missing expense selection for one of the products.")

    if not expense_flags:
        expense_flags = ["0"] * len(product_ids)

    expense_percent = 0.0
    if sale_type == "sale":
        settings = ShopSettings.get_for_shop(db, shop["id"])
        if settings:
            expense_percent = float(settings["expense_percent"] or 0)

    entries = []
    customer_id = None
    if customer_id_raw:
        try:
            customer_id = int(customer_id_raw)
        except (TypeError, ValueError):
            customer_id = None
    for idx in range(len(product_ids)):
        try:
            pid = int(product_ids[idx])
        except (TypeError, ValueError):
            return fail("Invalid product selected.")
        try:
            quantity = int(quantities[idx])
        except (TypeError, ValueError):
            return fail("Enter a valid quantity.")
        if quantity <= 0:
            return fail("Quantity must be greater than zero.")
        product = Product.get_for_shop(db, shop["id"], pid)
        if not product:
            return fail("Product not found.")
        if sale_type == "sale" and product["quantity"] < quantity:
            return fail(f"Not enough stock for {product['name']}.")

        use_expense = sale_type == "sale" and expense_flags[idx] == "1"
        unit_cost = StockBatch.average_purchase_rate(db, shop["id"], pid)
        if use_expense:
            if unit_cost <= 0:
                return fail(f"Add a restock purchase price for {product['name']} before using expense pricing.")
            price = round(unit_cost * (1 + (expense_percent / 100)), 2)
        else:
            price = parse_float(prices[idx], "sale price")
            if price is None:
                return fail("Enter a valid sale price.")

        entries.append(
            {
                "product_id": pid,
                "quantity": quantity,
                "unit_price": price,
                "unit_cost": unit_cost,
                "product_name": product["name"],
            }
        )

    if customer_id:
        customer = Customer.get_for_shop(db, shop["id"], customer_id)
        if not customer:
            return fail("Selected customer not found.")

    try:
        sale_total_amount = 0.0
        for entry in entries:
            delta = -entry["quantity"] if sale_type == "sale" else entry["quantity"]
            Product.adjust_quantity(db, shop["id"], entry["product_id"], delta)
            sale_total_amount += entry["quantity"] * entry["unit_price"]
        sale_id = Sale.record(
            db,
            shop["id"],
            sale_type,
            [
                {
                    "product_id": e["product_id"],
                    "quantity": e["quantity"],
                    "unit_price": e["unit_price"],
                    "unit_cost": e.get("unit_cost", 0),
                }
                for e in entries
            ],
            payment_method=payment_method,
            customer_id=customer_id,
        )
        if sale_type == "sale" and sale_total_amount > 0:
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                round(sale_total_amount, 2),
                "add",
                f"Sale #{sale_id}",
                cash_bucket=payment_method,
            )
        db.commit()
        if is_ajax:
            return jsonify(
                {
                    "status": "ok",
                    "sale_id": sale_id,
                    "sale_type": sale_type,
                    "payment_method": payment_method,
                    "sale_total": round(sale_total_amount, 2),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "items": entries,
                }
            )
        flash(f"Recorded sale for {len(entries)} product(s).", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to record sale or return.")
        if is_ajax:
            return jsonify({"status": "failed", "error": "Failed to record sale/return."}), 500
        flash("Failed to record sale/return.", "error")

    return _redirect_to_page("sales")


@manager_bp.route("/sales/<int:sale_id>/cash-summary", methods=["GET"])
@manager_required
def sale_cash_summary(sale_id: int):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        return jsonify({"status": "failed", "error": "No shop assigned."}), 403

    summary = _build_sale_cash_summary(db, shop["id"], sale_id)
    if not summary:
        return jsonify({"status": "failed", "error": "Sale not found."}), 404

    return jsonify({"status": "ok", "sale": summary})


@manager_bp.route("/settings", methods=["GET", "POST"])
@manager_required
def settings_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    if request.method == "POST":
        raw_percent = request.form.get("expense_percent", "").strip()
        hide_sale_prices = request.form.get("hide_sale_prices") == "on"
        try:
            expense_percent = float(raw_percent)
            if expense_percent < 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid expense percentage.", "error")
            return redirect(url_for("manager.settings_page"))
        ShopSettings.set_values(db, shop["id"], expense_percent, hide_sale_prices)
        db.commit()
        flash("Settings updated.", "success")
        return redirect(url_for("manager.settings_page"))

    ctx = _build_manager_context(db, shop, "settings")
    return render_template("manager.html", **ctx)


@manager_bp.route("/wallet-history", methods=["GET"])
@manager_required
def wallet_history_page():
    return redirect(url_for("manager.cash_history_page"))


@manager_bp.route("/easyload-history", methods=["GET"])
@manager_required
def easyload_history_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    ctx = _build_manager_context(db, shop, "easyload_history")
    return render_template("manager.html", **ctx)


@manager_bp.route("/expense-history", methods=["GET"])
@manager_required
def cash_history_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    ctx = _build_manager_context(db, shop, "cash_history")
    return render_template("manager.html", **ctx)


@manager_bp.route("/cash-history/<day>", methods=["GET"])
@manager_required
def cash_history_detail_page(day: str):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    try:
        parsed_day = datetime.strptime(day, "%Y-%m-%d").date().isoformat()
    except ValueError:
        flash("Invalid cash history date.", "error")
        return redirect(url_for("manager.cash_history_page"))

    ctx = _build_manager_context(db, shop, "cash_history_detail")
    selected_day = _find_cash_history_day(ctx.get("cash_history", []), parsed_day)
    if not selected_day:
        flash("No cash history found for that date.", "error")
        return redirect(url_for("manager.cash_history_page"))

    ctx["cash_history_day"] = selected_day
    ctx["cash_history_day_breakdown"] = _build_cash_history_day_breakdown(selected_day)
    return render_template("manager.html", **ctx)


@manager_bp.route("/profit-history", methods=["GET"])
@manager_required
def profit_history_page():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    ctx = _build_manager_context(db, shop, "profit_history")
    return render_template("manager.html", **ctx)


@manager_bp.route("/profit-history/<day>", methods=["GET"])
@manager_required
def profit_history_detail_page(day: str):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned to this manager account.", "error")
        return redirect(url_for("auth.logout"))

    try:
        parsed_day = datetime.strptime(day, "%Y-%m-%d").date().isoformat()
    except ValueError:
        flash("Invalid profit history date.", "error")
        return redirect(url_for("manager.profit_history_page"))

    ctx = _build_manager_context(db, shop, "profit_history_detail")
    selected_day = _find_cash_history_day(ctx.get("profit_history", []), parsed_day)
    if not selected_day:
        flash("No profit history found for that date.", "error")
        return redirect(url_for("manager.profit_history_page"))

    ctx["profit_history_day"] = selected_day
    return render_template("manager.html", **ctx)


@manager_bp.route("/finance/record", methods=["POST"])
@manager_required
def record_finance_transaction():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    mode = request.form.get("mode", "").strip().lower()
    category = request.form.get("category", "").strip().lower()
    network = request.form.get("network", "").strip().lower()
    amount_raw = request.form.get("amount", "").strip()
    note = request.form.get("note", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.dashboard")

    def _redirect_with_state():
        separator = "&" if "?" in return_url else "?"
        category_part = category or "easypaisa"
        network_part = network or "zong"
        return redirect(
            f"{return_url}{separator}finance_modal={mode or 'cash_in'}&finance_category={category_part}&finance_network={network_part}"
        )

    if mode not in ("cash_in", "out"):
        flash("Invalid finance action selected.", "error")
        return _redirect_with_state()

    if category in ServiceTransaction.WALLET_CHANNELS:
        channel = category
        entry_type = "cash_in" if mode == "cash_in" else "cash_out"
    elif category == "easyload":
        if network not in ServiceTransaction.EASYLOAD_CHANNELS:
            flash("Select a valid easyload network.", "error")
            return _redirect_with_state()
        channel = network
        entry_type = "purchase_in" if mode == "cash_in" else "out"
    else:
        flash("Select a valid cash category.", "error")
        return _redirect_with_state()

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid amount greater than zero.", "error")
        return _redirect_with_state()

    channel_label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
    is_wallet_cash_in = entry_type == "cash_in" and channel in ServiceTransaction.WALLET_CHANNELS
    is_easyload_purchase_in = entry_type == "purchase_in" and channel in ServiceTransaction.EASYLOAD_CHANNELS
    if is_wallet_cash_in and not note:
        note = f"Cash transferred from counter to {channel_label}"
    if is_easyload_purchase_in and not note:
        note = f"Cash transferred from counter to {channel_label} easyload"

    if not note:
        flash("Message is required.", "error")
        return _redirect_with_state()

    counter_cash_balance = SystemCashEntry.total_for_shop(db, shop["id"])
    if entry_type in ("cash_in", "purchase_in"):
        if amount > counter_cash_balance:
            flash("Counter cash is not enough for this transfer.", "error")
            return _redirect_with_state()

    if entry_type in ("cash_out", "out"):
        current_balance = ServiceTransaction.current_balance(db, shop["id"], channel)
        if amount > current_balance:
            flash("Out amount is greater than the available balance.", "error")
            return _redirect_with_state()

    try:
        ServiceTransaction.add_entry(
            db,
            shop["id"],
            channel,
            entry_type,
            amount,
            note=note,
        )
        if entry_type == "cash_in":
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                amount,
                entry_type="expense",
                expense_name=note if is_wallet_cash_in else f"Transferred to {channel_label}: {note}",
            )
        elif entry_type == "purchase_in":
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                amount,
                entry_type="expense",
                expense_name=note if is_easyload_purchase_in else f"Purchased {channel_label} load: {note}",
            )
        db.commit()
        label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
        action_label = ServiceTransaction.ENTRY_LABELS.get(entry_type, entry_type.title())
        if entry_type == "purchase_in":
            profit_amount = ServiceTransaction.calculate_easyload_profit(channel, amount)
            flash(
                f"{label} {action_label.lower()} saved. Counter cash reduced by PKR {amount:.2f}; network credited PKR {amount + profit_amount:.2f}.",
                "success",
            )
        elif entry_type == "cash_in":
            flash(
                f"{label} cash in saved. Counter cash reduced by PKR {amount:.2f}.",
                "success",
            )
        else:
            flash(f"{label} {action_label.lower()} saved successfully.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to save finance transaction.")
        flash("Failed to save transaction.", "error")
        return _redirect_with_state()

    return redirect(return_url)


@manager_bp.route("/wallet-balances/refresh", methods=["POST"])
@manager_required
def refresh_wallet_balances():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.dashboard")

    actual_balances = {}
    for channel in ServiceTransaction.WALLET_CHANNELS:
        raw_value = request.form.get(f"{channel}_balance", "").strip()
        try:
            actual_balance = float(raw_value)
            if actual_balance < 0:
                raise ValueError
        except ValueError:
            flash("Enter valid Easypaisa and JazzCash balances.", "error")
            return redirect(return_url)
        actual_balances[channel] = round(actual_balance, 2)

    service_totals = ServiceTransaction.totals_by_channel(db, shop["id"])
    adjustments = []
    for channel, actual_balance in actual_balances.items():
        current_balance = round(float(service_totals.get(channel, {}).get("cash_balance_total", 0.0)), 2)
        difference = round(actual_balance - current_balance, 2)
        if abs(difference) < 0.01:
            continue
        entry_type = "cash_in" if difference > 0 else "cash_out"
        adjustments.append((channel, entry_type, abs(difference), difference, current_balance, actual_balance))

    if not adjustments:
        flash("Wallet balances already match the entered amounts.", "success")
        return redirect(return_url)

    try:
        for channel, entry_type, amount, _difference, current_balance, actual_balance in adjustments:
            channel_label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
            ServiceTransaction.add_entry(
                db,
                shop["id"],
                channel,
                entry_type,
                amount,
                note=f"Wallet balance updated: system PKR {current_balance:.2f}, actual PKR {actual_balance:.2f}",
            )
            if entry_type == "cash_out":
                sold_note = _build_wallet_refresh_sale_note(channel_label, current_balance, actual_balance)
                SystemCashEntry.add_entry(
                    db,
                    shop["id"],
                    amount,
                    entry_type="add",
                    expense_name=sold_note,
                )
                profit_amount = ServiceTransaction.calculate_wallet_profit(channel, amount)
                if profit_amount > 0:
                    ServiceTransaction.add_entry(
                        db,
                        shop["id"],
                        channel,
                        "profit_in",
                        profit_amount,
                        note=ServiceTransaction.build_profit_note(
                            f"Wallet refresh profit from {channel_label}: sold PKR {amount:.2f}",
                            destination="counter",
                        ),
                    )
                    SystemCashEntry.add_entry(
                        db,
                        shop["id"],
                        profit_amount,
                        entry_type="add",
                        expense_name=f"Wallet profit moved from {channel_label}: Wallet refresh profit on PKR {amount:.2f}",
                    )
        db.commit()
        parts = []
        for channel, adjustment_entry_type, adjustment_amount, difference, _current_balance, _actual_balance in adjustments:
            label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
            sign = "+" if difference > 0 else "-"
            part = f"{label} {sign}PKR {abs(difference):.2f}"
            if adjustment_entry_type == "cash_out":
                profit_amount = ServiceTransaction.calculate_wallet_profit(channel, adjustment_amount)
                if profit_amount > 0:
                    part = f"{part} -> counter PKR {adjustment_amount:.2f} + profit PKR {profit_amount:.2f}"
            parts.append(part)
        flash(f"Wallet balances refreshed: {', '.join(parts)}.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to refresh wallet balances.")
        flash("Failed to refresh wallet balances.", "error")

    return redirect(return_url)


@manager_bp.route("/easyload-balances/refresh", methods=["POST"])
@manager_required
def refresh_easyload_balances():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.dashboard")

    actual_balances = {}
    for channel in ServiceTransaction.EASYLOAD_CHANNELS:
        raw_value = request.form.get(f"{channel}_balance", "").strip()
        try:
            actual_balance = float(raw_value)
            if actual_balance < 0:
                raise ValueError
        except ValueError:
            flash("Enter valid Easyload balances.", "error")
            return redirect(return_url)
        actual_balances[channel] = round(actual_balance, 2)

    service_totals = ServiceTransaction.totals_by_channel(db, shop["id"])
    adjustments = []
    for channel, actual_balance in actual_balances.items():
        current_balance = round(float(service_totals.get(channel, {}).get("balance_total", 0.0)), 2)
        difference = round(actual_balance - current_balance, 2)
        if abs(difference) < 0.01:
            continue
        entry_type = "adjust_in" if difference > 0 else "out"
        adjustments.append((channel, entry_type, abs(difference), difference, current_balance, actual_balance))

    if not adjustments:
        flash("Easyload balances already match the entered amounts.", "success")
        return redirect(return_url)

    try:
        for channel, entry_type, amount, _difference, current_balance, actual_balance in adjustments:
            channel_label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
            if entry_type == "adjust_in":
                ServiceTransaction.add_entry(
                    db,
                    shop["id"],
                    channel,
                    entry_type,
                    amount,
                    note=f"Easyload balance updated: system PKR {current_balance:.2f}, actual PKR {actual_balance:.2f}",
                )
            else:
                ServiceTransaction.add_entry(
                    db,
                    shop["id"],
                    channel,
                    entry_type,
                    amount,
                    note=f"Easyload balance updated: system PKR {current_balance:.2f}, actual PKR {actual_balance:.2f}",
                )
                SystemCashEntry.add_entry(
                    db,
                    shop["id"],
                    amount,
                    entry_type="add",
                    expense_name=_build_easyload_refresh_sale_note(channel_label, current_balance, actual_balance),
                )
        db.commit()
        parts = []
        for channel, adjustment_entry_type, adjustment_amount, difference, _current_balance, _actual_balance in adjustments:
            label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
            sign = "+" if difference > 0 else "-"
            part = f"{label} {sign}PKR {abs(difference):.2f}"
            if adjustment_entry_type == "out":
                part = f"{part} -> counter PKR {adjustment_amount:.2f}"
            parts.append(part)
        flash(f"Easyload balances refreshed: {', '.join(parts)}.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to refresh Easyload balances.")
        flash("Failed to refresh Easyload balances.", "error")

    return redirect(return_url)


@manager_bp.route("/profits/add", methods=["POST"])
@manager_required
def add_wallet_profit():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    channel = request.form.get("channel", "").strip().lower()
    entry_type = request.form.get("entry_type", "").strip().lower()
    destination = request.form.get("destination", "wallet").strip().lower()
    amount_raw = request.form.get("amount", "").strip()
    note = request.form.get("note", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()

    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.settings_page")
    channel_label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())

    if channel not in ServiceTransaction.WALLET_CHANNELS:
        flash("Invalid wallet channel selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=easypaisa")
    if entry_type != "profit_in":
        flash("Invalid wallet profit action selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")
    if destination not in ("wallet", "counter"):
        flash("Invalid wallet profit destination selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid profit amount greater than zero.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")
    try:
        ServiceTransaction.add_entry(
            db,
            shop["id"],
            channel,
            entry_type,
            amount,
            note=ServiceTransaction.build_profit_note(note, destination=destination),
        )
        if destination == "counter":
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                amount,
                entry_type="add",
                expense_name=f"Wallet profit moved from {ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())}: {(note or 'Profit transfer').strip()}",
            )
        db.commit()
        if destination == "counter":
            flash(f"{channel_label} profit added to counter cash successfully.", "success")
        else:
            action = ServiceTransaction.ENTRY_LABELS.get(entry_type, entry_type.title())
            flash(f"{channel_label} {action.lower()} saved successfully.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to save wallet profit entry.")
        flash("Failed to save wallet profit entry.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    return redirect(return_url)


@manager_bp.route("/easyload/add", methods=["POST"])
@manager_required
def add_easyload_entry():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    channel = request.form.get("channel", "").strip().lower()
    entry_type = request.form.get("entry_type", "").strip().lower()
    load_amount_raw = request.form.get("load_amount", "").strip()
    note = request.form.get("note", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.easyload_history_page")

    if channel not in ServiceTransaction.EASYLOAD_CHANNELS:
        flash("Invalid easyload network selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=zong")
    if entry_type not in ("purchase_in", "out"):
        flash("Invalid easyload action selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    try:
        load_amount = float(load_amount_raw)
        if load_amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid easyload amount greater than zero.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    channel_label = ServiceTransaction.DISPLAY_NAMES.get(channel, channel.title())
    is_easyload_purchase_in = entry_type == "purchase_in"
    if is_easyload_purchase_in and not note:
        note = f"Cash transferred from counter to {channel_label} easyload"

    if not note:
        flash("Message is required for easyload transactions.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    counter_cash_balance = SystemCashEntry.total_for_shop(db, shop["id"])
    if entry_type == "purchase_in" and load_amount > counter_cash_balance:
        flash("Counter cash is not enough for this purchase.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    if entry_type == "out":
        current_balance = ServiceTransaction.current_balance(db, shop["id"], channel)
        if load_amount > current_balance:
            flash("Out amount is greater than the available easyload balance.", "error")
            separator = "&" if "?" in return_url else "?"
            return redirect(f"{return_url}{separator}profit_modal={channel}")

    profit_amount = ServiceTransaction.calculate_easyload_profit(channel, load_amount) if entry_type == "purchase_in" else 0.0

    try:
        ServiceTransaction.add_entry(
            db,
            shop["id"],
            channel,
            entry_type,
            load_amount,
            note=note,
        )
        if entry_type == "purchase_in":
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                load_amount,
                entry_type="expense",
                expense_name=note if is_easyload_purchase_in else f"Purchased {channel_label} load: {note}",
            )
        db.commit()
        label = channel_label
        action = ServiceTransaction.ENTRY_LABELS.get(entry_type, entry_type.title())
        if entry_type == "purchase_in":
            flash(
                f"{label} {action.lower()} saved. Counter cash reduced by PKR {load_amount:.2f}; network credited PKR {load_amount + profit_amount:.2f}.",
                "success",
            )
        else:
            flash(f"{label} out saved. Amount PKR {load_amount:.2f}.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to save easyload entry.")
        flash("Failed to save easyload entry.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal={channel}")

    return redirect(return_url)



@manager_bp.route("/system-cash/transfer", methods=["POST"])
@manager_required
def transfer_cash():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    amount_raw = request.form.get("amount", "").strip()
    source = request.form.get("source", "").strip().lower()
    target = request.form.get("target", "").strip().lower()
    note = request.form.get("note", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.dashboard")

    CASH_BUCKETS = ("counter", "online")
    WALLET_CHANNELS = ServiceTransaction.WALLET_CHANNELS  # e.g. ("easypaisa", "jazzcash")
    ALL_SOURCES = list(CASH_BUCKETS) + list(WALLET_CHANNELS)

    SOURCE_LABELS = {
        "counter": "Counter Cash",
        "online": "Online Cash",
        "easypaisa": "Easypaisa Wallet",
        "jazzcash": "JazzCash Wallet",
    }

    def _err(msg):
        flash(msg, "error")
        return redirect(return_url)

    if source not in ALL_SOURCES:
        return _err("Invalid transfer source selected.")
    if target not in ALL_SOURCES:
        return _err("Invalid transfer destination selected.")
    if source == target:
        return _err("Source and destination cannot be the same.")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return _err("Enter a valid transfer amount greater than zero.")

    if not note:
        note = f"Transfer from {SOURCE_LABELS.get(source, source)} to {SOURCE_LABELS.get(target, target)}"

    # --- Check source balance ---
    if source in CASH_BUCKETS:
        src_balance = SystemCashEntry.total_for_shop(db, shop["id"], cash_bucket=source)
    else:
        src_balance = ServiceTransaction.current_balance(db, shop["id"], source)

    if amount > src_balance:
        return _err(
            f"Insufficient balance. {SOURCE_LABELS.get(source, source)} only has PKR {src_balance:.2f}."
        )

    try:
        # --- Deduct from source ---
        if source in CASH_BUCKETS:
            SystemCashEntry.add_entry(
                db, shop["id"], amount,
                entry_type="expense",
                expense_name=note,
                cash_bucket=source,
            )
        else:
            ServiceTransaction.add_entry(
                db, shop["id"], source, "cash_out", amount, note=note
            )

        # --- Credit to target ---
        if target in CASH_BUCKETS:
            SystemCashEntry.add_entry(
                db, shop["id"], amount,
                entry_type="add",
                expense_name=note,
                cash_bucket=target,
            )
        else:
            ServiceTransaction.add_entry(
                db, shop["id"], target, "cash_in", amount, note=note
            )

        db.commit()
        flash(
            f"PKR {amount:.2f} transferred from {SOURCE_LABELS.get(source, source)} to {SOURCE_LABELS.get(target, target)} successfully.",
            "success",
        )
    except (ValueError, Exception) as e:
        db.rollback()
        current_app.logger.exception("Failed to transfer cash.")
        flash("Transfer failed. Please try again.", "error")

    return redirect(return_url)


@manager_bp.route("/system-cash/add", methods=["POST"])
@manager_required
def add_system_cash():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    amount_raw = request.form.get("amount", "").strip()
    entry_type = request.form.get("entry_type", "add").strip().lower()
    expense_name = request.form.get("expense_name", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.settings_page")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid cash amount greater than zero.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=system")

    if entry_type not in SystemCashEntry.VALID_ENTRY_TYPES:
        flash("Invalid cash action selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=system")
    if not expense_name:
        flash("Message is required for cash in and cash out.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=system")

    try:
        SystemCashEntry.add_entry(
            db,
            shop["id"],
            amount,
            entry_type=entry_type,
            expense_name=expense_name,
        )
        db.commit()
        if entry_type == "expense":
            flash("Cash out recorded and deducted from counter cash.", "success")
        else:
            flash("Cash in added to counter cash.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to add counter cash entry.")
        flash("Failed to add counter cash.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=system")

    return redirect(return_url)


@manager_bp.route("/package-profit/add", methods=["POST"])
@manager_required
def add_package_profit():
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    amount_raw = request.form.get("amount", "").strip()
    entry_type = request.form.get("entry_type", "profit_in").strip().lower()
    cash_bucket = request.form.get("cash_bucket", "counter").strip().lower()
    note = request.form.get("note", "").strip()
    return_url_raw = request.form.get("return_url", "").strip()
    return_url = _safe_manager_return_url(return_url_raw) or url_for("manager.settings_page")

    if entry_type not in ("profit_in", "profit_out"):
        flash("Invalid package profit action selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=package")

    if cash_bucket not in ("counter", "online"):
        flash("Invalid cash bucket selected.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=package")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid package profit amount greater than zero.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=package")

    if not note:
        flash("Message is required for package profit entries.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=package")

    system_entry_type = "add" if entry_type == "profit_in" else "expense"
    try:
        SystemCashEntry.add_entry(
            db,
            shop["id"],
            amount,
            entry_type=system_entry_type,
            expense_name=_build_package_profit_note(note),
            cash_bucket=cash_bucket,
        )
        db.commit()
        if entry_type == "profit_in":
            if cash_bucket == "online":
                flash("Package profit added to online cash successfully.", "success")
            else:
                flash("Package profit added to counter cash successfully.", "success")
        else:
            if cash_bucket == "online":
                flash("Package profit out recorded and deducted from online cash.", "success")
            else:
                flash("Package profit out recorded and deducted from counter cash.", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to save package profit entry.")
        flash("Failed to save package profit entry.", "error")
        separator = "&" if "?" in return_url else "?"
        return redirect(f"{return_url}{separator}profit_modal=package")

    return redirect(return_url)


@manager_bp.route("/sales/<int:sale_id>/return", methods=["GET", "POST"])
@manager_required
def sale_return(sale_id: int):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
        (request.accept_mimetypes and request.accept_mimetypes.best == "application/json")
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        if is_ajax:
            return jsonify({"status": "failed", "error": "No shop assigned"}), 403
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    def _safe_return_url(raw: str | None):
        if not raw:
            return None
        raw = raw.strip()
        if raw.startswith("/"):
            return raw
        return None

    if request.method == "GET":
        try:
            sale_id = int(sale_id)
        except (TypeError, ValueError):
            flash("Invalid sale reference.", "error")
            return _redirect_to_page("sales")

        sale, sale_items = Sale.get_with_items(db, shop["id"], sale_id)
        if not sale:
            flash("Sale not found.", "error")
            return _redirect_to_page("sales")
        if sale["sale_type"] != "sale":
            flash("Only sales can be returned.", "error")
            return _redirect_to_page("sales")

        return_items = [item for item in sale_items if item["remaining_quantity"] > 0]
        raw_preselect = request.args.get("return_item_id")
        preselect_item_id = None
        if raw_preselect:
            try:
                candidate = int(raw_preselect)
            except (TypeError, ValueError):
                candidate = None
            if candidate and any(item["id"] == candidate for item in return_items):
                preselect_item_id = candidate

        return_to = _safe_return_url(request.args.get("return_to"))
        back_url = return_to or url_for("manager.sales_page")
        return render_template(
            "sale_return.html",
            shop=shop,
            sale=sale,
            return_items=return_items,
            preselect_item_id=preselect_item_id,
            return_to=return_to,
            back_url=back_url,
        )

    try:
        sale_id = int(sale_id)
    except (TypeError, ValueError):
        flash("Invalid sale reference.", "error")
        return _redirect_to_page("sales")

    sale, sale_items = Sale.get_with_items(db, shop["id"], sale_id)
    if not sale:
        flash("Sale not found.", "error")
        return _redirect_to_page("sales")
    if sale["sale_type"] != "sale":
        flash("Only sales can be returned.", "error")
        return _redirect_to_page("sales")

    posted_ids = request.form.getlist("return_sale_item_id[]")
    posted_qty = request.form.getlist("return_quantity[]")
    if not posted_ids or not (len(posted_ids) == len(posted_qty)):
        flash("Return form incomplete.", "error")
        return _redirect_to_page("sales")

    sale_item_lookup = {str(item["id"]): item for item in sale_items}
    entries = []
    for idx in range(len(posted_ids)):
        item_id = posted_ids[idx]
        sale_item = sale_item_lookup.get(item_id)
        if not sale_item:
            flash("Invalid sale item selected.", "error")
            return _redirect_to_page("sales")
        available_to_return = sale_item["quantity"] - (sale_item.get("returned_quantity") or 0)
        if available_to_return <= 0:
            flash("This product has already been fully returned.", "error")
            return _redirect_to_page("sales")
        try:
            qty = int(posted_qty[idx])
        except (TypeError, ValueError):
            flash("Enter a valid quantity.", "error")
            return _redirect_to_page("sales")
        if qty <= 0 or qty > available_to_return:
            flash("Return quantity must be between 1 and the sold amount.", "error")
            return _redirect_to_page("sales")
        entries.append(
            {
                "product_id": sale_item["product_id"],
                "quantity": qty,
                "unit_price": float(sale_item["unit_price"] or 0),
                "unit_cost": float(sale_item.get("unit_cost") or 0),
                "product_name": sale_item["product_name"],
                "sale_item_id": sale_item["id"],
            }
        )

    if not entries:
        flash("Nothing selected to return.", "error")
        return _redirect_to_page("sales")

    try:
        processed_items = []
        return_total_amount = 0.0
        for entry in entries:
            Product.adjust_quantity(db, shop["id"], entry["product_id"], entry["quantity"])
            return_total_amount += entry["quantity"] * entry["unit_price"]
            processed_items.append(
                {
                    "product_id": entry["product_id"],
                    "quantity": entry["quantity"],
                    "unit_price": entry["unit_price"],
                    "unit_cost": entry.get("unit_cost", 0),
                }
            )
        Sale.record(
            db,
            shop["id"],
            "return",
            processed_items,
            payment_method=(sale["payment_method"] or "counter"),
            customer_id=sale["customer_id"],
            reference_sale_id=sale["id"],
        )
        if return_total_amount > 0:
            SystemCashEntry.add_entry(
                db,
                shop["id"],
                round(return_total_amount, 2),
                entry_type="expense",
                expense_name=f"Sale Restored #{sale['id']}",
                cash_bucket=(sale["payment_method"] or "counter"),
            )
        for entry in entries:
            sale_item = sale_item_lookup.get(str(entry["sale_item_id"]))
            current_returned = sale_item.get("returned_quantity") or 0
            total_returned = current_returned + entry["quantity"]
            if total_returned >= sale_item["quantity"]:
                db.execute(
                    "UPDATE sale_items SET returned_quantity = ?, returned_at = datetime('now') WHERE id = ?",
                    (sale_item["quantity"], entry["sale_item_id"]),
                )
            else:
                db.execute(
                    "UPDATE sale_items SET returned_quantity = ?, returned_at = NULL WHERE id = ?",
                    (total_returned, entry["sale_item_id"]),
                )
        db.commit()
        flash(f"Recorded return for {len(entries)} product(s).", "success")
    except sqlite3.DatabaseError:
        db.rollback()
        current_app.logger.exception("Failed to record sale return.")
        flash("Failed to record return.", "error")

    return_to = _safe_return_url(request.form.get("return_to"))
    if return_to:
        return redirect(return_to)
    return _redirect_to_page("sales")


@manager_bp.route("/brands/create", methods=["POST"])
@manager_required
def create_brand():
    name = request.form.get("brand_name", "").strip()
    if not name:
        flash("Brand name is required.", "error")
        return _redirect_to_page("brands")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    try:
        Brand.create(db, shop["id"], name)
        db.commit()
        flash("Brand added.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Brand already exists for this shop.", "error")

    return _redirect_to_page("brands")


@manager_bp.route("/brands/update", methods=["POST"])
@manager_required
def update_brand():
    brand_id = request.form.get("brand_id")
    name = request.form.get("brand_new_name", "").strip()

    try:
        brand_id = int(brand_id)
    except (TypeError, ValueError):
        flash("Invalid brand.", "error")
        return _redirect_to_page("brands")

    if not name:
        flash("Brand name is required.", "error")
        return _redirect_to_page("brands")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    brand = Brand.get_by_id(db, shop["id"], brand_id)
    if not brand:
        flash("Brand not found.", "error")
        return _redirect_to_page("brands")

    try:
        Brand.update(db, shop["id"], brand_id, name)
        db.commit()
        flash("Brand updated.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Another brand already uses that name.", "error")

    return _redirect_to_page("brands")


@manager_bp.route("/products/update", methods=["POST"])
@manager_required
def update_product():
    product_id = request.form.get("edit_product_id")
    name = request.form.get("edit_product_name", "").strip()
    brand_id_raw = request.form.get("edit_product_brand_id")
    category_id_raw = request.form.get("edit_product_category_id")
    reorder_level_raw = request.form.get("edit_product_reorder_level", "3")
    return_to = request.form.get("return_to", "").strip().lower()

    def _redirect_after():
        if return_to.startswith("brand:"):
            try:
                brand_id = int(return_to.split(":", 1)[1])
            except (TypeError, ValueError, IndexError):
                return _redirect_to_page("products")
            return redirect(url_for("manager.brand_detail", brand_id=brand_id))
        if return_to.startswith("category:"):
            try:
                category_id = int(return_to.split(":", 1)[1])
            except (TypeError, ValueError, IndexError):
                return _redirect_to_page("products")
            return redirect(url_for("manager.category_detail", category_id=category_id))
        return _redirect_to_page("products")

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        flash("Invalid product.", "error")
        return _redirect_after()

    if not name:
        flash("Product name is required.", "error")
        return _redirect_after()

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    brand_id = None
    if brand_id_raw:
        try:
            brand_id = int(brand_id_raw)
        except ValueError:
            brand_id = None
    if brand_id:
        brand = Brand.get_by_id(db, shop["id"], brand_id)
        if not brand:
            flash("Brand not found.", "error")
            return _redirect_after()

    category_id = None
    if category_id_raw:
        try:
            category_id = int(category_id_raw)
        except ValueError:
            category_id = None
    if category_id:
        category = Category.get_by_id(db, shop["id"], category_id)
        if not category:
            flash("Category not found.", "error")
            return _redirect_after()

    product = Product.get_for_shop(db, shop["id"], product_id)
    if not product:
        flash("Product not found.", "error")
        return _redirect_after()

    try:
        reorder_level = int(reorder_level_raw)
        if reorder_level < 0:
            raise ValueError
    except (TypeError, ValueError):
        flash("Enter a valid minimum stock level (0 or above).", "error")
        return _redirect_after()

    current_price = product["price"]

    try:
        Product.update(
            db,
            shop["id"],
            product_id,
            name=name,
            price=current_price,
            brand_id=brand_id if brand_id is not None else product["brand_id"],
            category_id=category_id if category_id is not None else product["category_id"],
            reorder_level=reorder_level,
        )
        db.commit()
        flash("Product updated.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("SKU already exists.", "error")

    return _redirect_after()


@manager_bp.route("/products/delete", methods=["POST"])
@manager_required
def delete_product():
    product_id = request.form.get("delete_product_id")

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        flash("Invalid product.", "error")
        return _redirect_to_page("products")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    product = Product.get_for_shop(db, shop["id"], product_id)
    if not product:
        flash("Product not found.", "error")
        return _redirect_to_page("products")

    has_sales_history = db.execute(
        """
        SELECT 1
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        WHERE si.product_id = ? AND s.shop_id = ?
        LIMIT 1;
        """,
        (product_id, shop["id"]),
    ).fetchone()
    has_stock_history = db.execute(
        """
        SELECT 1
        FROM stock_batches
        WHERE product_id = ? AND shop_id = ?
        LIMIT 1;
        """,
        (product_id, shop["id"]),
    ).fetchone()
    if has_sales_history or has_stock_history:
        flash(
            "This product cannot be deleted because it has sales or restock history. "
            "Keep it for records instead of deleting it.",
            "error",
        )
        return _redirect_to_page("products")
    if int(product["quantity"] or 0) > 0:
        flash("This product still has stock. Reduce stock to zero before deleting it.", "error")
        return _redirect_to_page("products")

    Product.delete(db, shop["id"], product_id)
    db.commit()
    flash(f"Removed {product['name']}.", "success")
    return _redirect_to_page("products")


@manager_bp.route("/brands/<int:brand_id>", methods=["GET"])
@manager_required
def brand_detail(brand_id: int):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    try:
        brand_id = int(brand_id)
    except (TypeError, ValueError):
        flash("Invalid brand.", "error")
        return _redirect_to_page("brands")

    brand = Brand.get_by_id(db, shop["id"], brand_id)
    if not brand:
        flash("Brand not found.", "error")
        return _redirect_to_page("brands")

    products = Product.all_by_shop(db, shop["id"])
    brand_products = [p for p in products if p["brand_id"] == brand_id]
    categories = Category.all_by_shop(db, shop["id"])
    brands = Brand.all_by_shop(db, shop["id"])

    return render_template(
        "brand_detail.html",
        shop=shop,
        brand=brand,
        products=brand_products,
        categories=categories,
        brands=brands,
    )


@manager_bp.route("/stock_batches/<batch_date>", methods=["GET"])
@manager_required
def stock_batch_detail(batch_date: str):
    try:
        parsed_date = datetime.strptime(batch_date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        flash("Invalid restock date.", "error")
        return _redirect_to_page("stock")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    entries = StockBatch.by_date(db, shop["id"], parsed_date)
    if not entries:
        flash("No restock records found for that date.", "error")
        return _redirect_to_page("stock")

    total_purchase = sum(e["purchase_rate"] * e["quantity"] for e in entries)
    total_sale = sum(e["sale_price"] * e["quantity"] for e in entries)
    restock_groups = {}
    for entry in entries:
        created_at = entry["created_at"] or ""
        local_created = parse_utc_to_local(created_at)
        key = local_created.strftime("%Y-%m-%d %H:%M") if local_created else created_at
        group = restock_groups.setdefault(
            key,
            {
                "created_at": created_at,
                "entries": [],
                "total_items": 0,
                "total_purchase": 0.0,
            },
        )
        group["entries"].append(entry)
        group["total_items"] += 1
        group["total_purchase"] += entry["purchase_rate"] * entry["quantity"]

    restock_runs = list(restock_groups.values())
    restock_runs.sort(key=lambda item: item["created_at"], reverse=True)

    return render_template(
        "stock_batch_detail.html",
        shop=shop,
        batch_date=parsed_date,
        entries=entries,
        total_purchase=total_purchase,
        total_sale=total_sale,
        restock_runs=restock_runs,
    )


@manager_bp.route("/products/<int:product_id>/purchases", methods=["GET"])
@manager_required
def product_purchases(product_id: int):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        flash("Invalid product.", "error")
        return _redirect_to_page("products")

    product = Product.get_for_shop(db, shop["id"], product_id)
    if not product:
        flash("Product not found.", "error")
        return _redirect_to_page("products")

    entries = StockBatch.by_product(db, shop["id"], product_id)
    total_quantity = sum(entry["quantity"] for entry in entries)
    total_spend = sum(entry["quantity"] * entry["purchase_rate"] for entry in entries)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
        (request.accept_mimetypes and request.accept_mimetypes.best == "application/json")
    if is_ajax:
        return jsonify({
            "status": "success",
            "product": {
                "id": product["id"],
                "name": product["name"],
                "quantity": product["quantity"],
                "brand_name": product["brand_name"],
                "category_name": product["category_name"]
            },
            "entries": [{
                "batch_date": entry["batch_date"],
                "quantity": entry["quantity"],
                "purchase_rate": entry["purchase_rate"],
                "sale_price": entry["sale_price"]
            } for entry in entries],
            "total_quantity": total_quantity,
            "total_spend": total_spend
        })

    return render_template(
        "product_purchases.html",
        shop=shop,
        product=product,
        entries=entries,
        total_quantity=total_quantity,
        total_spend=total_spend,
    )


@manager_bp.route("/categories/<int:category_id>", methods=["GET"])
@manager_required
def category_detail(category_id: int):
    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        flash("Invalid category.", "error")
        return _redirect_to_page("categories")

    category = Category.get_by_id(db, shop["id"], category_id)
    if not category:
        flash("Category not found.", "error")
        return _redirect_to_page("categories")

    products = Product.all_by_shop(db, shop["id"])
    category_products = [p for p in products if p["category_id"] == category_id]
    brands = Brand.all_by_shop(db, shop["id"])
    categories = Category.all_by_shop(db, shop["id"])

    return render_template(
        "category_detail.html",
        shop=shop,
        category=category,
        products=category_products,
        brands=brands,
        categories=categories,
    )


@manager_bp.route("/categories/create", methods=["POST"])
@manager_required
def create_category():
    name = request.form.get("category_name", "").strip()
    if not name:
        flash("Category name is required.", "error")
        return _redirect_to_page("categories")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    try:
        Category.create(db, shop["id"], name)
        db.commit()
        flash("Category added.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Category already exists for this shop.", "error")

    return _redirect_to_page("categories")


@manager_bp.route("/categories/update", methods=["POST"])
@manager_required
def update_category():
    category_id = request.form.get("category_id")
    name = request.form.get("category_new_name", "").strip()

    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        flash("Invalid category.", "error")
        return _redirect_to_page("categories")

    if not name:
        flash("Category name is required.", "error")
        return _redirect_to_page("categories")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    category = Category.get_by_id(db, shop["id"], category_id)
    if not category:
        flash("Category not found.", "error")
        return _redirect_to_page("categories")

    try:
        Category.update(db, shop["id"], category_id, name)
        db.commit()
        flash("Category updated.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Another category already uses that name.", "error")

    return _redirect_to_page("categories")


@manager_bp.route("/sales/reports/<report_date>", methods=["GET"])
@manager_required
def sales_report_detail(report_date: str):
    try:
        parsed_date = datetime.strptime(report_date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        flash("Invalid report date.", "error")
        return _redirect_to_page("reports")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    report_sales = Sale.by_date_with_items(db, shop["id"], parsed_date, parsed_date)
    summary = Sale.daily_summary(db, shop["id"], parsed_date, parsed_date)
    summary_entry = summary[0] if summary else {
        "sale_date": parsed_date,
        "sales_total": 0.0,
        "returns_total": 0.0,
        "sale_count": 0,
        "return_count": 0,
        "sold_items": 0,
        "returned_items": 0,
    }

    return render_template(
        "sales_report_detail.html",
        shop=shop,
        report_date=parsed_date,
        summary=summary_entry,
        report_sales=report_sales,
    )


@manager_bp.route("/customers/create", methods=["POST"])
@manager_required
def create_customer():
    name = request.form.get("customer_name", "").strip()
    phone = request.form.get("customer_phone", "").strip()
    return_to = request.form.get("return_to", "").strip().lower()
    if return_to not in ("sales", "customers"):
        return_to = "customers"

    def _redirect_after(customer_id: int | None = None):
        if return_to == "sales":
            if customer_id:
                return redirect(url_for("manager.sales_page", customer_id=customer_id))
            return redirect(url_for("manager.sales_page"))
        return _redirect_to_page("customers")

    if not name:
        flash("Customer name is required.", "error")
        return _redirect_after()

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    created_customer_id = None
    try:
        created_customer_id = Customer.create(db, shop["id"], name, phone if phone else None)
        db.commit()
        flash("Customer added.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Customer already exists.", "error")
        existing = Customer.get_by_name(db, shop["id"], name)
        if return_to == "sales" and existing:
            return redirect(url_for("manager.sales_page", customer_id=existing["id"]))

    return _redirect_after(created_customer_id)


@manager_bp.route("/customers/delete", methods=["POST"])
@manager_required
def delete_customer():
    customer_id = request.form.get("customer_id")

    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        flash("Invalid customer.", "error")
        return _redirect_to_page("customers")

    db = get_db()
    shop = _get_manager_shop(db)
    if not shop:
        flash("No shop assigned.", "error")
        return redirect(url_for("auth.logout"))

    customer = Customer.get_for_shop(db, shop["id"], customer_id)
    if not customer:
        flash("Customer not found.", "error")
        return _redirect_to_page("customers")

    Customer.delete(db, shop["id"], customer_id)
    db.commit()
    flash(f"Removed customer {customer['name']}.", "success")
    return _redirect_to_page("customers")
