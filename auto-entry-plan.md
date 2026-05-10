# Auto Entry Plan – Ezzystore Shop Ahmedabad Rawalpindi

## Goal
Auto-register all categories, brands, and products for the shop named **"Ezzystore Shop Ahmedabad Rawalpindi."** directly in the SQLite database.

## Approach (what I will do)
1. **Resolve shop_id**
   - Query `shops` to find the row with name exactly: `Ezzystore Shop Ahmedabad Rawalpindi.`
   - Store its `id` as `shop_id` and use it for all inserts.

2. **Load source data**
   - Parse your stock list (e.g., `C:\Users\Sarjeel\Desktop\Stock List Updated.xlsx`) to get rows with `Category`, `Brand`, and `Product`.
   - Normalize whitespace and remove empty rows.

3. **Upsert Categories**
   - For each unique category name:
     - If a row already exists for this `shop_id` + category name, reuse it.
     - Otherwise, insert into `categories` and capture the new `id`.

4. **Upsert Brands**
   - For each unique brand name:
     - If a row already exists for this `shop_id` + brand name, reuse it.
     - Otherwise, insert into `brands` and capture the new `id`.

5. **Insert Products**
   - For each product row (Category + Brand + Product):
     - Resolve `category_id` and `brand_id` from the maps above.
     - Check if a product with the same name already exists for this `shop_id` (optionally also match category/brand if that is how you want duplicates handled).
     - If missing, insert into `products` with `shop_id`, `category_id`, `brand_id`, and `name`.

6. **Safety & Integrity**
   - Wrap the operation in a single SQL transaction to avoid partial inserts.
   - Enforce foreign keys (`PRAGMA foreign_keys = ON`).
   - Produce a summary of how many categories, brands, and products were created vs. already existed.

## What I need from you before I run it
- Confirm the source file path (or provide a different file).
- Confirm if product duplicate checking should be by **product name only** or by **(product name + category + brand)**.
- Confirm whether you want me to **skip** or **insert** blank purchase rate / qty fields (currently they are empty in the sheet).

## Output
- I will print:
  - `shop_id` used
  - counts of new/existing categories, brands, and products
  - any rows that were skipped due to missing category/brand/product

---
If you approve, I will proceed with the auto-entry script and insert everything into the database for that shop.
