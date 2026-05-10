from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .db import get_db
from .models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def home():
    if session.get("role") == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = User.authenticate(db, username, password)

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["username"] = user["username"]

            if user["role"] == "admin":
                return redirect(url_for("admin.dashboard"))

            if user["role"] == "manager":
                shop = get_db().execute("""
                    SELECT s.id, s.name
                    FROM shops s
                    JOIN shop_managers sm ON sm.shop_id = s.id
                    WHERE sm.manager_user_id = ?
                    LIMIT 1;
                """, (user["id"],)).fetchone()

                if not shop:
                    session.clear()
                    flash("This manager account is not assigned to any shop yet.", "error")
                    return redirect(url_for("auth.login"))

                session["shop_id"] = shop["id"]
                session["shop_name"] = shop["name"]
                return redirect(url_for("manager.dashboard"))

        flash("Invalid username or password", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
