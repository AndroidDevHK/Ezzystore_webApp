# Agent Notes – Ezzystore WebApp

## Project Snapshot
- **Stack:** Flask 3.x style app factory + blueprints, SQLite via `sqlite3` module, plain HTML/CSS frontend (no build tooling).
- **Entry point:** `run.py` instantiates `app.create_app()` and runs the development server (`flask run` is not wired up).
- **Configuration:** `app/config.py` defines a hard-coded `SECRET_KEY` and points `DB_PATH` at `instance/ezzystore.db`. SQLite lives in `instance/`, which is already created.
- **Dependencies:** Only `flask` and `werkzeug` per `requirements.txt`; install with `pip install -r requirements.txt`.

## Structure
- `app/__init__.py` – app factory; initializes DB/tables via `init_models`, registers the `auth`, `admin`, and `manager` blueprints, and wires up `close_db`.
- `app/db.py` – sqlite connection helper stored in Flask `g`; enforces FK constraints.
- `app/models/` – lightweight data layer with explicit `CREATE TABLE` statements:
  - `user.py` enforces a single admin row (partial unique index) and seeds the default admin (`admin` / `admin123`).
  - `brand.py`, `category.py`, `product.py`, `stock_batch.py` implement CRUD helpers scoped to a shop_id. `Product` tracks quantity via aggregate from restocks, `StockBatch` logs dated restocks.
  - `__init__.py` stitches tables together (shops, shop_managers, etc.) and ensures schema exists on startup.
- `app/auth.py` – routes for `/`, `/login`, `/logout`. Login sets `session` keys for `user_id`, `role`, and optionally shop context for managers. Only managers with a `shop_managers` record can sign in.
- `app/admin/routes.py` – admin dashboard (list shops + assigned managers) and POST actions to create shops and create/assign a manager. Guards all routes with `admin_required`.
- `app/manager/routes.py` – big blueprint that powers the manager console:
  - Dashboard aggregates products, brands, categories, and restock summaries for the manager’s single shop.
  - POST handlers cover product creation, stock additions (multi-product restock support), product edits/deletes, and brand/category CRUD.
  - GET detail routes for brands, categories, and restock dates feed modal/detail templates (`brand_detail.html`, etc.).
- `app/templates/` – standalone HTML pages (no base layout). `login.html`, `admin.html`, `manager.html`, plus detail fragments. Frontend is form-based with Bootstrap-like custom CSS.
- `app/static/` – CSS (login + presumably admin/manager) and image assets; `app/static/css/login.css` is the custom styling you were looking at.
- `instance/ezzystore.db` – SQLite database; tracked in repo, so be careful not to blow it away unless the user asks.

## Running / Resetting
1. `python -m venv .venv && .\.venv\Scripts\activate` (if you need isolation).
2. `pip install -r requirements.txt`.
3. `python run.py` and open `http://127.0.0.1:5000/login`.
4. Log in as the seeded admin: `admin` / `admin123`. Only the admin can access `/admin`. Managers are created/assigned within the admin UI; they can only access `/manager`.
- Schema is created automatically when the app starts (inside `create_app()`), so deleting `instance/ezzystore.db` is enough for a clean slate, but only do this with explicit user approval.

## Implementation Notes
- There is no ORM; all SQL is handwritten. When adding features, mimic the explicit SQL patterns already present.
- Session-based auth is simple: role strings gate blueprints via decorators (`admin_required`, `manager_required`). Respect this structure for new routes.
- Validation relies on server-side `flash` messages shown in templates. Follow the same pattern for UX consistency.
- `manager/routes.py` relies on helper methods from model modules (e.g., `Product.create`, `Brand.get_by_id`). Review those helpers if you need to extend data behavior.
- Templates use inline logic and no macros. If you introduce new views, either duplicate the style or consider extracting shared fragments (but coordinate with the user since that’s a bigger refactor).
- Static styling is manual; there is no bundler or SCSS. Add new CSS under `app/static/css/` and reference via `url_for('static', ...)`.

## Testing / Verification
- There’s no automated test suite. Manual verification is the norm:
  - After backend changes, run the dev server and exercise the relevant forms/routes.
  - For CSS/HTML tweaks, reload the affected page and confirm layout/flash states.
  - If you touch SQL migrations, confirm the tables/columns exist via `sqlite3 instance/ezzystore.db ".schema"` or similar.

## Common Tasks
- **Create new admin-only features:** add routes/functions inside `app/admin/routes.py`, decorate with `@admin_required`, and update `app/templates/admin.html`.
- **Extend manager inventory logic:** modify `app/manager/routes.py` plus associated templates. Keep shop scoping intact by always filtering on the manager’s shop_id.
- **Adjust login experience:** edit `app/templates/login.html` and `app/static/css/login.css`.
- **Change default credentials/secret:** update `app/models/user.py` (seed) and `app/config.py`.

Keep an eye on the instructions in the harness (no destructive git commands, approval policy “never”), and remember that `instance/` contents are effectively production data unless the user says otherwise.***
