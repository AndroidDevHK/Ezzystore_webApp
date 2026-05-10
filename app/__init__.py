from flask import Flask

from .admin.routes import admin_bp
from .auth import auth_bp
from .config import Config
from .db import close_db, get_db
from .manager.routes import manager_bp
from .models import init_models
from .time_utils import parse_utc_to_local


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DB + tables + default admin once, at startup.
    with app.app_context():
        db = get_db()
        init_models(db)
        db.commit()

    app.teardown_appcontext(close_db)

    @app.template_filter("human_datetime")
    def human_datetime(value, fmt="%d-%b-%Y - %I:%M %p"):
        dt = parse_utc_to_local(value)
        if not dt:
            return value or "-"
        return dt.strftime(fmt)

    @app.template_filter("human_date")
    def human_date(value, fmt="%d-%b-%Y"):
        dt = parse_utc_to_local(value)
        if not dt:
            return value or "-"
        return dt.strftime(fmt)

    @app.template_filter("human_time")
    def human_time(value, fmt="%I:%M %p"):
        dt = parse_utc_to_local(value)
        if not dt:
            return value or "-"
        return dt.strftime(fmt)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(manager_bp, url_prefix="/manager")

    return app
