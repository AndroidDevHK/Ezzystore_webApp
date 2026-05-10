from .user import User
from .brand import Brand
from .category import Category
from .product import Product
from .stock_batch import StockBatch
from .sale import Sale
from .customer import Customer
from .shop_settings import ShopSettings
from .wallet_profit import WalletProfit
from .system_cash_entry import SystemCashEntry
from .service_transaction import ServiceTransaction

def init_models(db):
    User.create_table(db)

    db.execute("""
    CREATE TABLE IF NOT EXISTS shops (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      name        TEXT NOT NULL UNIQUE,
      created_by  INTEGER NOT NULL,
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # One shop -> one manager (UNIQUE shop_id)
    db.execute("""
    CREATE TABLE IF NOT EXISTS shop_managers (
      shop_id          INTEGER PRIMARY KEY,
      manager_user_id  INTEGER NOT NULL UNIQUE,
      created_by       INTEGER NOT NULL,
      created_at       TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (shop_id)         REFERENCES shops(id) ON DELETE CASCADE,
      FOREIGN KEY (manager_user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (created_by)      REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    Brand.create_table(db)
    Category.create_table(db)
    Product.create_table(db)
    StockBatch.create_table(db)
    Customer.create_table(db)
    Sale.create_table(db)
    ShopSettings.create_table(db)
    WalletProfit.create_table(db)
    SystemCashEntry.create_table(db)
    ServiceTransaction.create_table(db)

    User.ensure_default_admin(db)
