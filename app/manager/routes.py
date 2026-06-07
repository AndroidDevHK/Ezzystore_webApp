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
from ..models.customer_ledger import CustomerLedger
from ..time_utils import parse_utc_to_local

manager_bp = Blueprint("manager", __name__)


def _redirect_to_page(page_name):
    page_map = {
        "overview": "dashboard",
        "products": "product_management_page",
        "stock": "stock_page",
        "sales": "sales_page",
        "reports": "reports_page",
        "daily_report": "daily_report_page",
        "customers": "customers_page",
        "brands": "brands_page",
        "categories": "categories_page",
        "settings": "settings_page",
        "cash_history": "cash_history_page",
        "profit_history": "profit_history_page",
        "easyload_history": "easyload_history_page"
    }
    endpoint = page_map.get(page_name)
    if endpoint:
        return redirect(url_for(f"manager.{endpoint}"))
    return redirect(url_for("manager.dashboard", page=page_name))

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


from ..services.dashboard import _build_manager_context, _safe_manager_return_url, _build_package_profit_note, _build_refresh_sale_note, _find_cash_history_day, _build_cash_history_day_breakdown


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
    pending_amount = parse_float(request.form.get("pending_amount", "0"), "pending_amount") or 0.0

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
            cash_received = sale_total_amount - pending_amount
            if cash_received > 0:
                SystemCashEntry.add_entry(
                    db,
                    shop["id"],
                    round(cash_received, 2),
                    "add",
                    f"Sale #{sale_id}" + (f" (Pending: {pending_amount})" if pending_amount > 0 else ""),
                    cash_bucket=payment_method,
                )
            if pending_amount > 0 and customer_id:
                CustomerLedger.record_pending_amount(
                    db, shop["id"], customer_id, sale_id, pending_amount
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
                sold_note = _build_refresh_sale_note('Wallet', channel_label, current_balance, actual_balance)
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
                    expense_name=_build_refresh_sale_note('Easyload', channel_label, current_balance, actual_balance),
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

@manager_bp.route("/customer/add", methods=["POST"])
@manager_required
def add_customer():
    db = get_db()
    shop = _get_manager_shop(db)
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    
    if not name:
        flash("Customer name is required.", "error")
        return redirect(url_for("manager.dashboard", page="customers"))
        
    try:
        Customer.create(db, shop["id"], name, phone)
        db.commit()
        flash("Customer added successfully.", "success")
    except Exception as e:
        db.rollback()
        flash("Customer with this name already exists or invalid data.", "error")
        
    return redirect(url_for("manager.dashboard", page="customers"))

@manager_bp.route("/customer/<int:customer_id>/pay", methods=["POST"])
@manager_required
def pay_customer_debt(customer_id):
    db = get_db()
    shop = _get_manager_shop(db)
    
    amount = request.form.get("amount", "0").strip()
    note = request.form.get("note", "Debt Payment").strip()
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Invalid payment amount.", "error")
        return redirect(url_for("manager.dashboard", page="customers"))
        
    # Check if customer exists
    customer = Customer.get_for_shop(db, shop["id"], customer_id)
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("manager.dashboard", page="customers"))
        
    CustomerLedger.record_payment(db, shop["id"], customer_id, amount, note)
    
    # Add to system cash because we received money
    SystemCashEntry.add_entry(
        db, shop["id"], amount, "add", f"Debt payment from {customer['name']}"
    )
    
    db.commit()
    flash("Payment recorded successfully.", "success")
    return redirect(url_for("manager.dashboard", page="customers"))

@manager_bp.route("/api/customer/<int:customer_id>/history", methods=["GET"])
@manager_required
def get_customer_history(customer_id):
    db = get_db()
    shop = _get_manager_shop(db)
    
    history = CustomerLedger.get_history(db, shop["id"], customer_id)
    return jsonify({"status": "success", "history": history})


@manager_bp.route("/api/sales/<int:sale_id>/items", methods=["GET"])
@manager_required
def api_sale_items(sale_id):
    db = get_db()
    shop = _get_manager_shop(db)
    sale, sale_items = Sale.get_with_items(db, shop["id"], sale_id)
    if not sale:
        return jsonify({"status": "failed", "error": "Sale not found"}), 404
    
    # Get current balance for customer if applicable
    current_balance = 0.0
    if sale["customer_id"]:
        current_balance = CustomerLedger.get_balance(db, shop["id"], sale["customer_id"])

    return_items = []
    for item in sale_items:
        if item["remaining_quantity"] > 0:
            return_items.append({
                "id": item["id"],
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "remaining_quantity": item["remaining_quantity"]
            })
            
    return jsonify({
        "status": "success",
        "sale_id": sale_id,
        "customer_id": sale["customer_id"],
        "customer_name": sale["customer_name"],
        "current_balance": current_balance,
        "items": return_items
    })


@manager_bp.route("/api/sales/return/record", methods=["POST"])
@manager_required
def api_record_sale_return():
    db = get_db()
    shop = _get_manager_shop(db)
    
    sale_id_raw = request.form.get("sale_id")
    try:
        sale_id = int(sale_id_raw)
    except (TypeError, ValueError):
        return jsonify({"status": "failed", "error": "Invalid sale reference"}), 400

    sale, sale_items = Sale.get_with_items(db, shop["id"], sale_id)
    if not sale or sale["sale_type"] != "sale":
        return jsonify({"status": "failed", "error": "Invalid sale"}), 400

    item_ids = request.form.getlist("return_sale_item_id[]")
    return_qtys = request.form.getlist("return_quantity[]")
    
    if not item_ids or len(item_ids) != len(return_qtys):
        return jsonify({"status": "failed", "error": "Invalid items submitted"}), 400

    revised_pending_amount = request.form.get("revised_pending_amount", "")
    cash_refunded = request.form.get("cash_refunded", "")
    
    try:
        revised_pending_amount = float(revised_pending_amount) if revised_pending_amount else 0.0
        cash_refunded = float(cash_refunded) if cash_refunded else 0.0
    except ValueError:
        return jsonify({"status": "failed", "error": "Invalid financial amounts"}), 400

    # Validate items and quantities
    return_entries = []
    for idx in range(len(item_ids)):
        try:
            item_id = int(item_ids[idx])
            qty = int(return_qtys[idx])
        except ValueError:
            return jsonify({"status": "failed", "error": "Invalid quantity"}), 400
            
        original_item = next((i for i in sale_items if i["id"] == item_id), None)
        if not original_item:
            return jsonify({"status": "failed", "error": "Item not found in sale"}), 400
            
        if qty <= 0 or qty > original_item["remaining_quantity"]:
            return jsonify({"status": "failed", "error": f"Invalid return quantity for {original_item['product_name']}"}), 400
            
        return_entries.append({
            "product_id": original_item["product_id"],
            "quantity": qty,
            "unit_price": original_item["unit_price"],
            "unit_cost": original_item["unit_cost"],
            "sale_item_id": original_item["id"]
        })

    if not return_entries:
        return jsonify({"status": "failed", "error": "No items selected to return"}), 400

    try:
        # Create return sale record
        return_sale_id = Sale.record(
            db,
            shop["id"],
            "return",
            return_entries,
            payment_method=sale["payment_method"],
            customer_id=sale["customer_id"],
            reference_sale_id=sale["id"],
        )

        for entry in return_entries:
            # Update returned quantity in original sale
            db.execute(
                "UPDATE sale_items SET returned_quantity = returned_quantity + ?, returned_at = datetime('now') WHERE id = ?",
                (entry["quantity"], entry["sale_item_id"])
            )
            # Add stock back
            Product.adjust_quantity(db, shop["id"], entry["product_id"], entry["quantity"])

        # Handle financials
        if sale["customer_id"]:
            current_balance = CustomerLedger.get_balance(db, shop["id"], sale["customer_id"])
            adjustment = current_balance - revised_pending_amount
            
            if adjustment > 0:
                # Debt reduced by adjustment (Treat as if they paid)
                CustomerLedger.record_payment(db, shop["id"], sale["customer_id"], adjustment, f"Debt offset by Return #{return_sale_id}")
            elif adjustment < 0:
                # Debt increased
                CustomerLedger.record_pending_amount(db, shop["id"], sale["customer_id"], return_sale_id, abs(adjustment))
                
        if cash_refunded > 0:
            SystemCashEntry.add_entry(
                db, shop["id"], cash_refunded, "remove", f"Cash refund for Return #{return_sale_id}", cash_bucket=sale["payment_method"]
            )

        db.commit()
        return jsonify({"status": "success", "message": "Sale returned successfully."})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "failed", "error": str(e)}), 500
