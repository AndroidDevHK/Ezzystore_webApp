# High-Severity Findings

This review focuses on behavioral bugs, security risks, and data-integrity problems that can materially affect production use.

## 1. Hardcoded secret key and seeded default admin credentials

- Status: Fixed
- Evidence:
  - [app/config.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/config.py:5)
  - [app/models/user.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/user.py:27)
  - [app/models/user.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/user.py:33)
  - [README.md](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/README.md:3)
- Original problem:
  - The Flask `SECRET_KEY` was fixed in source, which made session signing predictable across deployments.
  - The app auto-created an `admin/admin123` account when no admin existed, and the README exposed that password.
- Fix applied:
  - `SECRET_KEY` now comes from environment or a generated random fallback at runtime.
  - Default hardcoded admin credentials were removed.
  - First-admin bootstrap now only happens when `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` are explicitly set.
  - The README was updated to document the safer bootstrap flow.

## 2. Deleting a product also deletes historical sales and stock records

- Status: Fixed
- Evidence:
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2558)
  - [app/models/product.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/product.py:89)
  - [app/models/sale.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/sale.py:42)
  - [app/models/stock_batch.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/stock_batch.py:15)
- Original problem:
  - `products` were deleted directly.
  - `sale_items.product_id` and `stock_batches.product_id` both use `ON DELETE CASCADE`.
  - Deleting one product could erase purchase history, sale history, return history, and reporting inputs.
- Fix applied:
  - Product deletion is now blocked if the product has sale history or stock-batch history.
  - Deletion is also blocked while stock remains above zero.
  - This prevents accidental audit-history loss without redesigning the whole product lifecycle yet.

## 3. Customer return amounts can be tampered with from the browser

- Status: Fixed
- Evidence:
  - [app/templates/sale_return.html](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/templates/sale_return.html:95)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2288)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2312)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2353)
- Original problem:
  - The return form posted `return_price[]` as a hidden client-side field.
  - The server trusted that posted value to compute the refund.
- Fix applied:
  - The hidden client-side refund price field was removed from the return form.
  - The server now always uses the original sale item `unit_price` from stored data when computing return cash.

## 4. Two competing return paths create inconsistent accounting

- Status: Fixed
- Evidence:
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1362)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1364)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2347)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2353)
- Original problem:
  - `record_sale()` accepted `sale_type="return"`.
  - That path adjusted stock but did not reliably reverse counter cash or link the original sale the way the dedicated return route did.
- Fix applied:
  - Direct return posting through `record_sale()` is now rejected.
  - Returns must go through the dedicated `/sales/<id>/return` flow, which handles reference linking and counter-cash reversal consistently.

## 5. `sale_return()` references `is_ajax` before it is defined

- Status: Fixed
- Evidence:
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2212)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2218)
- Original problem:
  - Inside `sale_return()`, the `"no shop assigned"` branch checked `is_ajax` before it had been initialized.
- Fix applied:
  - `is_ajax` is now defined at the top of `sale_return()` before any conditional branch uses it.
