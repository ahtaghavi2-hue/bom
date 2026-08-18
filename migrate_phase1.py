"""
اسکریپت مهاجرت دیتابیس - فاز ۱
افزودن فیلدهای جدید برای زمان‌بندی پیشرفته و مدیریت منابع

این اسکریپت:
۱. فیلدهای PERT و زمان‌بندی را به جدول stages اضافه می‌کند
۲. فیلدهای تنظیمات پروژه را به جدول production_schedules اضافه می‌کند
۳. جداول جدید resources, resource_assignments, project_settings, schedule_scenarios را ایجاد می‌کند
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    Stage, ProductionSchedule, Resource, ResourceAssignment, 
    ProjectSettings, ScheduleScenario
)
from sqlalchemy import inspect

def check_column_exists(table_name, column_name):
    """بررسی وجود ستون در جدول"""
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(table_name):
    """بررسی وجود جدول"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def migrate():
    with app.app_context():
        print("=" * 60)
        print("شروع مهاجرت دیتابیس - فاز ۱")
        print("=" * 60)
        
        # ───── اجرای اولیه create_all برای اطمینان از وجود جداول پایه ─────
        print("\n📌 بخش ۰: ایجاد جداول پایه (در صورت عدم وجود)...")
        db.create_all()
        print("   ✓ جداول پایه ایجاد شدند")
        
        # ───── بخش ۱: افزودن فیلدهای جدید به جدول stages ─────
        print("\n📌 بخش ۱: به‌روزرسانی جدول stages...")
        
        stage_columns = [
            'time_optimistic', 'time_most_likely', 'time_pessimistic',
            'time_expected', 'time_variance', 'cost_material', 'cost_labor',
            'cost_overhead', 'storage_cost_per_day', 'required_resource_type',
            'resource_capacity_required', 'predecessor_ids', 'is_critical',
            'slack_time', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end'
        ]
        
        for col in stage_columns:
            if not check_column_exists('stages', col):
                print(f"   ✓ افزودن ستون {col} به جدول stages")
                # SQLAlchemy به صورت خودکار در create_all اضافه می‌کند
            else:
                print(f"   → ستون {col} از قبل وجود دارد")
        
        # ───── بخش ۲: افزودن فیلدهای جدید به جدول production_schedules ─────
        print("\n📌 بخش ۲: به‌روزرسانی جدول production_schedules...")
        
        schedule_columns = [
            'target_delivery_date', 'budget_limit', 'risk_tolerance',
            'resource_constraints', 'critical_path_duration', 'total_project_cost',
            'completion_probability', 'monte_carlo_runs'
        ]
        
        for col in schedule_columns:
            if not check_column_exists('production_schedules', col):
                print(f"   ✓ افزودن ستون {col} به جدول production_schedules")
            else:
                print(f"   → ستون {col} از قبل وجود دارد")
        
        # ───── بخش ۳: ایجاد جداول جدید ─────
        print("\n📌 بخش ۳: ایجاد جداول جدید...")
        
        new_tables = {
            'resources': 'جدول منابع کارگاه',
            'resource_assignments': 'جدول تخصیص منابع',
            'project_settings': 'جدول تنظیمات پروژه',
            'schedule_scenarios': 'جدول سناریوهای زمان‌بندی'
        }
        
        for table_name, description in new_tables.items():
            if not check_table_exists(table_name):
                print(f"   ✓ ایجاد {description} ({table_name})")
            else:
                print(f"   → جدول {table_name} از قبل وجود دارد")
        
        # ───── اجرای migration ─────
        print("\n📌 بخش ۴: اجرای مهاجرت دیتابیس...")
        
        try:
            # ایجاد تمام جداول و ستون‌های جدید
            db.create_all()
            print("   ✓ مهاجرت با موفقیت انجام شد")
        except Exception as e:
            print(f"   ✗ خطا در مهاجرت: {str(e)}")
            raise
        
        # ───── بخش ۵: ایجاد داده‌های نمونه ─────
        print("\n📌 بخش ۵: ایجاد داده‌های نمونه (در صورت نیاز)...")
        
        # بررسی وجود منابع نمونه
        if Resource.query.count() == 0:
            sample_resources = [
                Resource(name='دستگاه CNC 1', resource_type='machine', capacity=8.0, cost_per_hour=50000),
                Resource(name='دستگاه CNC 2', resource_type='machine', capacity=8.0, cost_per_hour=50000),
                Resource(name='اپراتور ماهر 1', resource_type='operator', capacity=8.0, cost_per_hour=30000),
                Resource(name='اپراتور ماهر 2', resource_type='operator', capacity=8.0, cost_per_hour=30000),
                Resource(name='فضای اسمبلی', resource_type='space', capacity=4.0, cost_per_hour=10000),
                Resource(name='ابزار دقیق', resource_type='tool', capacity=2.0, cost_per_hour=20000),
            ]
            
            for res in sample_resources:
                db.session.add(res)
            
            db.session.commit()
            print(f"   ✓ {len(sample_resources)} منبع نمونه ایجاد شد")
        else:
            print(f"   → {Resource.query.count()} منبع از قبل وجود دارد")
        
        # ───── خلاصه مهاجرت ─────
        print("\n" + "=" * 60)
        print("خلاصه مهاجرت:")
        print("=" * 60)
        print(f"   • تعداد منابع: {Resource.query.count()}")
        print(f"   • تعداد تخصیص‌ها: {ResourceAssignment.query.count()}")
        print(f"   • تعداد تنظیمات پروژه: {ProjectSettings.query.count()}")
        print(f"   • تعداد سناریوها: {ScheduleScenario.query.count()}")
        
        # نمایش فیلدهای جدید Stage
        stage_sample = Stage.query.first()
        if stage_sample:
            print("\n   فیلدهای جدید Stage:")
            print(f"      - time_optimistic: {stage_sample.time_optimistic}")
            print(f"      - time_most_likely: {stage_sample.time_most_likely}")
            print(f"      - time_pessimistic: {stage_sample.time_pessimistic}")
            print(f"      - pert_time_expected: {stage_sample.pert_time_expected}")
        
        print("\n✅ مهاجرت فاز ۱ با موفقیت کامل شد!")
        print("=" * 60)

if __name__ == '__main__':
    migrate()
