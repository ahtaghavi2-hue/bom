"""Seed Phase 1 scheduling data for the drone (UAV-SKY-100) product.

Populates:
  - PERT time estimates on Parts that have stages
  - Resource definitions (CNC, Assembly, QC, etc.)
  - ProjectSettings for the drone product
  - Two named scenarios with per-part overrides

Prerequisite:  python seed_drone.py   (creates the drone BOM first)

Run:  python seed_scheduling.py
"""

import os, sys, random

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DATABASE_URL', 'sqlite:///bom_system.db')

from datetime import datetime, timedelta
from app import app, db
from models import (
    Product, Part, Stage, Resource, ResourceAssignment,
    ProjectSettings, Scenario, ScenarioOverride, ScheduleResult,
)

# ── Resource definitions ──────────────────────────────────────────────

RESOURCE_DEFS = [
    # (name, type, capacity, shift_hours, cost_per_hour, notes)
    (' CNC Router — T6',          'CNC',         2,  8.0, 45.0, 'primary CNC for carbon fibre'),
    ('CNC Mill — VMC-850',        'CNC',         1,  8.0, 55.0, 'aluminium parts'),
    ('Assembly Bench A',          'Assembly',     4,  8.0, 25.0, 'general assembly'),
    ('Assembly Bench B',          'Assembly',     2,  8.0, 25.0, 'electronics integration'),
    ('QC Station',                'QC',           2,  8.0, 30.0, 'dimensional + functional test'),
    ('Soldering & Electronics',   'Electronics',  2,  8.0, 20.0, 'PCB soldering & wiring harness'),
    ('Paint & Finish',            'Finish',       1,  8.0, 15.0, 'surface coating'),
    ('Test Flight Area',          'Test',         1,  4.0, 60.0, 'limited hours per day'),
]

# ── PERT-like time estimates (hours) per Part name ────────────────────
# (optimistic, most_likely, pessimistic)

PERT_TIMES = {
    'فریم مرکزی':           (12, 18, 30),
    'بازوی موتور':           ( 4,  6, 12),
    'ارابه فرود':            ( 3,  5,  8),
    'پیچ و مهره مجموعه':     ( 1,  2,  4),
    'موتور براشلس 2212':     ( 0.5, 1, 2),      # bought – assembly only
    'کنترل‌رنده سرعت (ESC) 30A': (0.5, 1, 2),
    'ملخ 10×4.5':            ( 0.25, 0.5, 1),
    'هاب ملخ':                ( 2,  3,  5),
    'کنترلر پرواز پیکس‌هاوک': (0.5, 1, 2),
    'ماژول GPS با قطب‌نما':    (0.5, 1, 1.5),
    'گیرنده رادیویی 2.4GHz':   (0.5, 1, 2),
    'سوئیچ ایمنی و بازر':      ( 1,  2,  4),
    'گیمبال 2-محوره':          ( 2,  4,  8),
    'دوربین 4K اکشن':          ( 0.5, 1, 2),
    'فرستنده ویدیو 5.8GHz':    ( 0.5, 1, 2),
    'باتری لیتیوم 4S 5200mAh': (0.5, 1, 1.5),
    'ماژول توزیع توان (PDB)':  ( 1,  2,  4),
}

# Cost estimates (material, labor, overhead) per Part name
COST_ESTIMATES = {
    'فریم مرکزی':           (450000, 350000, 120000),
    'بازوی موتور':           ( 80000,  60000,  30000),
    'ارابه فرود':            (120000,  40000,  20000),
    'پیچ و مهره مجموعه':     ( 25000,   5000,  10000),
    'موتور براشلس 2212':     (960000,  30000,  20000),
    'کنترل‌رنده سرعت (ESC) 30A': (720000, 20000, 15000),
    'ملخ 10×4.5':            ( 64000,   5000,   5000),
    'هاب ملخ':                ( 80000,  60000,  30000),
    'کنترلر پرواز پیکس‌هاوک': (2200000, 50000, 30000),
    'ماژول GPS با قطب‌نما':    (800000,  30000,  20000),
    'گیرنده رادیویی 2.4GHz':   (350000,  20000,  15000),
    'سوئیچ ایمنی و بازر':      ( 45000,  30000,  15000),
    'گیمبال 2-محوره':          (1800000, 120000, 60000),
    'دوربین 4K اکشن':          (3200000,  40000, 30000),
    'فرستنده ویدیو 5.8GHz':    (600000,  30000,  20000),
    'باتری لیتیوم 4S 5200mAh': (1500000, 20000, 15000),
    'ماژول توزیع توان (PDB)':  ( 80000,  40000,  20000),
}

# Required resource type per Part name
RESOURCE_MAP = {
    'فریم مرکزی':           'CNC',
    'بازوی موتور':           'CNC',
    'هاب ملخ':                'CNC',
    'سوئیچ ایمنی و بازر':      'Assembly',
    'پیچ و مهره مجموعه':     'Assembly',
    'ارابه فرود':            'Assembly',
    'موتور براشلس 2212':     'Assembly',
    'کنترل‌رنده سرعت (ESC) 30A': 'Assembly',
    'ملخ 10×4.5':            'Assembly',
    'کنترلر پرواز پیکس‌هاوک': 'Electronics',
    'ماژول GPS با قطب‌نما':    'Electronics',
    'گیرنده رادیویی 2.4GHz':   'Electronics',
    'گیمبال 2-محوره':          'Assembly',
    'دوربین 4K اکشن':          'Assembly',
    'فرستنده ویدیو 5.8GHz':    'Electronics',
    'باتری لیتیوم 4S 5200mAh': 'Assembly',
    'ماژول توزیع توان (PDB)':  'Electronics',
}

# Storage cost per day (IRR) for parts that have lead time
STORAGE_COSTS = {
    'موتور براشلس 2212': 5000,
    'کنترل‌رنده سرعت (ESC) 30A': 3000,
    'کنترلر پرواز پیکس‌هاوک': 8000,
    'ماژول GPS با قطب‌نما': 5000,
    'گیرنده رادیویی 2.4GHz': 3000,
    'گیمبال 2-محوره': 8000,
    'دوربین 4K اکشن': 12000,
    'فرستنده ویدیو 5.8GHz': 4000,
    'باتری لیتیوم 4S 5200mAh': 10000,
}


def seed():
    with app.app_context():
        db.create_all()

        drone = Product.query.filter_by(code='UAV-SKY-100').first()
        if not drone:
            print('ERROR: Drone product not found. Run seed_drone.py first.')
            return

        # ── 1. Populate Part fields ───────────────────────────────────
        parts_updated = 0
        for part in Part.query.all():
            changes = False
            name = part.name

            if name in PERT_TIMES:
                o, m, p = PERT_TIMES[name]
                part.time_optimistic = o
                part.time_most_likely = m
                part.time_pessimistic = p
                changes = True

            if name in COST_ESTIMATES:
                mat, lab, ovh = COST_ESTIMATES[name]
                part.cost_material = mat
                part.cost_labor = lab
                part.cost_overhead = ovh
                changes = True

            if name in RESOURCE_MAP:
                part.required_resource_type = RESOURCE_MAP[name]
                changes = True

            if name in STORAGE_COSTS:
                part.storage_cost_per_day = STORAGE_COSTS[name]
                changes = True

            if changes:
                parts_updated += 1
        db.session.commit()
        print(f'  Parts updated: {parts_updated}')

        # ── 2. Resources ──────────────────────────────────────────────
        resources_created = 0
        for name, rtype, cap, shift, cost, notes in RESOURCE_DEFS:
            existing = Resource.query.filter_by(name=name).first()
            if not existing:
                db.session.add(Resource(
                    name=name, resource_type=rtype, capacity=cap,
                    shift_hours=shift, cost_per_hour=cost, notes=notes,
                ))
                resources_created += 1
        db.session.commit()
        print(f'  Resources created: {resources_created}')
        print(f'  Resources total:   {Resource.query.count()}')

        # ── 3. ProjectSettings ────────────────────────────────────────
        if not ProjectSettings.query.filter_by(product_id=drone.id).first():
            deadline = datetime.utcnow() + timedelta(days=90)
            db.session.add(ProjectSettings(
                product_id=drone.id,
                target_delivery_date=deadline,
                daily_penalty=2_000_000,          # 2M IRR per day late
                total_budget=150_000_000,          # 150M IRR
                risk_reserve_pct=12.0,
                monte_carlo_runs=1000,
            ))
            db.session.commit()
            print(f'  ProjectSettings created for {drone.name}')
        else:
            print('  ProjectSettings already exists, skipping')

        # ── 4. Scenarios ──────────────────────────────────────────────
        base_scenario = Scenario.query.filter_by(
            product_id=drone.id, is_default=True
        ).first()
        if not base_scenario:
            base_scenario = Scenario(
                product_id=drone.id,
                name='سناریوی پایه (Base)',
                description='بدون تغییر پارامترها – حالت عادی',
                is_default=True,
            )
            db.session.add(base_scenario)
            db.session.flush()
            print('  Scenario "Base" created')

            # Create optimistic scenario
            optimistic = Scenario(
                product_id=drone.id,
                name='سناریوی خوش‌بینانه (Optimistic)',
                description='زمان‌ها 20% کمتر، هزینه‌ها 10% کمتر',
            )
            db.session.add(optimistic)
            db.session.flush()

            # Create pessimistic / resource shortage scenario
            pessimistic = Scenario(
                product_id=drone.id,
                name='سناریوی کمبود منبع (Resource Shortage)',
                description='ظرفیت CNC نصف شده، زمان‌ها 30% بیشتر',
            )
            db.session.add(pessimistic)
            db.session.flush()

            # Add overrides for optimistic scenario
            for part in Part.query.filter(Part.time_most_likely.isnot(None)).all():
                db.session.add(ScenarioOverride(
                    scenario_id=optimistic.id, part_id=part.id,
                    field_name='time_optimistic',
                    field_value=(part.time_optimistic or 1) * 0.8,
                ))
                db.session.add(ScenarioOverride(
                    scenario_id=optimistic.id, part_id=part.id,
                    field_name='time_most_likely',
                    field_value=(part.time_most_likely or 1) * 0.8,
                ))
                db.session.add(ScenarioOverride(
                    scenario_id=optimistic.id, part_id=part.id,
                    field_name='cost_material',
                    field_value=(part.cost_material or 0) * 0.9,
                ))

            # Add overrides for pessimistic scenario
            for part in Part.query.filter(Part.time_most_likely.isnot(None)).all():
                db.session.add(ScenarioOverride(
                    scenario_id=pessimistic.id, part_id=part.id,
                    field_name='time_most_likely',
                    field_value=(part.time_most_likely or 1) * 1.3,
                ))
                db.session.add(ScenarioOverride(
                    scenario_id=pessimistic.id, part_id=part.id,
                    field_name='time_pessimistic',
                    field_value=(part.time_pessimistic or 1) * 1.4,
                ))
                db.session.add(ScenarioOverride(
                    scenario_id=pessimistic.id, part_id=part.id,
                    field_name='cost_material',
                    field_value=(part.cost_material or 0) * 1.15,
                ))

            db.session.commit()
            print(f'  Scenarios created: {Scenario.query.filter_by(product_id=drone.id).count()}')
        else:
            print('  Scenarios already exist, skipping')

        # ── Summary ───────────────────────────────────────────────────
        print()
        print('  === Phase 1 Seed Summary ===')
        print(f'  Products:       {Product.query.count()}')
        print(f'  Parts:          {Part.query.count()}')
        print(f'  Stages:         {Stage.query.count()}')
        print(f'  Resources:      {Resource.query.count()}')
        print(f'  Scenarios:      {Scenario.query.count()}')
        print(f'  Settings:       {ProjectSettings.query.count()}')
        print(f'  Login: admin / admin123')
        print(f'  Product: {drone.name} ({drone.code})')


if __name__ == '__main__':
    seed()
