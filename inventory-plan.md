# Inventory Dashboard Plan

> Status: **plan only — nothing implemented yet.**
> Scope: turn the current quantity fields into a real inventory dashboard: item catalog, storage locations, tagging, event-sourced stock history, and BOM-based shortage reporting.
> Linked audit: [bugs.md](bugs.md) — several bugs (B14, B15, B19, B22, B2) directly affect this plan and are referenced below.

---

## 0. Starting point and design principles

The current codebase already has the required base:

- In `models.py`, all three entities (`Product`, `Assembly`, `Part`) carry quantity/need fields (`quantity`, `required_quantity`, `order_count`, `required_total`, `shortage`).
- The BOM demand/shortage logic exists (`bom_calculation.py`) and is covered by `api_v2.py` and `test_bom_inventory.py`.

Core principle:

> **Inventory must gradually become the authoritative single source of truth for real stock — we never create a parallel, inconsistent number next to the current `quantity` field.**

Two structural risks to control from day one:

1. **Dual inventory:** if the dashboard keeps a separate stock number, it will drift from the current `quantity` field immediately.
2. **Double-counting shared parts:** stock of a part used across multiple products must be counted once, not per product.

### 0.1 Locked design decisions (from the architecture review)

These replace earlier open options. They are decisions, not proposals:

- **D1 — Item model.** For BOM parts, **`Part` IS the catalog entry**: add `unit`, `min_stock`, `max_stock` columns to `Part` (null = not an inventory item). A new `InventoryItem` table exists only for non-BOM items (consumables, fasteners not in any BOM, packaging, tools). For merging several `Part`s that reference the same physical article, a plain `inventory_groups` join table (`group_id`, `part_id`) comes in a later phase — v1 ships without it. This avoids migrating every existing part into a second table and avoids duplicating name/media/supplier metadata.
- **D2 — Balance representation.** The event log is the source of truth for *correctness*; performance uses a **cached balance column** (`stock_quantity` on `Part`/`InventoryItem`) updated **inside the same transaction as the movement insert**. A "recount from events" action and a periodic integrity check validate the cache. Pure on-the-fly aggregation on every `load_data()` call is rejected — it would multiply the existing N+1 problem (bugs.md B19).
- **D3 — Reservation lifecycle.** A reservation is a ledger event type that **must reference a `ProductionSchedule`** (nullable FK for manual reservations). Reserved balances auto-release when: the schedule is cancelled, the schedule is completed, or a scheduled auto-release date passes (TTL field). No orphaned reservations.
- **D4 — Units (v1 rule).** One item has exactly **one unit**, and that unit must match the unit used by BOM `required_quantity` of the items it covers. Unit conversion (e.g. cable in meters) is explicitly out of scope for v1.
- **D5 — Role matrix.** Stock mutations go under `/api/v2` with the existing role model:

  | Action | viewer | engineer | admin |
  |---|---|---|---|
  | View reports/dashboard | ✔ | ✔ | ✔ |
  | Receipt / Issue / Transfer | ✖ | ✔ | ✔ |
  | Manual reservation | ✖ | ✔ | ✔ |
  | Adjust (count correction) | ✖ | ✖ | ✔ (reason mandatory) |
  | Catalog / locations / tags admin | ✖ | ✔ | ✔ |

  (Classic routes must get the same enforcement — see bugs.md B2.)
- **D6 — Idempotency & concurrency.** Every stock event mutation accepts a client-generated `idempotency_key` (stored unique on the event row); repeated submits with the same key are no-ops. Balance updates happen in one short transaction with the movement (SQLite serializes writers); the service rejects events that would make the balance negative (unless the event type is an explicit adjustment).
- **D7 — Allocation rule (aggregate view).** When total demand exceeds available stock, allocate by: **earliest schedule due date first**, then make-items before buy-items. This exact rule is implemented once in a shared service; per-product views comply with it for analysis.
- **D8 — Tags reuse the existing taxonomy.** Do not build a second tagging system. Generalize the existing `Category`/`Tag` schema (currently manufacturer-scoped) into a shared taxonomy consumed by manufacturers, items and locations via typed link tables.

---

## 1. Item catalog

Per stock item, stored data:

- **Identifiers:** name; for BOM parts the existing `part_code` doubles as item code/SKU; barcode/QR deferred (v1.5+); image comes from the existing image system.
- **Item kind:** purchasable, made, raw material, consumable, packaging, tool.
- **Unit of count:** per D4 — one unit per item, same as BOM usage.
- **Specs & notes:** technical description, supplier, min/max stock (reorder point) — `min_stock`/`max_stock` columns per D1.
- **BOM link:** inherent for parts (`Part` is the item); inventory-only items have none.

Non-BOM items (spare screws, glue, gloves) live in `InventoryItem` and appear in the same dashboard views as parts.

---

## 2. Categories, tags and storage locations

**Classification** and **physical location** are separate concepts and stay separate:

### 2.1 Tags

Per D8: generalized existing `Category`/`Tag` tables + typed link tables (`item_tags`). Manageable, multiple per item: part kind (electronic/mechanical/...) , sourcing (purchased/made/consignment), origin, brand (linked to the existing manufacturer directory), material, ESD/fragile flags, priority. Tags must be creatable, editable, colorable and mergeable from the UI.

### 2.2 Locations

Structured hierarchy, not free text:

```
Warehouse → Zone → Shelf → Level → Bin
```

with a short scannable code like `A-03-02`.

- Unique, searchable location code (unique index).
- Stock tracked **per location** (an item can sit in two bins) → balances are held per (item, location) pair in the event summary, not only globally.
- Transfers between locations are ledger events (section 3).
- Shelf fill/capacity display and printable shelf labels: **deferred to v1.5** (see scope, section 8).

---

## 3. Stock ledger (event log)

**The balance never changes by editing a number; every change is an event.** Event types:

| Event | Purpose |
|---|---|
| Receipt | purchase, production input, return from repair |
| Opening balance | initial count at setup |
| Issue | consumption in production or sale |
| Transfer | movement between locations (from/to required) |
| Adjustment | physical count correction, reason mandatory, admin only |
| Return / Scrap | defective or returned goods |
| Reserve / Release | allocation for a schedule or manual hold / lifecycle per D3 |

Per event: item, quantity, from/to location, timestamp, user, reason or reference (schedule id, order number, invoice).

- **Reservations are separated from physical issue** (per D3) so the dashboard can always show what is on the shelf vs. what is committed vs. what remains available.
- Idempotency keys per D6; balances never go negative except via explicit admin adjustments.

---

## 4. Inventory reporting and BOM integration

### 4.1 Disaggregated figures per item

- **Physical stock:** sum across all locations.
- **Reserved:** committed to schedules/holds.
- **Available:** physical − reserved − defective/quarantined.
- **Required:** from BOM demand across active schedules (reuse `bom_calculation`, computed server-side per B19).
- **Shortage:** `max(0, required − available)`.

Computed server-side in a report service; the frontend never recomputes demand loops.

### 4.2 Report page

- Low-stock and shortage list: name, code, available, required, shortage, location.
- Filters: category, tag, location, manufacturer, status. Sorting and grouping by product/assembly/category.
- **Excel/CSV export** for reports and for the physical count sheet (printable, with count columns for pen & paper).
- All filtering/sorting happens server-side (per B19).

### 4.3 Shared-part calculation rule

A part used by several products is counted once. Two views, driven by the D7 allocation rule:

1. **Per-product view:** this product's shortage assuming the shared stock were allocated to it (analysis only — not for purchasing decisions).
2. **Warehouse view:** aggregate demand, one allocation pass per D7 (the purchasing-decision source).

Summing per-product shortages is explicitly forbidden in reports because it overstates the real shortage.

---

## 5. UX and experience

Goal: convey a physical warehouse feel, not a boring admin form.

- **Overview page:** status cards (item count, low-stock count, production shortages, recent movements).
- **Fast search** by name, code (part_code), location; instant results; keyboard-first.
- **Keyboard shortcuts from v1:** `q` = receipt, `w` = issue, `e` = transfer, `c` = count/adjust — the mobile/warehouse shell stays aligned with these actions as the four primary buttons.
- Prominent display of bin/shelf code and item status.
- **Status always color + icon + text** (accessibility, color-blind users — consistent with bugs.md B32/B40 single-source status classes).
- Simple charts: critical items and location fill (fill display minimal in v1; full shelf-visual deferred to v1.5).
- Warehouse feel: item thumbnail, shelf icon, movement animations on receipt/issue with clear confirmation.
- Light/dark themes via the existing CSS variables; full RTL; mobile/tablet friendly for on-floor counting.
- Per B29 lesson: every hidden-by-default field must have explicit show/hide logic — the inventory screens are built without static `display:none` surprises.

---

## 6. Additional ideas (prioritized backlog)

1. **Bulk Excel import/export** of items+balances for initial setup and stock counts (**promoted into v1** — without it, catalog setup is manual line-by-line).
2. Barcode/QR scanning by phone camera for receipt/issue and item lookup (v1.5).
3. Low-stock alerts and reorder suggestions from average consumption (v1.5; hooks exist via `email_notif.py` — respecting B25 fixes).
4. Movement history report with time/user filters (v1.5).
5. In-app/email notifications for critical shortages (v1.5, depends on 3 + B25).
6. Item and shelf label printing with QR (v2).
7. Inventory-vs-production-demand comparison dashboard per product (v1.5; the warehouse view of section 4.3 covers v1).

---

## 7. Specialized capabilities (later, only if needed)

- Batch/lot tracking and expiry dates.
- Per-unit serial numbers.
- Financial valuation (FIFO/weighted average).
- Multiple warehouses (the v1 location hierarchy keeps a warehouse root level, so multi-warehouse is a schema-compatible extension).

---

## 8. Version-1 scope

**Minimal but complete:**

- One warehouse with hierarchical locations (unique codes).
- Catalog: `Part` augmented per D1 + `InventoryItem` for non-BOM items.
- Tags via generalized shared taxonomy (D8).
- Blockchain event logging: receipt, issue, transfer, adjustment, reserve/release (with D3 lifecycle, D6 idempotency, D5 roles).
- Links to BOM: aggregate shortage report per D7 + per-product view.
- **Bulk Excel import/export of catalog and balances.**
- Reports: shortage list, movement history (basic), printable count sheet.

**Explicitly deferred to v1.5:** shelf capacity/fill display, printable shelf labels, barcode scanning, QR label printing, low-stock alert automation, comparison dashboard polish, reserving against non-schedule sources, merge-groups (`inventory_groups`).

**Not in v1 (from section 7):** lot/expiry, serials, financial valuation, multi-warehouse.

---

## 9. Migration from the current quantities

Handled cautiously, with lessons from the incomplete `migrate_data.py` (bugs.md B23):

1. **Dry-run on a copy** of the database first; produce a diff report (item count, balance totals before/after) — the run is accepted only when totals reconcile.
2. **Preview mapping:** list current parts side-by-side with proposed stock items (per D1 most parts map 1:1; only non-BOM items need new rows).
3. **Suspicion report:** duplicate names, inconsistent units/shapes, invalid balances (negative, null) — surfaced before any write.
4. **Explicit user approval before writing.**
5. **No silent rewriting:** existing `quantity` values seed the **opening balance events** (one "opening balance" event per item+location), so the ledger explains every number from day one. `Part.stock_quantity` cache is seeded from the same events.
6. **Rollback script included:** the migration backs up the DB file (same discipline as `bom_inventory_migration.py`) and can restore it.

---

## 10. Implementation steps

1. Data model: `InventoryItem`, `Location` (self-referencing FK + unique code), `StockMovement` (with `idempotency_key`, `schedule_id` nullable FK), plus D1 column additions on `Part`; generalized `Tag`/`Category` link tables (D8).
2. Service layer: balance maintenance (transactional cache per D2), demand aggregation + D7 allocation, shortage report builder.
3. APIs under `/api/v2` with the D5 role matrix; idempotent event endpoint.
4. Bulk Excel import/export (section 6.1).
5. UI: overview, catalog, locations, reports; keyboard shortcuts and RTL/themes from the start.
6. Migration with dry-run, reconciliation, approval, rollback (section 9).
7. Automated tests: correctness of shortage math incl. shared parts (per B10's nested-multiplier lessons), negative-balance rejection, idempotency replay, location code uniqueness, ledger history integrity, D3 reservation lifecycle (cancel/complete/TTL release), D5 role enforcement (viewer 403), migration reconciliation totals.

---

## 11. Definition of done (v1)

- Every balance shown can be traced to an event list; a recount action reconciles the cache with zero differences on a consistent DB.
- A viewer cannot mutate anything (403), an engineer can run receipts/issues/transfers, only an admin can adjust.
- Two clients submitting the same movement twice produce exactly one event.
- The aggregate warehouse report and per-product views never sum per-product shortages.
- The migration runs twice safely (idempotent, dry-run first, reconciled totals) on a copy before touching real data.
