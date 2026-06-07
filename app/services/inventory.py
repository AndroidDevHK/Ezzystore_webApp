# Inventory Service
from app.models.product import Product
from app.models.brand import Brand
from app.models.category import Category

class InventoryService:
    @staticmethod
    def get_full_inventory(db, shop_id: int):
        """Returns products, brands, categories, and stock summaries for a shop."""
        products = Product.all_by_shop(db, shop_id)
        brands = Brand.get_by_shop(db, shop_id)
        categories = Category.get_by_shop(db, shop_id)
        
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

        return {
            "products": products,
            "brands": brands,
            "categories": categories,
            "total_products": total_products,
            "total_stock": total_stock,
            "out_of_stock": out_of_stock,
            "category_counts": category_counts,
            "brand_counts": brand_counts
        }
