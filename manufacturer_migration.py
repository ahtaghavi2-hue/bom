"""Additive manufacturer schema, online SQLite backup and one-time suggestions."""
from datetime import datetime
from pathlib import Path
import sqlite3
from threading import RLock
from sqlalchemy import inspect, text
from models import Category, Tag, manufacturer_tags, StageManufacturer

_lock = RLock()
_TABLES = (Category.__table__, Tag.__table__, manufacturer_tags, StageManufacturer.__table__)
_SUGGESTIONS = {
    'فرایند': ('برش', 'ماشین‌کاری', 'جوشکاری', 'رنگ'),
    'قیمت': ('اقتصادی', 'متوسط', 'بالا'),
    'کیفیت': ('معمولی', 'خوب', 'عالی'),
    'تحویل': ('سریع', 'معمولی', 'طولانی'),
}


def ensure_manufacturer_schema(engine, backup_dir=None):
    """Run before ORM access. Never seed again after the durable seed marker."""
    with _lock:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        add_active = 'manufacturers' in tables and 'is_active' not in {
            c['name'] for c in inspector.get_columns('manufacturers')}
        missing = any(t.name not in tables for t in _TABLES)
        marker_missing = 'manufacturer_schema_state' not in tables
        normalize = False
        if 'manufacturers' in tables and not add_active:
            with engine.connect() as conn:
                normalize = conn.execute(text('SELECT 1 FROM manufacturers WHERE is_active IS NULL LIMIT 1')).first() is not None
        if not (add_active or missing or marker_missing or normalize):
            return None
        backup = None
        if engine.dialect.name == 'sqlite' and engine.url.database not in (None, '', ':memory:'):
            database = Path(engine.url.database).resolve()
            directory = Path(backup_dir) if backup_dir else Path(__file__).resolve().parent / 'backups'
            directory.mkdir(parents=True, exist_ok=True)
            backup = str(directory / (database.name + '.manufacturers-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.sqlite'))
            with sqlite3.connect(str(database)) as source, sqlite3.connect(backup) as destination:
                source.backup(destination)
        with engine.begin() as conn:
            if add_active:
                conn.execute(text('ALTER TABLE manufacturers ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1'))
            if normalize:
                conn.execute(text('UPDATE manufacturers SET is_active = 1 WHERE is_active IS NULL'))
            for table in _TABLES:
                table.create(conn, checkfirst=True)
            conn.execute(text('CREATE TABLE IF NOT EXISTS manufacturer_schema_state (id INTEGER PRIMARY KEY)'))
            if not conn.execute(text('SELECT id FROM manufacturer_schema_state WHERE id = 1')).first():
                pristine = not conn.execute(Category.__table__.select().limit(1)).first() and not conn.execute(Tag.__table__.select().limit(1)).first()
                if pristine:
                    for name, tags in _SUGGESTIONS.items():
                        result = conn.execute(Category.__table__.insert().values(name=name))
                        category_id = result.inserted_primary_key[0]
                        conn.execute(Tag.__table__.insert(), [{'name': tag, 'category_id': category_id} for tag in tags])
                conn.execute(text('INSERT INTO manufacturer_schema_state (id) VALUES (1)'))
        return backup
