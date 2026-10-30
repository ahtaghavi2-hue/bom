"""Test-only subprocess entry point; configuration is isolated before app import."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

# The script now lives inside tests/; make the repository root importable again.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    parser.add_argument('--ready', required=True)
    parser.add_argument('--legacy', action='store_true')
    args = parser.parse_args()
    database = Path(args.database).resolve()
    ready = Path(args.ready).resolve()
    # Refuse repository databases even if the caller accidentally supplies one.
    root = Path(__file__).resolve().parent
    if database == root or root in database.parents:
        raise RuntimeError('The startup harness requires a temporary database outside the repository')
    if not database.parent.is_dir() or not ready.parent.is_dir():
        raise RuntimeError('Caller must create the temporary directories first')
    existed = database.exists()
    from config import Config
    with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///' + database.as_posix()), \
         patch.object(Config, 'UPLOAD_FOLDER', str(database.parent)), \
         patch.object(Config, 'SECRET_KEY', 'isolated-browser-startup-only'):
        import app as backend
    from extensions import db
    from models import Product, Assembly, Part, User, Stage, StageDetail
    from werkzeug.serving import make_server
    app = backend.app
    app.config.update(TESTING=True, LOGIN_DISABLED=False)
    # Authenticate a real fixture engineer on both browser and urllib requests.
    # LOGIN_DISABLED alone leaves AnonymousUser.role absent on V2 write routes.
    from extensions import login_manager
    @login_manager.request_loader
    def fixture_user(request):
        return db.session.get(User, 901)
    # Preserve the actual manufacturer migration, only redirect its optional
    # backup destination so test startup cannot write repository backups.
    if hasattr(backend, 'ensure_manufacturer_schema'):
        from functools import partial
        backend.ensure_manufacturer_schema = partial(backend.ensure_manufacturer_schema,
                                                     backup_dir=database.parent / 'backups')
    with app.app_context():
        assert Path(db.engine.url.database).resolve() == database
        if not existed:
            # Create a fixture schema, not app.init_db (which may seed/reset real data).
            db.create_all()
            db.session.add(User(id=901, username='browser-fixture-engineer',
                                email='browser-fixture@example.test',
                                password_hash='not-a-login-password', role='engineer'))
            db.session.add_all([
                Product(id=41, name='Startup Product Alpha', order_count=10, quantity=2),
                Product(id=73, name='محصول ماندگار Beta', order_count=0, quantity=9),
            ])
            db.session.flush()
            db.session.add(Assembly(id=51, product_id=41, name='Startup Assembly',
                                    quantity=4, required_quantity=3))
            db.session.flush()
            db.session.add(Assembly(id=52, product_id=41, parent_id=51,
                                    name='Startup Nested', quantity=5, required_quantity=2))
            db.session.flush()
            db.session.add(Part(id=61, assembly_id=52, name='Startup Part',
                                quantity=7, required_quantity=4))
            db.session.flush()
            db.session.add_all([
                Stage(id=81, part_id=61, name='Fixture machining', sort_order=0),
                Stage(id=82, part_id=61, name='Fixture finishing', sort_order=1),
            ])
            db.session.flush()
            db.session.add(StageDetail(id=91, stage_id=81, step_number=1,
                                       description='Preserve fixture machining detail'))
            db.session.commit()
        db.session.remove()
        db.engine.dispose()
    if args.legacy:
        if existed:
            raise RuntimeError('Legacy preparation may only modify a newly created fixture')
        with sqlite3.connect(database) as connection:
            for table, column in [('products', 'quantity'), ('assemblies', 'quantity'),
                                  ('assemblies', 'required_quantity')]:
                connection.execute(f'ALTER TABLE {table} DROP COLUMN {column}')
    # OS-assigned port avoids the reserve-close-rebind race between test workers.
    server = make_server('127.0.0.1', 0, app, threaded=True)
    ready.write_text(json.dumps({'url': f'http://127.0.0.1:{server.server_port}',
                                'database': str(database)}), encoding='utf-8')
    print('ISOLATED_SERVER_READY', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


if __name__ == '__main__':
    main()
