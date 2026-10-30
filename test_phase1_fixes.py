"""Phase-1 regressions (bugs.md B4, B6, B8, B9, B10, B12); never the configured database."""
from unittest.mock import patch

import pytest
from sqlalchemy import text
from config import Config

with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'):
    import app as backend

from extensions import db
from models import (Assembly, Document, Image, NotificationLog, Part, Product,
                    ProductionSchedule, Stage, User, WorkOrder)


@pytest.fixture
def client():
    app = backend.app
    config = dict(app.config)
    keys = ('bom_inventory_schema_ready', 'manufacturer_schema_ready')
    flags = {key: app.extensions[key] for key in keys if key in app.extensions}
    try:
        app.config.update(TESTING=True, LOGIN_DISABLED=False)
        with app.app_context():
            assert db.engine.url.database == ':memory:'
            try:
                db.create_all()
                with db.engine.begin() as conn:
                    conn.execute(text('DROP TABLE IF EXISTS manufacturer_schema_state'))
                for key in keys:
                    app.extensions.pop(key, None)
                for role in ('admin', 'engineer', 'viewer'):
                    user = User(username=role, email=role + '@example.com', role=role)
                    user.set_password('test-password')
                    db.session.add(user)
                db.session.commit()
                test_client = app.test_client()
                login_as(test_client, 'admin')
                yield test_client
            finally:
                db.session.remove()
                db.drop_all()
                with db.engine.begin() as conn:
                    conn.execute(text('DROP TABLE IF EXISTS manufacturer_schema_state'))
    finally:
        app.config.clear()
        app.config.update(config)
        for key in keys:
            app.extensions.pop(key, None)
        app.extensions.update(flags)


def login_as(client, role):
    from flask import g
    g.pop('_login_user', None)
    user = User.query.filter_by(username=role).one()
    with client.session_transaction() as session:
        session.clear()
        session['_user_id'] = str(user.id)
        session['_fresh'] = True


def make_product():
    product = Product(name='Phase1 Product', quantity=0, order_count=0)
    db.session.add(product)
    db.session.commit()
    return product


def nested_chain(part_required=2, inner_required=3, outer_required=4):
    """Product → assembly (4×) → nested assembly (3×) → part (2×)."""
    product = make_product()
    outer = Assembly(product_id=product.id, name='Outer', quantity=0,
                     required_quantity=outer_required)
    db.session.add(outer)
    db.session.commit()
    inner = Assembly(product_id=product.id, parent_id=outer.id, name='Inner', quantity=0,
                     required_quantity=inner_required)
    db.session.add(inner)
    db.session.commit()
    part = Part(assembly_id=inner.id, name='Deep Part', quantity=0,
                required_quantity=part_required, part_type='make', status='not_started')
    db.session.add(part)
    db.session.commit()
    return product, outer, inner, part


# ───── B4 — no open redirect on /auth/login ─────

def test_b4_json_login_ignores_foreign_next(client):
    response = client.post('/auth/login?next=https://evil.example/x',
                           json={'username': 'admin', 'password': 'test-password'})
    assert response.status_code == 200
    assert response.get_json()['redirect'] == '/'


def test_b4_form_login_ignores_foreign_next(client):
    response = client.post('/auth/login?next=//evil.example',
                           data={'username': 'admin', 'password': 'test-password'})
    assert response.status_code == 302
    assert 'evil.example' not in response.headers['Location']


def test_b4_relative_next_is_honored(client):
    response = client.post('/auth/login?next=/settings',
                           json={'username': 'admin', 'password': 'test-password'})
    assert response.get_json()['redirect'] == '/settings'


# ───── B6 — tampered session id signs out instead of 500 ─────

@pytest.mark.parametrize('user_id', ['not-a-number', '999999', '1.5'])
def test_b6_tampered_session_id_signs_out(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session['_user_id'] = user_id
        session['_fresh'] = True
    response = client.get('/api/data')
    assert response.status_code in (301, 302), response.status_code


# ───── B8 — assembly name is validated ─────

def test_b8_assembly_without_name_is_rejected(client):
    product = make_product()
    for payload in ({'product_id': product.id},
                    {'product_id': product.id, 'name': '   '},
                    {'product_id': product.id, 'name': None}):
        response = client.post('/api/v2/assemblies', json=payload)
        assert response.status_code == 400, response.get_data(as_text=True)
        assert 'name' in response.get_json()['error']


def test_b8_assembly_rename_to_blank_is_rejected(client):
    _, outer, _, _ = nested_chain()
    response = client.put(f'/api/v2/assemblies/{outer.id}', json={'name': ''})
    assert response.status_code == 400
    with backend.app.app_context():
        assert db.session.get(Assembly, outer.id).name == 'Outer'


def test_b8_classic_blank_name_falls_back_to_default(client):
    response = client.post('/api/node', json={'type': 'product', 'name': '   ', 'parent': None})
    assert response.status_code == 200
    assert response.json['node']['name'] == 'بدون نام'


# ───── B9 — schedule creation validates its payload ─────

@pytest.mark.parametrize('path', ['/api/schedules', '/api/v2/schedules'])
def test_b9_schedule_rejects_bad_payloads(client, path):
    product = make_product()
    cases = [
        None,                                                        # no JSON body at all
        {'quantity': 1},                                             # no product
        {'product_id': 999999, 'quantity': 1},                       # unknown product
        {'product_id': product.id, 'quantity': -1},                  # negative
        {'product_id': product.id, 'quantity': 0},                   # zero
        {'product_id': product.id, 'quantity': 1.5},                 # float
        {'product_id': product.id, 'quantity': 1, 'start_date': 'not-a-date'},
        {'product_id': product.id, 'quantity': 1, 'status': 'bogus'},
        {'product_id': product.id, 'quantity': 1, 'priority': 'bogus'},
    ]
    for payload in cases:
        response = client.post(path, json=payload) if payload is not None else client.post(path)
        assert response.status_code == 400, (path, payload, response.status_code,
                                             response.get_data(as_text=True))
    with backend.app.app_context():
        assert ProductionSchedule.query.count() == 0


@pytest.mark.parametrize('path', ['/api/schedules', '/api/v2/schedules'])
def test_b9_schedule_accepts_valid_payload(client, path):
    product = make_product()
    response = client.post(path, json={'product_id': product.id, 'quantity': 3,
                                       'start_date': '2026-11-01T08:00:00',
                                       'end_date': None, 'notes': ''})
    assert response.status_code in (200, 201), response.get_data(as_text=True)
    with backend.app.app_context():
        schedule = ProductionSchedule.query.one()
        assert schedule.quantity == 3
        assert schedule.start_date.isoformat().startswith('2026-11-01')
        assert schedule.end_date is None


# ───── B12 — null dates clear instead of raising ─────

def test_b12_update_schedule_with_null_dates(client):
    product = make_product()
    created = client.post('/api/v2/schedules', json={
        'product_id': product.id, 'quantity': 2,
        'start_date': '2026-11-01T08:00:00', 'end_date': '2026-11-05T17:00:00'})
    schedule_id = created.get_json()['data']['id']
    response = client.put(f'/api/v2/schedules/{schedule_id}',
                          json={'start_date': None, 'end_date': None})
    assert response.status_code == 200, response.get_data(as_text=True)
    with backend.app.app_context():
        schedule = db.session.get(ProductionSchedule, schedule_id)
        assert schedule.start_date is None and schedule.end_date is None


def test_b12_update_schedule_rejects_bad_date_and_quantity(client):
    product = make_product()
    created = client.post('/api/v2/schedules', json={'product_id': product.id, 'quantity': 2})
    schedule_id = created.get_json()['data']['id']
    for payload in ({'start_date': 'yesterday'}, {'quantity': -5}, {'quantity': 0},
                    {'status': 'bogus'}):
        response = client.put(f'/api/v2/schedules/{schedule_id}', json=payload)
        assert response.status_code == 400, (payload, response.status_code)


# ───── B10 — work orders honour nested multipliers ─────

@pytest.mark.parametrize('path', ['/api/schedules', '/api/v2/schedules'])
def test_b10_nested_multipliers_for_work_orders(client, path):
    product, _, _, part = nested_chain()          # 4 × 3 × 2 per unit
    response = client.post(path, json={'product_id': product.id, 'quantity': 5})
    assert response.status_code in (200, 201), response.get_data(as_text=True)
    with backend.app.app_context():
        order = WorkOrder.query.filter_by(part_id=part.id).one()
        assert order.quantity == 120, order.quantity   # 4 × 3 × 2 × 5


# ───── B11 — pending work orders follow schedule quantity changes ─────

def test_b11_quantity_change_refreshes_pending_work_orders(client):
    product, _, _, part = nested_chain()          # 4 × 3 × 2 = 24 per unit
    created = client.post('/api/v2/schedules', json={'product_id': product.id, 'quantity': 20})
    schedule_id = created.get_json()['data']['id']
    with backend.app.app_context():
        assert WorkOrder.query.filter_by(part_id=part.id).one().quantity == 480
    response = client.put(f'/api/v2/schedules/{schedule_id}', json={'quantity': 50})
    assert response.status_code == 200, response.get_data(as_text=True)
    with backend.app.app_context():
        orders = WorkOrder.query.filter_by(part_id=part.id).all()
        assert len(orders) == 1, [o.quantity for o in orders]
        assert orders[0].quantity == 1200
        assert orders[0].status == 'pending'
        schedule = db.session.get(ProductionSchedule, schedule_id)
        assert '20 → 50' in schedule.notes


def test_b11_started_orders_are_kept_and_remainder_is_planned(client):
    product, _, _, part = nested_chain()
    created = client.post('/api/v2/schedules', json={'product_id': product.id, 'quantity': 20})
    schedule_id = created.get_json()['data']['id']
    with backend.app.app_context():
        order = WorkOrder.query.filter_by(part_id=part.id).one()
        order.status = 'in_progress'
        started_id, started_quantity = order.id, order.quantity
        db.session.commit()
    assert client.put(f'/api/v2/schedules/{schedule_id}',
                      json={'quantity': 50}).status_code == 200
    with backend.app.app_context():
        started = db.session.get(WorkOrder, started_id)
        assert started.quantity == started_quantity and started.status == 'in_progress'
        pending = WorkOrder.query.filter_by(part_id=part.id, status='pending').one()
        assert pending.quantity == 1200 - started_quantity


def test_b11_unrelated_update_keeps_orders_and_notes(client):
    product, _, _, part = nested_chain()
    created = client.post('/api/v2/schedules', json={'product_id': product.id, 'quantity': 20})
    schedule_id = created.get_json()['data']['id']
    with backend.app.app_context():
        original = [(o.id, o.quantity) for o in WorkOrder.query.all()]
    assert client.put(f'/api/v2/schedules/{schedule_id}',
                      json={'priority': 'high', 'notes': 'rush'}).status_code == 200
    with backend.app.app_context():
        assert [(o.id, o.quantity) for o in WorkOrder.query.all()] == original
        schedule = db.session.get(ProductionSchedule, schedule_id)
        assert schedule.notes == 'rush'
        assert schedule.priority == 'high'


# ───── B15 — deleting a node cleans files and orphan rows ─────

def test_b15_delete_product_cascades_files_documents_and_orders(client, tmp_path, monkeypatch):
    monkeypatch.setattr(backend, 'UPLOAD_DIR', tmp_path)
    product = make_product()
    assembly = Assembly(product_id=product.id, name='A', quantity=0, required_quantity=1)
    db.session.add(assembly)
    db.session.commit()
    part = Part(assembly_id=assembly.id, name='P', quantity=0, required_quantity=1,
                part_type='make', status='not_started')
    db.session.add(part)
    db.session.commit()
    db.session.add(Stage(part_id=part.id, name='Cut'))
    for name, kwargs in (('part-doc.pdf', {'part_id': part.id}),
                         ('asm-doc.pdf', {'assembly_id': assembly.id})):
        (tmp_path / name).write_bytes(b'%PDF')
        db.session.add(Document(filename=name, original_name=name, file_type='pdf', file_size=4,
                                url=f'/uploads/{name}', **kwargs))
    for name, kwargs in (('part-img.png', {'part_id': part.id}),
                         ('asm-img.png', {'assembly_id': assembly.id})):
        (tmp_path / name).write_bytes(b'PNG')
        db.session.add(Image(url=f'/uploads/{name}', label=name, **kwargs))
    # A row whose file is already gone must still be removed without erroring.
    db.session.add(Document(filename='ghost.pdf', url='/uploads/ghost.pdf', file_type='pdf'))
    db.session.add(NotificationLog(part_id=part.id, sent_to='ops@example.com', status='sent'))
    db.session.commit()
    created = client.post('/api/v2/schedules', json={'product_id': product.id, 'quantity': 3})
    assert created.status_code == 201
    schedule_id = created.get_json()['data']['id']

    response = client.delete(f'/api/node/p{product.id}')
    assert response.status_code == 200, response.get_data(as_text=True)
    removed = response.get_json()['removed']
    # The both-NULL "ghost" document has no owner (B14), so it is not attributed
    # to this product and must survive; its missing file is not an error either.
    assert removed == {'documents': 2, 'images': 2, 'files': 4, 'work_orders': 1,
                       'notifications': 1, 'schedules': 1}, removed
    assert sorted(p.name for p in tmp_path.iterdir()) == []
    with backend.app.app_context():
        for model in (Product, Assembly, Part, Stage, Image, NotificationLog,
                      ProductionSchedule, WorkOrder):
            assert model.query.count() == 0, model.__name__
        assert [d.filename for d in Document.query.all()] == ['ghost.pdf']
        assert db.session.get(ProductionSchedule, schedule_id) is None


def test_b15_delete_single_part_keeps_sibling_data(client, tmp_path, monkeypatch):
    monkeypatch.setattr(backend, 'UPLOAD_DIR', tmp_path)
    product = make_product()
    assembly = Assembly(product_id=product.id, name='A', quantity=0, required_quantity=1)
    db.session.add(assembly)
    db.session.commit()
    kept = Part(assembly_id=assembly.id, name='Keep', quantity=0, required_quantity=1,
                part_type='make', status='not_started')
    doomed = Part(assembly_id=assembly.id, name='Doomed', quantity=0, required_quantity=1,
                  part_type='make', status='not_started')
    db.session.add_all([kept, doomed])
    db.session.commit()
    for name, part in (('kept.pdf', kept), ('doomed.pdf', doomed)):
        (tmp_path / name).write_bytes(b'x')
        db.session.add(Document(filename=name, url=f'/uploads/{name}', part_id=part.id))
    db.session.commit()

    assert client.delete(f'/api/node/r{doomed.id}').status_code == 200
    assert (tmp_path / 'kept.pdf').is_file() and not (tmp_path / 'doomed.pdf').exists()
    with backend.app.app_context():
        assert Document.query.filter_by(part_id=doomed.id).count() == 0
        assert Document.query.filter_by(part_id=kept.id).count() == 1
        assert db.session.get(Part, kept.id) is not None
