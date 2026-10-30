# Bug Report (bugs)

> Last code-audit update: **October 30, 2026** — branch: `dev/classic-restart`
> Scope: all layers (data model, migrations, service/API, auth & authorization, frontend, templates/CSS, tests & tooling).
> **Phase 0 (B1, B2, B3, B13, B7) and the opened Phase 1 items (B4, B6, B8, B9, B10, B12, B11, B15) are fixed.** This file is the tracking document: when a fix starts, tick the checklist items under the bug and mark it Done.
> Unrelated: [inventory-plan.md](inventory-plan.md)
>
> Audit method: every item was re-verified against the current code (file + line references) and by execution (8x... see "Status legend").
> Test run 2026-10-30 (after B11/B15): **121 unit tests passed, 14/14 browser tests passed.**

## Status legend

- **Confirmed** — verified in current code (and/or by execution).
- **Corrected** — original claim needed wording/correction; current text is the verified version.
- **Downgraded** — real, but severity lowered after analysis.
- **Stale / fixed already** — no longer reproducible in current code; kept only for audit history.

Items are ordered by severity: **Critical → High → Medium → Low**, with the ID kept for traceability.

Each completed item carries a **Work log** list: what was actually changed, plus anything done beyond the checklist (test-fixture repairs, docs, behaviour fixes found while testing).

### Work log template (open items)

Open items end with an empty `**Work log:**` placeholder. When a fix lands, replace it with these three bullets and keep the wording short:

```markdown
**Work log:**
- **Changed:** files/routes/helpers actually touched (paths + function names, not a diff summary).
- **Beyond checklist:** anything needed to make the fix real and verifiable — test-fixture repairs,
  docs/README updates, neighbouring behaviour found while testing, follow-up items opened.
- **Left open:** whatever was deliberately deferred, with the bug ID or area it belongs to.
  Write "none" when the checklist is fully closed.
```

A finished item must say *how it was verified* somewhere in those bullets (test file name, or the manual/HTTP check performed).

## Completed work log — phases 0 and 1

- `013edc8` — phase 0: B1, B2, B3, B13, B7 (new `permissions.py`, 19-test `test_phase0_security.py`).
- `341650a` — phase 1 (opened items): B4, B6, B8, B9, B10, B12 (new `schedule_service.py`, 17-test `test_phase1_fixes.py`).
- Phase 1 continuation: B11 and B15 (see the `schedule_service` regeneration helper and `app.py` delete cascade; `test_phase1_fixes.py` gained 5 tests).
- Cross-cutting, not tied to a single bug: two legacy fixtures were signing in as nobody and are now real sessions; a flask-login per-app-context cache leak between test clients was fixed in the tests; README security/roles/test sections rewritten; `templates/settings.html` had CRLF/no-newline damage from earlier edits and was normalized.

## 🔴 Critical

### B1 — Disabled accounts can still log in — **Done (Phase 0)**
The real login entry point `app.py` (`/login`, `login_page`) never checks `is_active_user`, while `/auth/login` (`auth.py`) does. A disabled user cannot use the v2 auth route but the main route is wide open, and any page guarded only by `login_required` works for them.

**Fix checklist:**
- [x] Add the same `is_active_user` check in `login_page` before `login_user(user)`.
- [x] Reject with the same error message/HTTP shape as `auth.login` (403 for JSON, flash+redirect otherwise).
- [x] Add a regression test: disabled user login must fail on `/login` (`test_phase0_security.py`).
- [x] Check any other auth entry points (none currently known) for the same gap. (`/auth/login` already checked it; those are the only two.)

**Work log:**
- `login_page` now returns `403 {"success": false, "message": "حساب کاربری غیرفعال است"}` for JSON and flash + redirect to the form for browsers, mirroring `auth.login`.
- Two tests: form flow with `follow_redirects` (message shown, no `_user_id` in the session) and a JSON-shape test; an active user still logs in.
- Beyond the checklist: the form path needed `flash` + redirect rather than a re-rendered template, because the login page only surfaces flashed messages; the regression test follows the redirect to prove the message is visible.
- Observed but deliberately not changed (out of scope): the wrong-password branch of the same view still passes `error=...` to a template that only reads flashed messages, so that error is invisible today — a UX fix for the auth-error family (B20).

### B2 — Role checks only exist in API v2 — **Done (Phase 0)**
`admin_required` is defined only in `api_v2.py`. All classic `/api/*` mutation routes carry only `login_required`:

- `/api/node` (create/edit/move/delete node)
- `/api/schedules` (create)
- `/api/settings/save`
- `/api/documents/upload/...` and document delete
- `/api/upload`

A `viewer` can therefore delete the whole BOM or rewrite SMTP settings through the classic API, while the identical operation is 403 on v2. (Executed-verified: `POST /api/settings/save` returns `200` without any role check.)

**Fix checklist:**
- [x] Create a shared decorator (e.g. `role_required('admin','engineer')`) importable by both blueprints (avoid circular imports — put it in a small `permissions.py`).
- [x] Apply it to all classic mutation routes listed above (GET-only routes may stay `login_required`).
- [x] Decide: document upload/delete = engineer+; settings save = admin only.
- [x] Regression tests for each role × route class (viewer must get 403).
  - Note: `test_manufacturers.py` previously asserted that viewers may rewrite node/stage data through the classic API; that assertion encoded the bug, so it now expects 403 and verifies the same legacy payloads still succeed for an engineer.

**Work log:**
- New `permissions.py` with `role_required(*roles)`; it reads `getattr(current_user, 'role', None)` so an `AnonymousUser` (test/`LOGIN_DISABLED` setups) yields 403 instead of `AttributeError`.
- Applied to: node create/update/move/delete, `/api/upload`, document upload and delete, `/api/schedules` create (already), `/api/settings/save`; `/settings` POST additionally refuses non-admins with a flash.
- Beyond the checklist: `test_bom_inventory.py` had been running all classic writes with `LOGIN_DISABLED=True` and no user, which is exactly why the hole went unnoticed — it now seeds an admin and signs in like production. During that work a flask-login `g._login_user` cache leak between test clients (they share one app context) was found and fixed in `test_phase0_security.py`, otherwise a second client silently inherited the first client's role.

### B3 — SMTP password stored and rendered in the clear — **Done (Phase 0)**
The password is saved in plaintext in the `settings` table and rendered into the page by `templates/settings.html` (`value="{{ settings.mail_password }}"` in a password-input — the value is still readable from the DOM/source). Any logged-in user, including `viewer`, can read or overwrite it.

**Fix checklist:**
- [x] Never pass the password value to the template; render only a "set / not set" indicator.
- [x] Split settings page: viewing vs saving SMTP credentials restricted to admin (depends on B2).
- [x] Ensure `autoSaveSetting('mail_password', ...)` only writes when a new password is actually typed (empty = keep old).
- [ ] Later: store secrets outside the DB (env/secret store) — still open (not filed as its own ID); the value remains plaintext in the `settings` table.

**Work log:**
- The settings view no longer passes `mail_password` to the template at all; the field renders empty with a keep-current placeholder and a `✓ ذخیره شده / ثبت نشده` indicator.
- Empty or whitespace-only password keeps the stored value on both `/settings` (form) and `/api/settings/save` (JSON).
- Beyond the checklist: `templates/settings.html` carried CRLF/joined-line damage from earlier edits and was normalized to clean LF while adding the indicator.

### B13 — Uploads without type/size limits (Corrected) — **Done (Phase 0)**
`/api/upload` accepts any extension with no size limit; files are served back from `/uploads`.
- Stored XSS: an uploaded HTML/SVG is served same-origin, where user cookies/sign-in apply.
- **Correction from original report:** `delete_document` *does* unlink the file from disk. Orphaned files are a real issue only via node deletion / image-record deletion (see B15).
- **Extra gap found:** `/uploads/<path:filename>` has **no `login_required`** — all uploads are publicly reachable without sign-in.

**Fix checklist:**
- [x] Whitelist extensions per endpoint (images for `/api/upload`; the existing `type_map` for documents) and reject others with 400.
- [x] Enforce a max upload size (request body limit / explicit size check) — 10 MB images, 25 MB documents, `413` on overflow.
- [x] Add `login_required` to `uploaded_file`.
- [x] For non-image types serve with `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`; HTML/SVG are not accepted at all.
- [x] Regression test: `.html` upload refused; oversized refused; anonymous `/uploads` request redirected to login (302, not 401 — redirect is what `login_required` gives a browser).

**Work log:**
- `_IMAGE_EXTENSIONS` allowlist for `/api/upload`, extension lowercased so `.PNG`/`.JPG` still pass; 10 MB image and 25 MB document caps returning `413`.
- `/uploads/<path:filename>` is now `login_required`; non-image responses get `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`.
- Beyond the checklist: documents keep their existing `type_map` (CAD/archive/office) but HTML/SVG/JS/EXE are refused; tests verify both the allowlist and the real download headers, not just status codes.

### B7 — Hardcoded default SECRET_KEY and default admin admin123 — **Done (Phase 0)**
`config.py` falls back to a hardcoded `SECRET_KEY` default; `app.py:init_db` creates admin with `admin123`. Together with forged-session risk (also see B6), this is production-fatal.

**Fix checklist:**
- [x] In production mode require `SECRET_KEY` from env and fail startup otherwise; dev/test keep safe random defaults.
- [x] First-run admin gets a random password printed once to the console (or a provisioning path) and is forced to change it.
  - Partially done: the random password is printed once; *forcing* a change on first login is still open (tracked with the auth hardening work).
- [x] Document both in README (also covered by B42).

**Work log:**
- `ensure_production_secret()` lives in `config.py` and is called at the top of `app.py`, so every entry point (not just `python app.py`) fails fast when `FLASK_ENV=production` and `SECRET_KEY` is missing.
- `init_db` creates the first admin with `secrets.token_urlsafe(12)` and prints it once, labelled as one-time.
- README no longer advertises `admin/admin123`; it documents the printed password and the production secret requirement.
- Beyond the checklist: the random password is printed but not *forced* to change on first login — left open deliberately and cross-referenced to the auth hardening work.

---

## 🟠 High

### B4 — Open redirect on `/auth/login` — **Done (Phase 1)**
`auth.py`: `next` is taken from `request.args` and used unvalidated for redirects (`redirect(next_page)`, `jsonify({'redirect': next_page})`).

**Fix checklist:**
- [x] Validate with `url_has_allowed_host_and_scheme(next_page, request.host)` (relative paths only).
  - Implemented as `safe_next_url()`: an explicit parse that rejects any scheme/netloc and any path not starting with `/` (or starting with `//`), which is stricter than the host-allowlist helper and needs no `SERVER_NAME`.
- [x] Fallback to `url_for('index')` when invalid.
- [x] Regression test for `next=https://evil.example` (JSON and form flows), plus a relative-`next` case that must still work.

**Work log:**
- `safe_next_url()` rejects non-strings, absolute URLs, protocol-relative `//host`, and any path not starting with `/`; valid relative paths keep their query string.
- Both the JSON `redirect` value and the form `Location` header go through it, falling back to `url_for('index')`.
- Beyond the checklist: `app.py`'s own `/login` never read `next` (always `index`), so it needed no change — recorded here so a future reader does not assume it was overlooked.

### B26 — Multiple stored-XSS injection points in frontend
Names/strings injected into HTML unescaped:
- Notifications list (`item.name`)
- Kanban cards (`card.name`)
- Breadcrumbs (`item.name`)
- Schedule list (`s.notes` where rendered)
- Image gallery (`img.label`, `img.url` inside `onclick="openModal('${url}')"`)

`escapeHtml` exists in `script.js` but is not used in all of these spots (stage names, details, manufacturer addresses *are* escaped).

**Fix checklist:**
- [ ] Wrap every dynamic interpolation above with `escapeHtml` (and for URLs, escape quotes/attribute content too).
- [ ] Sweep `script.js` for remaining bare template interpolations of user data; grep rule: no `${node.name}`-style without the helper.
- [ ] Regression test: product named `<img src=x onerror=alert(1)>` must render as text in tree, kanban, notifications, breadcrumbs, gallery.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B8 — Create assembly without name ⇒ 500 — **Done (Phase 1)**
`api_v2.py` `create_assembly` uses `data['name']` directly (KeyError). Confirmed by execution: `POST /api/v2/assemblies {"product_id":41}` → `500`.

**Fix checklist:**
- [x] Validate name like `_definition_payload` does (nonempty string, reasonable length) → 400. (Applied to create *and* update.)
- [x] Same for the classic `/api/node` path if applicable (it already defaults, but enforce nonempty for v1 parity).
  - Classic now normalizes a missing/blank name to `بدون نام` before fields are applied, so whitespace can no longer be stored as a name.

**Work log:**
- v2 `create_assembly` and `update_assembly` reject a missing, non-string or whitespace name with `400 Invalid assembly name`.
- Beyond the checklist: the first attempt at the classic fix looked correct but tests proved the name was overwritten again by `_apply_node_fields`, which copies `req['name']` onto the object; the create path now passes a normalized copy (`dict(req, name=name)`), so the default actually sticks.

### B9 — Production schedule creation without validation — **Done (Phase 1)**
Classic (`app.py create_schedule`) and v2 (`api_v2.py create_schedule`):
- Missing JSON body ⇒ 415 as an HTML error page (frontend expects JSON → B20).
- Nonexistent `product_id` or a bad/missing date ⇒ 500 (KeyError / `fromisoformat` ValueError).
- Negative `quantity` is accepted and saved (confirmed by execution: `WorkOrder` with `quantity: -20`).

**Fix checklist:**
- [x] One shared payload validator for both routes: product exists, dates parse-or-null, `quantity` >= 1 (integer), `status/priority` from an allowed set. (`schedule_service.validate_schedule_payload`)
- [x] Return JSON errors with 400 always (`request.get_json(silent=True)` + explicit checks).
- [x] Regression tests: no body, unknown product, bad date, negative quantity, zero, float quantity, bad status/priority.

**Work log:**
- One validator (`schedule_service.validate_schedule_payload`) is used by the classic and v2 routes; it checks product existence, integer quantity ≥ 1, ISO-or-null dates, and status/priority against fixed tuples.
- Both routes now use `get_json(silent=True)` and always answer `400` with a JSON `error`, so a missing body is no longer a `415` HTML page.
- Beyond the checklist: the duplicated `_auto_work_orders` (classic) and `_auto_generate_work_orders` (v2) helpers were deleted in favour of one shared generator, which is what made the B10 fix single-source.

### B10 — Wrong work-order quantity for nested BOMs — **Done (Phase 1)**
`_auto_work_orders` (classic) and `_auto_generate_work_orders` (v2) compute `part.required_quantity * schedule.quantity`, ignoring intermediate assembly multipliers. Confirmed by execution (expected −120, got −20 for a 4×3×2×5 chain).

**Fix checklist:**
- [x] Compute per-part `required_total` from the existing BOM calculation (`load_data()` already resolves nested multipliers correctly) instead of the direct product.
- [x] Add a unit test reproducing the 4×3×2×5 case.
- [x] Keep the formula single-source: reuse the same helper in both classic and v2 routes. (`schedule_service.part_requirement_totals`, used by `generate_work_orders`)
  - Note: the previous v2 test asserted the buggy `7×9=63`; it now expects `3×2×7×9=378`.

**Work log:**
- `schedule_service.part_requirement_totals()` walks the assembly tree once, multiplying every level; `generate_work_orders()` writes one pending order per part for both routes.
- Beyond the checklist: writing the test exposed a second mistake in the first implementation — the product→root-assembly edge was multiplied by 1, giving 30 instead of 120. The root coefficient is now applied, and the parametrized test covers the 4×3×2×5 chain on both endpoints.

### B11 — Work orders never refresh when a schedule changes — **Done (Phase 1)**
`update_schedule` can change `quantity` (v2), but previously generated work orders keep the old value. Confirmed by execution.

**Fix checklist:**
- [x] On schedule quantity change, delete not-yet-started work orders for that schedule and regenerate with the corrected totals (B10 helper).
- [x] Never touch started/completed orders; log the adjustment in `notes`.
- [x] Regression test: change schedule 20→50 → pending WOs follow.

**Work log:**
- **Changed:** `schedule_service.refresh_pending_work_orders()` rebuilds only `pending` orders from `part_requirement_totals()`; `api_v2.update_schedule` calls it when the quantity actually changes and appends `Work orders recalculated: 20 → 50 units (n pending)` to `notes`. Same transaction as the schedule update (one commit).
- **Beyond checklist:** the naive "delete pending and recreate" would have re-planned work that had already started, so quantities of `in_progress`/`completed`/`cancelled` orders are summed per part and subtracted; only the remainder becomes a new pending order. A no-op edit (priority/notes only) provably leaves order ids and quantities untouched.
- **Left open:** pending orders keep their old `due_date` when only `end_date` changes on the schedule — same regeneration path can be extended later; not part of this bug. Verified by five tests in `test_phase1_fixes.py` (`20→50` = 480→1200 on a 4×3×2 BOM, started-order remainder, unrelated update).

### B28 — Part type never saved from UI
`#field-partType` does not exist in any template, but `script.js` reads it (`payload.partType = $('#field-partType').val()`) and writes it on open. Result: `partType: undefined` is dropped from the payload → `part_type` is never set through the classic UI.

**Fix checklist:**
- [ ] Add the `partType` select (buy/make) to the inventory tab, shown for parts only.
- [ ] Wire it to autosave like other fields.
- [ ] Regression test: change type in UI → reload → value persists.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B27 — "Production schedule" tab is effectively dead
In `templates/index.html` the tab button is `hidden` with `display:none !important`, and `script.js` (`showEditForm`) always hides it as well. `loadSchedulesForProduct` is only called after creating a schedule. Scheduling is unreachable from the UI.

**Fix checklist:**
- [ ] Decide the UX: either show the tab for products with scheduling enabled, or remove the dead code path entirely (list schedules in the dashboard instead).
- [ ] If restored: unhide for product nodes and fix the call chain (load on product select).
- [ ] Document the decision in the UI plan.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B22 — No uniqueness / hard delete
`Product.code` and `Part.part_code` lack `unique` and search indexes; deletion is hard delete (history lost). This will bite the inventory plan (shared items, barcodes).

**Fix checklist:**
- [ ] Migration: normalize duplicate codes, then add indexes (+ `unique` where sensible).
- [ ] Return a clean 409 on duplicate insert/update in v2 endpoints.
- [ ] Soft-archive decision: deferred to inventory plan (archived flag) — do not invent a parallel scheme here.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B21 — `to_dict` monkey-patched onto models at import time
`api_v2.py` (`_add_to_dict_methods`) attaches `to_dict` to `Product/Assembly/Part/Stage/...` when `api_v2` is imported. Any consumer of the models without importing `api_v2` (migrations scripts, future code) gets `AttributeError`. `Stage.to_dict` also triggers per-stage manufacturer queries (N+1).

**Fix checklist:**
- [ ] Move `to_dict` definitions into `models.py` as real methods.
- [ ] For `Stage.to_dict`, accept preloaded manufacturer links or make it opt-in (`to_dict(with_links=False)` default).
- [ ] Remove `_add_to_dict_methods` and the import-time side effect.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B23 — `migrate_data.py` migrates data incompletely
Confirmed: nested assemblies (whose `parent` is an assembly) and their parts are skipped entirely; stage costs, assembly images and assembly `required_quantity` are not migrated; and there is no rollback.

**Fix checklist:**
- [ ] Two-pass migration: create all assembly rows first (map parents by type), then parts.
- [ ] Migrate assembly images, `required_quantity`, and stage cost fields.
- [ ] Wrap in a transaction (single commit at end) and delete `bom_data.json` marker / backup DB before starting, with a `--dry-run` mode.
- [ ] Test against a fixture JSON containing nested assemblies.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B24 — Schema migrations locked per process only
`RLock` in `bom_inventory_migration.py` / `manufacturer_migration.py` is process-local; with multiple workers there is a `duplicate column` race. Manufacturer backups land inside the repository (`backups/`); inventory backups land next to the DB file.

**Fix checklist:**
- [ ] Align on SQLite-level safety: wrap DDL in a transaction with `BEGIN IMMEDIATE` (SQLite serializes writers) or use a file lock (e.g. `msvcrt`/`fcntl` or a lockfile with timeout).
- [ ] Exclude `backups/` and `instance/` from git (check .gitignore; move runtime backups out of the repo tree).
- [ ] Test with two concurrent processes against one file DB.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

---

## 🟡 Medium

### B5 — CSRF / CORS (Downgraded from High)
`cors.init_app(app)` with defaults allows all origins (no `supports_credentials`, so cross-origin credential reading is blocked by default). No CSRF protection exists (no Flask-WTF). Modern browsers default session cookies to `SameSite=Lax`, which blocks most cross-site POSTs; risk is moderate, not critical.

**Fix checklist:**
- [ ] Set `SESSION_COOKIE_SAMESITE = 'Lax'` (or `'Strict'`) and `SESSION_COOKIE_SECURE` in production config.
- [ ] Restrict CORS to same-origin (drop global `CORS()` or configure exact origins) — the app is same-origin today.
- [ ] Optionally add origin verification on POST for the classic mutating routes (cheap CSRF strategy for a JSON API).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B12 — `PUT` schedule with `null` date ⇒ 500 — **Done (Phase 1)**
`api_v2.py update_schedule`: `datetime.fromisoformat(data['start_date'])` with `None` in payload. Confirmed by execution → 500.

**Fix checklist:**
- [x] `if data['start_date'] in (None, ''): schedule.start_date = None else: parse` (same for end_date) — also apply to the classic route for parity. (Shared `validate_schedule_payload(..., partial=True)`; the classic module has no schedule-update route, so there is nothing else to align.)
- [x] Regression test included with B9's schedule test class.

**Work log:**
- `validate_schedule_payload(..., partial=True)` parses only the supplied fields, so `null`/`''` clear a date instead of raising, and invalid dates or quantities return `400`.
- Beyond the checklist: `product_id` is ignored on update (a schedule cannot be moved to another product through PUT), and `status`/`priority` are validated on update as well as create, not just on create.

### B14 — Product documents: no per-product attribution (Corrected)
`upload_document` for a `product` stores `part_id=None, assembly_id=None`; `list_documents` filters on exactly that. So product documents *are* listed — but for **every** product (both-None filter matches all product docs), and no record points back to the owning product. Original text had the direction inverted.

**Fix checklist:**
- [ ] Add a `product_id` concept: either a dedicated column on `Document`, or treat `part_id+assembly_id both NULL` + explicit `ref_node_id` column.
- [ ] Migrate existing both-NULL docs (they are indistinguishable today — mark as unassigned and surface in UI for manual assignment).
- [ ] Filter per node; regression test that product A's docs don't appear under product B.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B15 — Node deletion leaves orphaned data and files — **Done (Phase 1)**
`delete_node` does not clean `Document` records + disk files, `WorkOrder`, `NotificationLog`, or uploaded image files (images: only records deleted).

**Fix checklist:**
- [x] In the recursive delete: collect `Document` records → delete rows + unlink files; delete `WorkOrder`s and `NotificationLog`s for parts being removed.
- [x] For assembly/product cascade, include their image files too.
- [x] Keep a simple `deleted_uploads` audit line (log) or a dry-run listing (nice-to-have).
  - Delivered as machine-readable counts in the response (`{"removed": {documents, images, files, work_orders, notifications, schedules}}`) instead of a log line; the frontend ignores the extra key.
- [x] Regression test: build product + part + doc + image + schedule → delete root → filesystem and orphan tables are clean.

**Work log:**
- **Changed:** `app.py` gained `_unlink_upload()` (resolves `/uploads/<name>` to `UPLOAD_DIR`, basename only, ignores missing files) and `delete_node` now drops `Document` rows + files, `Image` rows + files, `WorkOrder`s and `NotificationLog`s per part, and assembly-level documents/images; deleting a product also deletes its `ProductionSchedule`s.
- **Beyond checklist:** the original recursive delete left `ProductionSchedule` rows pointing at a deleted product (dangling `product_id`, still listed in the UI) — those are now removed, and their work orders go with them. A document row whose file is already gone is still deleted without raising (tested).
- **Left open:** documents with `part_id` and `assembly_id` both NULL are not attributable to any node (B14), so deleting a product deliberately leaves them; they stay until B14 adds an owner column. Verified by two tests in `test_phase1_fixes.py` (full product cascade with real files on a temp `UPLOAD_DIR`, and a single-part delete that keeps the sibling part's document).

### B16 — Image upload for product/assembly nodes is a no-op
`_apply_node_fields` only handles the `images` block for `typ == 'part'`, but the frontend uploads images for all node types → file saved, no record created, image vanishes after reload.

**Fix checklist:**
- [ ] Extend the images block to `assembly` (exists: `Image.assembly_id`) and to `product` (needs the B14/B16 storage decision — simplest: reuse assembly-style `Image` rows keyed by product via a nullable `product_id`, or attach to a hidden root assembly).
- [ ] Same gallery semantics for those types (labels, delete).
- [ ] Regression test per node type: upload → save → reload → image persists.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B17 — Weak validation on node save
`_apply_node_fields`: no checks for `status`/`part_type` values, empty names, field lengths; `estimated_*`/`actual_*` (cost/hours) accept arbitrary strings/numbers into Float columns (SQLite type affinity accepts them silently).

**Fix checklist:**
- [ ] Validate enums (`status`, `part_type`) and clamp/parse numerics with `validate_quantities`-style helper for stage fields.
- [ ] Enforce nonempty names and reasonable max lengths (mirror the manufacturer `_definition_payload` rules).
- [ ] Return the first validation problem as JSON 400.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B18 — Fragile exports (Excel / Graphviz schematic)
- Schematic: node/stage names injected unescaped into the Graphviz HTML label (a `<` breaks PDF generation); Windows paths with backslashes are interpolated into `<IMG SRC="...">`; missing `dot` binary ⇒ raw 500.
- Excel: sheet names truncated to 31 chars after cleaning and can collide (openpyxl silently appends `1`), image always anchored at column C.

**Fix checklist:**
- [ ] Escape all label content (Graphviz supports an escape mode; or use `html=False` label building with a quoting helper).
- [ ] Convert image path separators to `/` for `IMG SRC`; guard `dot.pipe()` with a friendly JSON 500 ("Graphviz not installed, see README").
- [ ] Excel: ensure unique sheet titles (de-dup with a suffix map on our side; don't rely on openpyxl), and make the image anchor column configurable.
- [ ] Regression tests: export with names containing `<> &`; export machine without graphviz → clean error.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B19 — N+1 / O(n²) load path
`load_data()` issues per-entity queries (products → 2 queries each, assemblies/issues similarly, then `StageDetails`/`manufacturers` per stage); `/api/notifications` builds the same dataset again; frontend `refreshDemandViews` rebuilds the whole subtree per node.

**Fix checklist:**
- [ ] Batch queries: preload all assemblies/parts with `joinedload`/`selectinload`, then assemble in memory.
- [ ] `/api/notifications`: compute from the same cached `load_data()` result in-process (or share one function).
- [ ] Frontend: update only affected nodes on edits (jstree supports `set_text` per node — partial done).
- [ ] Benchmark before/after with ~200 parts (assert < some ms budget in a perf test).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B20 — Non-JSON error responses on classic routes
Classic routes leak HTML error pages (framework errors) while the frontend calls `res.json()` — users see "Unexpected token <" instead of the cause.

**Fix checklist:**
- [ ] Add app-level error handlers: `400/404/415/500` → JSON when `request.path.startswith('/api/')`.
- [ ] Frontend helper `readJson(res)` that throws with status + text for non-JSON payloads.
- [ ] Regression test: any invalid classic POST returns JSON error body.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B25 — Low-stock email scheduler misconfigured
The APScheduler job only runs under `__main__` (never under gunicorn); with `debug=True` the reloader runs it twice; every 6 hours it re-sends without any "already sent" memory (`NotificationLog` is written but never consulted); `check_and_notify_low_stock` also opens a redundant app context.

**Fix checklist:**
- [ ] Move scheduler startup into an init hook that runs in the serving process (and guard against reloader duplicates).
- [ ] Before sending, check `NotificationLog` for a recent successful send for the same part+recipient (window, e.g. 24h) — significant refactor; keep design decision here.
- [ ] Remove the inner `with current_app.app_context()` (caller already provides one).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B29 — Supplier name field permanently hidden
`#supplier-group` has a fixed `display:none` in `templates/index.html`; nothing ever shows it, even for parts. The input is still filled/wired, so the data model exists but the field is invisible.

**Fix checklist:**
- [ ] Show it for parts (mirror `#part-email-group` visibility logic), keep hidden for assemblies/products.
- [ ] Regression test in browser test: edit a part, supplier field visible and saveable.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B30 — Schedule filtering matches by product name too (Corrected)
`loadSchedulesForProduct` filters `s.product_name === productName || s.product_id == productId...`. The id branch exists now; two products with the *same name* still cross-match through the name branch. Original claim was partially stale.

**Fix checklist:**
- [ ] Drop the name branch; filter by id only.
- [ ] Regression test with two same-named products.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B31 — Stage details are keyed by positional index
`stageDetailsMap[idx]` + drag-and-drop reordering ⇒ details follow the wrong stage. Unsaved stages' details also only live client-side; once the stage gets a server id via autosave, details are never persisted.

**Fix checklist:**
- [ ] Key stage details by stage identity, not index (stable client-side key for new stages — mirror `persistedStageIds`).
- [ ] On reorder, re-map detail entries to their (moved) stage keys.
- [ ] Persist stage details at the same moment stages are saved (after autosave assigns ids).
- [ ] Regression test: add stages, reorder, reload → details stay on their stages.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B32 — Status colors defined in three places
CSS with `!important`, JS inline colors (`inventoryStatus` anchor coloring), and theme variables. `toggleTheme` doesn't recompute inline styles; the CSS `!important` rules also override the JS coloring at runtime.

**Fix checklist:**
- [ ] Single source: status classes (`status-*`) styled purely via CSS variables; JS sets class, not color strings.
- [ ] Remove corresponding `!important` rules and hardcoded hex (#4CAF50/#FF9800/#F44336) where duplicated.
- [ ] Browser test: toggle theme → node colors follow without reload.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B34 — Errors swallowed in the UI
`move_node.jstree` handler, `deleteNode`, `confirmInlineEdit`, `addChildOf` don't check non-2xx (a rejected move/delete looks successful); `loadNotifications` doesn't check `res.ok`.

**Fix checklist:**
- [ ] Route all of them through a small `requestJson(...)` wrapper that toasts on failure and reloads state on success only.
- [ ] On failed move, revert the tree node to its original parent (re-fetch).
- [ ] Browser test: simulate 400 from server → visible message shown.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B38 — CDN dependency without fallback on settings/manufacturers pages
`templates/settings.html` (and `manufacturers.html`) load jQuery only from CDN, no local fallback, no SRI. Offline/filtered networks kill these pages entirely (the main index page has a fallback).

**Fix checklist:**
- [ ] Bundle jQuery locally (vendored into `static/`) and reference it everywhere; or drop the dependency with vanilla JS.
- [ ] Add SRI hash if CDN reference remains.
- [ ] Align loading order across templates (one shared block).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B42 — Coverage gaps and empty README
No tests for: `/api/schedules`, work orders, excel/schematic exports, documents, settings, classic `/api/node` routes, `viewer` role — precisely where the bugs above live. `README.md` is just `# bom`. Also 648 `LegacyAPIWarning`s in test runs.

**Fix checklist:**
- [ ] Add API-level test classes for the six routes listed (a single `test_classic_api.py` is enough).
- [ ] Write a real README: setup, env vars, roles, migrations, scheduler, known limitations ending in bugs.md references...
- [ ] Silence modernization warnings by switching legacy `Query.get()` to `db.session.get()` (the only systematic family of warnings).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

---

## 🟢 Low

### B6 — Fragile `load_user` — **Done (Phase 1)**
`db.session.get(User, int(user_id))` raises `ValueError` on a non-integer session id → 500 per request instead of a clean signed-out state. (With a known SECRET_KEY a forged session becomes reachable — same root cause as B7.)

**Fix checklist:**
- [x] Guard: try/except int conversion → return None (signed-out) on any non-integer.
- [x] Quick unit test for a tampered session id (`not-a-number`, unknown id, `1.5`).

**Work log:**
- `load_user` converts inside `try/except (TypeError, ValueError)` and returns `None`, so the request is treated as signed out and redirects to login instead of returning 500.
- Three parametrized tests cover non-numeric, fractional and non-existent ids.
- Beyond the checklist: this closes the 500-per-request path that a forged or garbage session id could trigger even after B7, and it is the guard B7's `SECRET_KEY` requirement needed to fail safely.

### B33 — Dashboard counts unreachable nodes
`updateDashboard` counts all nodes from the server payload, including cycle/orphan nodes that don't render in the tree. Executed-verified: a self-cycle (`a51.parent_id = a51`) came back with status 200 and the node disappeared from the tree but stayed in stats.

**Fix checklist:**
- [ ] Server-side: detect cycles in `load_data()` (skip self/duplicate parents or flag them), avoid silently swallowing.
- [ ] Count stats from the same traversed tree used for rendering.
- [ ] Regression test with a cycle fixture.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B35 — Autosave without conflict detection
Every keystroke sends the whole node; two open tabs = last write wins, silently.

**Fix checklist:**
- [ ] Add `updated_at` on node tables and include it in payloads; reject PUT when the served version is newer (409) with a toast.
- [ ] Throttle autosave beyond the current 600ms debounce (e.g. coalesce unchanged fields).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B36 — Duplicated/dead frontend code
Two independent manufacturer-create flows (`submitMfrForm` and `ManufacturerUI.openEditor`), shared `mfrExpandState` across part views, and `stageDetailsMap = {}`/`expandedStages = {}` reset on every node selection.

**Fix checklist:**
- [ ] Consolidate manufacturer form into one component/state owner.
- [ ] Scope expand-state per node/per part context (keyed state), or persist intentionally.
- [ ] Preserve expand state on switching back to the same node when the node didn't change.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B39 — CSS leftovers (Corrected)
Two `#shortage-info` blocks exist (`style.css:331` and `:494`), with `!important` interplay; hardcoded colors (#f44336/#4CAF50/#333) appear across files. **Correction:** `--color-scheme-inherit` is *used* (line 443, `color-scheme: var(--color-scheme-inherit, light)`) — the actual oddity is its hardcoded `dark` value at line 46.

**Fix checklist:**
- [ ] Merge the two `#shortage-info` rule sets into one (keep the themed variant), drop redundant `!important`.
- [ ] Rename the variable to describe actual behavior (e.g. `--page-color-scheme`) and set it per theme, not hardcoded `dark`.
- [ ] Sweep hardcoded colors into theme variables (status colors shared with B32 work).

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

### B40 — Accessibility basics
Emoji-only buttons without `aria-label`; status conveyed by color alone (tree nodes); gallery title mislabeled (`title="No images"` on every image, script.js `renderImageGallery`).

**Fix checklist:**
- [ ] Add `aria-label`/`title` to icon-only buttons.
- [ ] Status shown via icon+color (make class from B32 include an icon glyph).
- [ ] Fix image title to the image label.

**Work log:** _empty — fill with the three bullets from the template at the top of this file when the fix lands._

---

## Audit appendix — items removed from the active list

These items were listed in the earlier report dated Oct 29 but no longer reproduce against the current code. Kept here for traceability:

### B37 — Settings page JS crash — **Stale / Guard exists**
The original claim was: `settings.html` loads `script.js`, whose `$(document).ready` dereferences `.form-actions` and fails on the settings page (no such element). Current code returns early at the top of the ready handler (`if (!document.getElementById('tree-container')) return;`) — shared pages like settings never reach the `.form-actions` block. Not reproducible. No action.

### B41 — Dark-mode transition flake in tests — **Stale / Fixed in the current test**
The original claim was: the browser dark-mode test read computed styles while a CSS transition was still running (timing-dependent failure). The current test's `STYLE_AUDIT` includes a `settled` flag (every ancestor animation `playState !== 'running'`) and `assert_style` waits for `textMatches && backgroundMatches && settled` before asserting. Executed verification 2026-10-30: **all 14 browser tests pass** (earlier "1 failing browser test" claim no longer holds). No action.

---

## Suggested fix order (phases)

1. **Phase 0 — security, smallest diffs (done):** B1 → B3 → B2 → B13 → B7 (each 1–3 touchpoints; B2 needs the shared decorator first).
2. **Phase 1 — data correctness:** ~~B8~~, ~~B9~~, ~~B12~~, ~~B10~~, ~~B11~~, ~~B15~~ (done), then B16, B14, B23, B22, B21, B24. Security continuations B4/B6 are also done.
3. **Phase 2 — UX and frontend correctness:** B26, B27, B28, B29, B30, B31, B34 (B20, B5 ride along here).
4. **Phase 3 — quality/performance/grinding:** B19, B18, B32, B38, B39, B40, B25, B33, B35, B36, B42 (tests last, once phases 1–2 stabilize the routes).
