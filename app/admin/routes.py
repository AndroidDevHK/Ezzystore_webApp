import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from ..db import get_db
from ..models.user import User

admin_bp = Blueprint("admin", __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route("/", methods=["GET"])
@admin_required
def dashboard():
    db = get_db()

    shops = db.execute("""
        SELECT s.id, s.name, s.created_at,
               u.full_name AS manager_name, u.username AS manager_username
        FROM shops s
        LEFT JOIN shop_managers sm ON sm.shop_id = s.id
        LEFT JOIN users u ON u.id = sm.manager_user_id
        ORDER BY s.id DESC;
    """).fetchall()

    total_shops = len(shops)
    assigned_shops = sum(1 for s in shops if s["manager_name"])
    pending_shops = total_shops - assigned_shops

    return render_template(
        "admin.html",
        shops=shops,
        total_shops=total_shops,
        assigned_shops=assigned_shops,
        pending_shops=pending_shops,
    )

@admin_bp.route("/create_shop", methods=["POST"])
@admin_required
def create_shop():
    name = request.form.get("shop_name", "").strip()
    if not name:
        flash("Shop name is required", "error")
        return redirect(url_for("admin.dashboard"))

    db = get_db()
    try:
        db.execute("INSERT INTO shops (name, created_by) VALUES (?, ?);", (name, session["user_id"]))
        db.commit()
        flash("Shop created successfully", "success")
    except sqlite3.IntegrityError:
        flash("Shop name already exists", "error")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/create_manager_for_shop", methods=["POST"])
@admin_required
def create_manager_for_shop():
    shop_id = request.form.get("shop_id")
    full_name = request.form.get("manager_full_name", "").strip()
    username = request.form.get("manager_username", "").strip()
    password = request.form.get("manager_password", "")

    if not shop_id or not full_name or not username or not password:
        flash("All fields are required", "error")
        return redirect(url_for("admin.dashboard"))

    db = get_db()
    try:
        # create manager user
        manager_user_id = User.create_manager(db, full_name, username, password)

        # assign manager to shop (ONE manager per shop)
        db.execute("""
            INSERT INTO shop_managers (shop_id, manager_user_id, created_by)
            VALUES (?, ?, ?);
        """, (int(shop_id), manager_user_id, session["user_id"]))

        db.commit()
        flash("Manager created & assigned to shop", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Username already exists OR this shop already has a manager", "error")

    return redirect(url_for("admin.dashboard"))
