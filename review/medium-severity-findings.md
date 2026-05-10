# Medium-Severity Findings And Risk Notes

These items were reviewed after the high-severity fixes and are now tracked with their current implementation status.

## 1. Profit and expense calculations use only the latest purchase batch

- Status: Fixed
- Evidence:
  - [app/models/sale.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/sale.py:40)
  - [app/models/stock_batch.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/stock_batch.py:87)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:80)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1421)
- Original problem:
  - Profit reporting used the latest stock batch purchase rate instead of a stable cost captured at sale time.
  - Expense-mode selling also depended on the latest batch only.
- Fix applied:
  - Added `unit_cost` storage on each `sale_items` row.
  - Sale recording now stores a product cost with the transaction.
  - Profit summaries now use stored `unit_cost` instead of recalculating from the latest batch.
  - Added weighted-average purchase-rate support for sale-time cost selection.
  - Added a legacy backfill so older sale items get a non-zero `unit_cost` estimate.

## 2. Easyload refresh positive adjustments can overshoot the real balance

- Status: Fixed
- Evidence:
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1852)
  - [app/models/service_transaction.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/service_transaction.py:11)
  - [app/models/service_transaction.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/service_transaction.py:138)
- Original problem:
  - Positive Easyload refresh differences were recorded as `purchase_in`, which added commission again and overshot the actual balance.
- Fix applied:
  - Added neutral adjustment entry types.
  - Easyload refresh positive reconciliation now uses exact-balance adjustment logic instead of commission-generating purchase logic.

## 3. Schema migration failures are silently swallowed

- Status: Fixed
- Evidence:
  - [app/models/product.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/product.py:8)
  - [app/models/stock_batch.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/stock_batch.py:3)
  - [app/models/system_cash_entry.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/system_cash_entry.py:5)
  - [app/models/sale.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/models/sale.py:5)
- Original problem:
  - Several tables used `ALTER TABLE` inside broad `try/except` blocks that silently ignored real migration failures.
- Fix applied:
  - Replaced the silent migration pattern in the reviewed models with explicit schema inspection using `PRAGMA table_info(...)`.
  - Columns are now added only when actually missing.

## 4. Broad `except Exception` blocks hide root causes during write operations

- Status: Fixed
- Evidence:
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1479)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1742)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:1840)
  - [app/manager/routes.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/app/manager/routes.py:2367)
- Original problem:
  - Write paths caught `Exception` broadly and returned generic UI errors, which hid the real failure cause.
- Fix applied:
  - Added structured exception logging.
  - Narrowed the reviewed transactional catches to `sqlite3.DatabaseError` instead of generic `Exception`.

## 5. There is no automated test coverage visible in the repository

- Status: Fixed
- Evidence:
  - [tests/test_regressions.py](D:/Hasnat%20WorkSpace/EzzyStore_WebApp/tests/test_regressions.py)
- Original problem:
  - There was no visible automated regression coverage for the highest-risk flows.
- Fix applied:
  - Added regression tests covering:
    - admin bootstrap safety
    - product deletion protection
    - stored sale cost / profit behavior
    - direct return rejection
    - tampered return price protection
    - exact Easyload refresh reconciliation
