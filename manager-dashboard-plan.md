# Manager Dashboard Navigation Refactor Plan

Goal: Convert the manager experience into separate pages per module (overview, products, stock, sales, reports, customers, brands, categories) with navigation between them, replacing the single-page/section layout.

## Current state (for reference)
- Layout: `manager.html` currently holds all modules/sections in one template; data for all modules is prepared in `manager/routes.py`.
- Styling: `app/static/css/manager.css` defines the manager shell, cards, grids, and section styles.
- Behavior: Inline JS handles in-page interactions (filters, modals) and previously toggled sections on the same page.

## Plan
1) Audit and map dependencies
   - Identify current section content, forms, modals, and JS behaviors in `manager.html` and data context from `manager/routes.py`.
   - Note shared components and POST targets that need to stay consistent across pages.
2) Design navigation + page structure
   - Define per-module routes (e.g., `/manager/overview`, `/manager/products`, `/manager/stock`, `/manager/sales`, `/manager/reports`, `/manager/customers`, `/manager/brands`, `/manager/categories`) plus a landing page with module cards linking out.
   - Decide shared layout elements (header with shop info, quick stats/nav links) reused on every page.
3) Split templates and wire routes
   - Extract each module into its own template (reuse partials for modals/alerts) and update `manager/routes.py` to fetch/render data per page.
   - Update navigation links/buttons to route between pages; ensure POST actions redirect back to the correct module page.
4) Update styling/assets
   - Add shared layout styles for the new header/nav and module pages; remove obsolete section-toggling styles.
   - Keep mobile responsiveness intact across pages.
5) Regression pass
   - Manually verify login → landing page → navigation to each module; confirm all CRUD/stock/sales/report/customer/brand/category flows work and redirect correctly.
