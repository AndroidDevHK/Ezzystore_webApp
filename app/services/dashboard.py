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
from ..models.customer_ledger import CustomerLedger
from ..models.shop_settings import ShopSettings
from ..models.wallet_profit import WalletProfit
from ..models.system_cash_entry import SystemCashEntry
from ..models.service_transaction import ServiceTransaction
from ..time_utils import parse_utc_to_local

PACKAGE_PROFIT_MARKER = "[package_profit]"


from flask import request

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


def _build_refresh_sale_note(service_type: str, channel_label: str, system_balance: float, actual_balance: float):
    return (
        f"{service_type} refresh sold amount from {channel_label}: "
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
                "balance_due": CustomerLedger.get_balance(db, shop["id"], customer["id"]),
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

