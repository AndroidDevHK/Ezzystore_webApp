import os
import shutil
import tempfile
import unittest

from app import create_app
from app.db import close_db, get_db
from app.models import init_models
from app.models.product import Product
from app.models.sale import Sale
from app.models.service_transaction import ServiceTransaction
from app.models.stock_batch import StockBatch
from app.models.user import User


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir_path = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir_path, "test.db")
        self.old_db_path = getattr(__import__("app.config", fromlist=["Config"]).Config, "DB_PATH")
        self.old_secret = os.environ.get("SECRET_KEY")
        self.old_admin_user = os.environ.get("INITIAL_ADMIN_USERNAME")
        self.old_admin_pass = os.environ.get("INITIAL_ADMIN_PASSWORD")
        self.old_admin_name = os.environ.get("INITIAL_ADMIN_FULL_NAME")

        os.environ["SECRET_KEY"] = "test-secret-key"
        os.environ.pop("INITIAL_ADMIN_USERNAME", None)
        os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        os.environ.pop("INITIAL_ADMIN_FULL_NAME", None)

        config_module = __import__("app.config", fromlist=["Config"])
        config_module.Config.DB_PATH = self.db_path
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO users (role, full_name, username, password_hash) VALUES ('admin', 'Admin', 'admin_local', 'x');"
            )
            self.manager_user_id = User.create_manager(db, "Manager", "manager_local", "pass123")
            db.execute("INSERT INTO shops (name, created_by) VALUES (?, ?);", ("Test Shop", 1))
            self.shop_id = db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
            db.execute(
                "INSERT INTO shop_managers (shop_id, manager_user_id, created_by) VALUES (?, ?, ?);",
                (self.shop_id, self.manager_user_id, 1),
            )
            db.commit()

    def tearDown(self):
        config_module = __import__("app.config", fromlist=["Config"])
        config_module.Config.DB_PATH = self.old_db_path
        with self.app.app_context():
            close_db()
        self.client = None
        shutil.rmtree(self.temp_dir_path, ignore_errors=True)

        if self.old_secret is None:
            os.environ.pop("SECRET_KEY", None)
        else:
            os.environ["SECRET_KEY"] = self.old_secret
        if self.old_admin_user is None:
            os.environ.pop("INITIAL_ADMIN_USERNAME", None)
        else:
            os.environ["INITIAL_ADMIN_USERNAME"] = self.old_admin_user
        if self.old_admin_pass is None:
            os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
        else:
            os.environ["INITIAL_ADMIN_PASSWORD"] = self.old_admin_pass
        if self.old_admin_name is None:
            os.environ.pop("INITIAL_ADMIN_FULL_NAME", None)
        else:
            os.environ["INITIAL_ADMIN_FULL_NAME"] = self.old_admin_name

    def _login_manager_session(self):
        with self.client.session_transaction() as session:
            session["user_id"] = self.manager_user_id
            session["role"] = "manager"
            session["username"] = "manager_local"
            session["shop_id"] = self.shop_id
            session["shop_name"] = "Test Shop"

    def test_initial_admin_is_not_created_without_bootstrap_env(self):
        temp_db = os.path.join(self.temp_dir_path, "bootstrap.db")
        import sqlite3

        db = sqlite3.connect(temp_db)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
        init_models(db)
        count = db.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin';").fetchone()["c"]
        db.close()
        self.assertEqual(count, 0)

    def test_product_delete_is_blocked_when_history_exists(self):
        self._login_manager_session()
        with self.app.app_context():
            db = get_db()
            Product.create(db, self.shop_id, "History Product", 0.0, None, None, 3)
            product_id = db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
            StockBatch.create(db, self.shop_id, product_id, 5, 100.0, 130.0, "2026-01-01")
            Product.add_stock(db, product_id, 5, 130.0)
            db.commit()

        response = self.client.post(
            "/manager/products/delete",
            data={"delete_product_id": str(product_id)},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            db = get_db()
            product = Product.get_for_shop(db, self.shop_id, product_id)
            self.assertIsNotNone(product)

    def test_sale_records_store_unit_cost_and_profit_uses_it(self):
        with self.app.app_context():
            db = get_db()
            Product.create(db, self.shop_id, "Average Cost Product", 0.0, None, None, 3)
            product_id = db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
            StockBatch.create(db, self.shop_id, product_id, 10, 100.0, 150.0, "2026-01-01")
            StockBatch.create(db, self.shop_id, product_id, 10, 200.0, 250.0, "2026-01-02")
            Product.add_stock(db, product_id, 20, 250.0)
            sale_id = Sale.record(
                db,
                self.shop_id,
                "sale",
                [{"product_id": product_id, "quantity": 2, "unit_price": 300.0, "unit_cost": 150.0}],
            )
            db.commit()

            from app.manager.routes import _build_sale_cash_summary

            summary = _build_sale_cash_summary(db, self.shop_id, sale_id)
            sale, items = Sale.get_with_items(db, self.shop_id, sale_id)

        self.assertEqual(float(items[0]["unit_cost"]), 150.0)
        self.assertEqual(round(float(summary["purchase_total"]), 2), 300.0)
        self.assertEqual(round(float(summary["profit"]), 2), 300.0)

    def test_direct_return_post_is_rejected(self):
        self._login_manager_session()
        with self.app.app_context():
            db = get_db()
            Product.create(db, self.shop_id, "Direct Return Product", 0.0, None, None, 3)
            product_id = db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
            Product.add_stock(db, product_id, 4, 100.0)
            db.commit()

        response = self.client.post(
            "/manager/sales/record",
            data={
                "sale_type": "return",
                "sale_product_id[]": [str(product_id)],
                "sale_quantity[]": ["1"],
                "sale_price[]": ["100"],
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            db = get_db()
            count = db.execute("SELECT COUNT(*) AS c FROM sales WHERE sale_type='return';").fetchone()["c"]
        self.assertEqual(count, 0)

    def test_tampered_return_price_is_ignored(self):
        self._login_manager_session()
        with self.app.app_context():
            db = get_db()
            Product.create(db, self.shop_id, "Return Product", 0.0, None, None, 3)
            product_id = db.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
            Product.add_stock(db, product_id, 5, 100.0)
            sale_id = Sale.record(
                db,
                self.shop_id,
                "sale",
                [{"product_id": product_id, "quantity": 2, "unit_price": 150.0, "unit_cost": 90.0}],
            )
            sale_item_id = db.execute("SELECT id FROM sale_items WHERE sale_id = ?;", (sale_id,)).fetchone()["id"]
            db.commit()

        response = self.client.post(
            f"/manager/sales/{sale_id}/return",
            data={
                "return_sale_item_id[]": [str(sale_item_id)],
                "return_quantity[]": ["1"],
                "return_price[]": ["9999"],
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            db = get_db()
            counter_total = db.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN entry_type='expense' THEN -amount ELSE amount END), 0) AS total
                FROM system_cash_entries
                WHERE shop_id = ?;
                """,
                (self.shop_id,),
            ).fetchone()["total"]
        self.assertEqual(round(float(counter_total), 2), -150.0)

    def test_easyload_refresh_positive_adjustment_matches_exact_balance(self):
        self._login_manager_session()
        with self.app.app_context():
            db = get_db()
            ServiceTransaction.add_entry(db, self.shop_id, "zong", "purchase_in", 1000.0, note="Initial load")
            db.commit()

        response = self.client.post(
            "/manager/easyload-balances/refresh",
            data={
                "zong_balance": "1500",
                "jazz_balance": "0",
                "ufone_balance": "0",
                "telenor_balance": "0",
                "return_url": "/manager/",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            db = get_db()
            balance = ServiceTransaction.current_balance(db, self.shop_id, "zong")
        self.assertEqual(round(balance, 2), 1500.0)


if __name__ == "__main__":
    unittest.main()
