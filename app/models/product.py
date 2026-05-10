class Product:
    @staticmethod
    def _column_names(db, table_name: str):
        return {
            row["name"]
            for row in db.execute(f"PRAGMA table_info({table_name});").fetchall()
        }

    @staticmethod
    def create_table(db):
        db.execute("""
        CREATE TABLE IF NOT EXISTS products (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          shop_id     INTEGER NOT NULL,
          brand_id    INTEGER,
          category_id INTEGER,
          name        TEXT NOT NULL,
          price       REAL NOT NULL DEFAULT 0 CHECK(price >= 0),
          quantity    INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
          reorder_level INTEGER NOT NULL DEFAULT 3 CHECK(reorder_level >= 0),
          created_at  TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (shop_id)     REFERENCES shops(id) ON DELETE CASCADE,
          FOREIGN KEY (brand_id)    REFERENCES brands(id) ON DELETE SET NULL,
          FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
          UNIQUE(shop_id, name)
        );
        """)

        columns = Product._column_names(db, "products")
        if "brand_id" not in columns:
            db.execute("ALTER TABLE products ADD COLUMN brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL;")
        if "category_id" not in columns:
            db.execute("ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL;")
        if "price" not in columns:
            db.execute("ALTER TABLE products ADD COLUMN price REAL NOT NULL DEFAULT 0;")
        if "quantity" not in columns:
            db.execute("ALTER TABLE products ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0;")
        if "reorder_level" not in columns:
            db.execute("ALTER TABLE products ADD COLUMN reorder_level INTEGER NOT NULL DEFAULT 3;")

    @staticmethod
    def create(db, shop_id: int, name: str, price: float, brand_id=None, category_id=None, reorder_level: int = 3):
        db.execute("""
            INSERT INTO products (shop_id, brand_id, category_id, name, price, reorder_level)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (shop_id, brand_id, category_id, name.strip(), price, reorder_level))

    @staticmethod
    def update(db, shop_id: int, product_id: int, *, name: str, price: float, brand_id=None, category_id=None, reorder_level: int | None = None):
        db.execute("""
            UPDATE products
            SET name=?, price=?, brand_id=?, category_id=?, reorder_level=COALESCE(?, reorder_level)
            WHERE id=? AND shop_id=?;
        """, (name.strip(), price, brand_id, category_id, reorder_level, product_id, shop_id))

    @staticmethod
    def add_stock(db, product_id: int, quantity: int, price: float | None = None):
        if price is not None:
            db.execute("""
                UPDATE products
                SET quantity = quantity + ?, price=?
                WHERE id = ?;
            """, (quantity, price, product_id))
        else:
            db.execute("""
                UPDATE products
                SET quantity = quantity + ?
                WHERE id = ?;
            """, (quantity, product_id))

    @staticmethod
    def all_by_shop(db, shop_id: int):
        return db.execute("""
            SELECT p.*, b.name AS brand_name, c.name AS category_name
            FROM products p
            LEFT JOIN brands b ON b.id = p.brand_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.shop_id = ?
            ORDER BY p.id DESC;
        """, (shop_id,)).fetchall()

    @staticmethod
    def get_for_shop(db, shop_id: int, product_id: int):
        return db.execute("""
            SELECT p.*, b.name AS brand_name, c.name AS category_name
            FROM products p
            LEFT JOIN brands b ON b.id = p.brand_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.shop_id=? AND p.id=?
            LIMIT 1;
        """, (shop_id, product_id)).fetchone()

    @staticmethod
    def delete(db, shop_id: int, product_id: int):
        db.execute("""
            DELETE FROM products
            WHERE id=? AND shop_id=?;
        """, (product_id, shop_id))

    @staticmethod
    def adjust_quantity(db, shop_id: int, product_id: int, delta: int):
        db.execute("""
            UPDATE products
            SET quantity = quantity + ?
            WHERE id=? AND shop_id=?;
        """, (delta, product_id, shop_id))
