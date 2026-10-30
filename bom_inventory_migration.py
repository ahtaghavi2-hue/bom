"""Additive inventory migration; SQLite is backed up before any changes."""
from datetime import datetime
from pathlib import Path
import sqlite3
from threading import RLock
from sqlalchemy import inspect, text

_lock = RLock()
_COLUMNS = {
    'products': {'quantity': 0},
    'assemblies': {'quantity': 0, 'required_quantity': 1},
    'parts': {'quantity': 0, 'required_quantity': 1},
}


def ensure_inventory_schema(engine):
    """Preserve existing values/records, normalize NULLs, and return backup path.

    No tables are created or replaced here. In-memory test databases need no
    backup. File-backed SQLite uses its online backup API (including WAL data).
    """
    with _lock:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        changes = []
        with engine.connect() as connection:
            for table, columns in _COLUMNS.items():
                if table not in tables:
                    continue
                existing = {column['name'] for column in inspector.get_columns(table)}
                for column, default in columns.items():
                    if column not in existing:
                        changes.append(f'ALTER TABLE {table} ADD COLUMN {column} INTEGER DEFAULT {default}')
                    elif connection.execute(text(
                        f'SELECT 1 FROM {table} WHERE {column} IS NULL LIMIT 1'
                    )).first():
                        changes.append(f'UPDATE {table} SET {column} = {default} WHERE {column} IS NULL')
        if not changes:
            return None
        backup_path = None
        if engine.dialect.name == 'sqlite' and engine.url.database not in (None, '', ':memory:'):
            database = Path(engine.url.database).resolve()
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            backup_path = str(database.with_name(f'{database.name}.inventory-backup-{stamp}.sqlite'))
            # Backup failure aborts the migration, before executing any DDL/DML.
            with sqlite3.connect(str(database)) as source, sqlite3.connect(backup_path) as destination:
                source.backup(destination)
        with engine.begin() as connection:
            for statement in changes:
                connection.execute(text(statement))
        return backup_path
