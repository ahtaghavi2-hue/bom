# BOM Manager

A Flask application for managing product bills of materials (BOM): products, assemblies and parts with quantities, manufacturing stages and costs, manufacturers, production schedules, inventory status and shortage reporting, plus Excel and PDF schematic exports and low-stock email notifications.

## Stack

- **Backend:** Flask 3, SQLAlchemy 2 (SQLite), Flask-Login, Flask-Mail, APScheduler
- **Frontend:** server-rendered templates, jQuery + jsTree (CDN with local caching in tests), theming with CSS variables, RTL/LTR bilingual UI (fa/en)
- **Exports:** Openpyxl (Excel), Graphviz (`dot` binary required) for the PDF schematic

## Quick start

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (bash: source .venv/bin/activate)
pip install -r requirements.txt
python app.py                 # starts http://localhost:5000 (creates/updates the schema on first run)
```

- On first run an **`admin` user is created with a random password that is printed once to the console** — copy it and change it after signing in.
- `SECRET_KEY` **must** be set in the environment (or `.env`) when `FLASK_ENV=production`; startup fails without it. Development keeps a local fallback; see `config.py`.
- Optional env vars: `DATABASE_URL`, `MAIL_*` (SMTP settings can also be configured in-app under `/settings`).

## Roles

| Role | /api/v2 mutations | Description |
|---|---|---|
| `admin` | ✔ | full access, including settings and adjustments |
| `engineer` | ✔ (non-admin-only actions) | structural data changes |
| `viewer` | ✖ (403) | read-only |

Classic `/api/*` mutation routes now enforce the same roles as v2 through the shared `role_required` decorator in `permissions.py` (uploaded files also require a signed-in user).

## Tests

```bash
python -m pytest test_bom_inventory.py test_manufacturers.py test_phase0_security.py -q  # unit tests (in-memory SQLite)
python -m pytest test_browser_startup.py -q                      # real browser regressions
```

Browser tests launch the real Flask server on temporary databases and drive an installed Chrome via CDP (`_browser_startup_server.py`, `tests/_browser_startup_cdp.js`). They do not mock app responses. Requirements:

- Windows Chrome at `%ProgramFiles%\Google\Chrome\Application\chrome.exe` (override with `BOM_TEST_CHROME`)
- Node.js with native `WebSocket` (override binary with `BOM_TEST_NODE`)
- First run fetches CDN dependencies once and caches them (override cache dir with `BOM_TEST_CDN_CACHE`)

## Migrations

Additive schema migrations run automatically on the first request (`bom_inventory_migration.py`, `manufacturer_migration.py`). They back up the SQLite file before any DDL: manufacturer backups into `backups/`, inventory backups next to the database file. **Do not commit those backups** (`backups/` and `*.sqlite` are gitignored).

## Project docs

- [bugs.md](bugs.md) — code-audit bug tracker, severity-ordered, with per-bug fix checklists
- [inventory-plan.md](inventory-plan.md) — plan for the real inventory dashboard (catalog, locations, stock ledger, shortage reports)
