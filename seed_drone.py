"""Creates the drone (پهپاد) product BOM inside the app's main database.

By default it seeds into instance/bom_system.db (the same DB the app uses).
Override with DATABASE_URL if you want a separate DB, e.g.:
    $env:DATABASE_URL='sqlite:///drone_bom.db'; python seed_drone.py

Run:  python seed_drone.py
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DATABASE_URL', 'sqlite:///bom_system.db')

from app import app, db                               # noqa: E402
from models import (User, Product, Assembly, Part, Stage, StageDetail,   # noqa: E402
                    Manufacturer, ManufacturerEmail, ManufacturerPhone)


def make_user(username, role, password):
    existing = User.query.filter_by(username=username).first()
    if existing:
        return existing
    u = User(username=username, email=f'{username}@drone.com', role=role)
    u.set_password(password)
    db.session.add(u)
    return u


def make_assembly(product, name, description='', sort=0):
    a = Assembly(product_id=product.id, name=name, description=description, sort_order=sort)
    db.session.add(a)
    db.session.flush()
    return a


def make_part(assembly, name, code, specs='', part_type='make', qty=1, supplier='', notes='', sort=0):
    p = Part(
        assembly_id=assembly.id, name=name, part_code=code, specs=specs,
        part_type=part_type, quantity=qty, required_quantity=qty,
        supplier=supplier, notes=notes, status='not_started', sort_order=sort,
    )
    db.session.add(p)
    db.session.flush()
    stages = ['طراحی', 'تأمین مواد', 'ساخت', 'مونتاژ', 'تست و کنترل کیفیت']
    for i, s in enumerate(stages):
        st = Stage(part_id=p.id, name=s, status='not_started', sort_order=i,
                   estimated_material_cost=0.0, estimated_labor_cost=0.0, estimated_overhead=0.0)
        db.session.add(st)
        db.session.flush()
        sd = StageDetail(stage_id=st.id, step_number=1, description='اجرای مرحله ' + s)
        db.session.add(sd)
    return p


def seed():
    with app.app_context():
        db.create_all()

        admin = make_user('admin', 'admin', 'admin123')
        engineer = make_user('engineer', 'engineer', 'engineer123')
        viewer = make_user('viewer', 'viewer', 'viewer123')

        existing_drone = Product.query.filter_by(code='UAV-SKY-100').first()
        if existing_drone:
            print(f'Drone already exists in DB (id={existing_drone.id}), skipping product creation.')
            drone = existing_drone
        else:
            drone = Product(
                name='پهپاد چهارموتوره آسمان',
                code='UAV-SKY-100',
                description='پهپاد چهارموتوره جهت تصویربرداری و شناسایی',
                specs='مواد بدنه: کربن کامپوزیت | وزن پرواز: ۲.۴ کیلوگرم | زمان پرواز: ۳۵ دقیقه | برد کنترل: ۵ کیلومتر',
                status='active',
                created_by=admin.id,
            )
            db.session.add(drone)
            db.session.flush()

        if Product.query.filter_by(code='UAV-SKY-100').count() and \
                Assembly.query.join(Product).filter(Product.code == 'UAV-SKY-100').count():
            print('Drone BOM already seeded, nothing to do.')
            db.session.commit()
            return

        body = make_assembly(drone, 'بدنه و سازه', 'فریم مرکزی، بازوها و ارابه فرود', 0)
        airframe = make_assembly(drone, 'سیستم پیشرانش', 'موتور، ESC و ملخ', 1)
        elec = make_assembly(drone, 'الکترونیک پرواز', 'کنترلر پرواز، GPS و گیرنده', 2)
        camera = make_assembly(drone, 'سامانه تصویربرداری', 'گیمبال و دوربین', 3)
        power = make_assembly(drone, 'سامانه تأمین توان', 'باتری و ماژول توزیع', 4)

        make_part(body, 'فریم مرکزی', 'FRM-001', 'پلیت کربن 3K، ضخامت 2mm', 'make', 1, notes='ماشین‌کاری CNC')
        make_part(body, 'بازوی موتور', 'ARM-004', 'لوله کربن 16mm', 'make', 4)
        make_part(body, 'ارابه فرود', 'LG-002', 'فیبر کربن', 'buy', 1, supplier='کارگاه ارابه')
        make_part(body, 'پیچ و مهره مجموعه', 'HW-010', 'استیل A2', 'buy', 48, supplier='اتحاد یراق')

        make_part(airframe, 'موتور براشلس 2212', 'MT-2212', 'KV980، رانش 850g', 'buy', 4, supplier='الکتروموتور شرق')
        make_part(airframe, 'کنترل‌رنده سرعت (ESC) 30A', 'ESC-30', '30A، BLHeli', 'buy', 4, supplier='الکتروموتور شرق')
        make_part(airframe, 'ملخ 10×4.5', 'PRP-1045', 'پلاستیک پیشرفته', 'buy', 8, supplier='دورن وینگ')
        make_part(airframe, 'هاب ملخ', 'HUB-010', 'آلومینیوم CNC', 'make', 4)

        make_part(elec, 'کنترلر پرواز پیکس‌هاوک', 'FC-PX4', 'فروشگاه پیش‌فرض', 'buy', 1, supplier='بردهای پیشرو')
        make_part(elec, 'ماژول GPS با قطب‌نما', 'GPS-M8N', 'u-blox M8N', 'buy', 1, supplier='بردهای پیشرو')
        make_part(elec, 'گیرنده رادیویی 2.4GHz', 'RX-24G', '8 کانال', 'buy', 1, supplier='رادیو پارس')
        make_part(elec, 'سوئیچ ایمنی و بازر', 'SW-BZ', 'نصب روی فریم', 'make', 1)

        make_part(camera, 'گیمبال 2-محوره', 'GMB-2A', 'موتورهای ژیروسکوپی', 'buy', 1, supplier='آسمان‌گیمبال')
        make_part(camera, 'دوربین 4K اکشن', 'CAM-4K', 'سنسور 1/2.3', 'buy', 1, supplier='آسمان‌گیمبال')
        make_part(camera, 'فرستنده ویدیو 5.8GHz', 'VTX-58', '25-800mW', 'buy', 1, supplier='رادیو پارس')

        make_part(power, 'باتری لیتیوم 4S 5200mAh', 'BAT-4S', 'LiPo 14.8V', 'buy', 1, supplier='انرژی پاک')
        make_part(power, 'ماژول توزیع توان (PDB)', 'PDB-01', '5V/12V BEC', 'make', 1)

        # Manufacturers
        m1 = Manufacturer(name='الکتروموتور شرق', phone='09121234567', address='تهران', quality_score=88.0, delivery_days=5)
        m2 = Manufacturer(name='بردهای پیشرو', phone='09129876543', address='اصفهان', quality_score=92.0, delivery_days=3)
        m3 = Manufacturer(name='انرژی پاک', phone='09137778899', address='تبریز', quality_score=85.0, delivery_days=7)
        for m in (m1, m2, m3):
            db.session.add(m)
            db.session.flush()
        db.session.add_all([
            ManufacturerEmail(manufacturer_id=m1.id, email='sales@electromotor-east.com'),
            ManufacturerPhone(manufacturer_id=m1.id, phone='021-55667788'),
            ManufacturerEmail(manufacturer_id=m2.id, email='info@pishro-boards.com'),
            ManufacturerEmail(manufacturer_id=m3.id, email='sales@energy-clean.com'),
        ])

        db.session.commit()

        with app.app_context():
            prods = Product.query.count()
            asms = Assembly.query.count()
            pts = Part.query.count()
            sts = Stage.query.count()
            mfrs = Manufacturer.query.count()
            usrs = User.query.count()

        print('Database seeded:', os.environ.get('DATABASE_URL', 'sqlite:///bom_system.db'))
        print(f'  users={usrs} products={prods} assemblies={asms} parts={pts} stages={sts} manufacturers={mfrs}')
        print('  login: admin/admin123 | engineer/engineer123 | viewer/viewer123')
        print('  product: پهپاد چهارموتوره آسمان (UAV-SKY-100)')


if __name__ == '__main__':
    seed()