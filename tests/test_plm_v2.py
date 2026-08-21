"""End-to-end tests for the migrated /api/v2 PLM endpoints (versions + change requests).

Uses an isolated temporary SQLite DB so the existing instance/bom_system.db is untouched.

Run:  python tests/test_plm_v2.py
"""
import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

TEST_DB = os.path.join(tempfile.gettempdir(), 'test_plm_v2.db')
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
os.environ['DATABASE_URL'] = 'sqlite:///' + TEST_DB.replace(os.sep, '/')
os.environ.pop('SECRET_KEY', None)

from app import app, db                     # noqa: E402
from models import User, PartVersion, ChangeRequest  # noqa: E402

app.config['TESTING'] = True

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {detail}')


def make_user(username, role, password):
    u = User(username=username, email=f'{username}@test.com', role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


def login(client, username, password):
    r = client.post('/auth/login', json={'username': username, 'password': password})
    try:
        ok = r.get_json().get('success', False)
    except Exception:
        ok = False
    return r, ok


def main():
    with app.app_context():
        db.create_all()
        admin = make_user('admin', 'admin', 'admin123')
        engineer = make_user('engineer', 'engineer', 'engineer123')
        viewer = make_user('viewer', 'viewer', 'viewer123')

    c = app.test_client()

    # ── Auth guards ──
    r, ok = login(c, 'viewer', 'viewer123')
    check('viewer login', ok)
    r = c.post('/api/v2/products', json={'name': 'X'})
    check('viewer cannot create product (403)',
          r.status_code == 403, f'got {r.status_code}')
    c.get('/auth/logout')

    login(c, 'admin', 'admin123')

    # ── Build product → assembly → part (drone) ──
    r = c.post('/api/v2/products', json={
        'name': 'پهپاد شناسایی',
        'code': 'UAV-T100',
        'description': 'پهپاد چهار موتوره',
        'specs': 'وزن 2.5kg',
    })
    body = r.get_json()
    check('create product', r.status_code == 201 and body.get('success'), str(body))
    product_id = body['data']['id']

    r = c.post('/api/v2/assemblies', json={
        'product_id': product_id,
        'name': 'بدنه',
        'description': 'فریم و ارابه',
    })
    body = r.get_json()
    check('create assembly', r.status_code == 201 and body.get('success'), str(body))
    assembly_id = body['data']['id']

    r = c.post('/api/v2/parts', json={
        'assembly_id': assembly_id,
        'name': 'فریم مرکزی',
        'part_code': 'FMW-001',
        'specs': 'کربن',
        'part_type': 'make',
        'quantity': 1,
        'required_quantity': 1,
    })
    body = r.get_json()
    check('create part', r.status_code == 201 and body.get('success'), str(body))
    part_id = body['data']['id']

    # ── Versions ──
    r = c.post(f'/api/v2/parts/{part_id}/versions', json={'change_summary': 'نسخه اولیه'})
    body = r.get_json()
    check('create v1', r.status_code == 201 and body.get('success'), str(body))
    v1_id = body['data']['id']
    check('v1 active', body['data']['is_active'] is True)

    r = c.post(f'/api/v2/parts/{part_id}/versions', json={'change_summary': 'بهینه‌سازی وزن'})
    body = r.get_json()
    check('create v2', r.status_code == 201 and body.get('success'), str(body))
    v2_id = body['data']['id']
    check('v2 number=2', body['data']['version_number'] == 2)
    check('v2 active, v1 inactive',
          body['data']['is_active'] is True and body['data']['version_number'] == 2)

    r = c.get(f'/api/v2/parts/{part_id}/versions')
    body = r.get_json()
    check('list versions = 2', body.get('success') and len(body['data']) == 2, str(body))

    r = c.get(f'/api/v2/versions/{v1_id}')
    body = r.get_json()
    check('version detail', body.get('success') and body['data']['id'] == v1_id, str(body))

    r = c.post(f'/api/v2/versions/{v1_id}/activate')
    body = r.get_json()
    check('activate v1', body.get('success') and body['data']['is_active'] is True, str(body))

    r = c.get(f'/api/v2/parts/{part_id}/versions')
    versions = r.get_json()['data']
    active = [v for v in versions if v['is_active']]
    check('exactly one active after activation', len(active) == 1 and active[0]['id'] == v1_id)

    # ── Change requests ──
    c.get('/auth/logout')
    login(c, 'viewer', 'viewer123')
    r = c.post(f'/api/v2/parts/{part_id}/change-requests', json={
        'description': 'افزایش ضخامت فریم',
        'justification': 'نیاز به مقاومت بیشتر',
    })
    body = r.get_json()
    check('create change request', r.status_code == 201 and body.get('success'), str(body))
    cr_id = body['data']['id']
    check('requester_name = viewer', body['data'].get('requester_name') == 'viewer',
          str(body['data'].get('requester_name')))
    check('status pending', body['data']['status'] == 'pending')

    r = c.post(f'/api/v2/parts/{part_id}/change-requests', json={'description': '  '})
    check('missing description rejected (400)', r.status_code == 400, str(r.status_code))

    r = c.get(f'/api/v2/parts/{part_id}/change-requests')
    body = r.get_json()
    check('list change requests = 1', body.get('success') and len(body['data']) == 1, str(body))

    r = c.get(f'/api/v2/change-requests/{cr_id}')
    body = r.get_json()
    check('change request detail', body.get('success') and body['data']['id'] == cr_id, str(body))

    c.get('/auth/logout')
    login(c, 'engineer', 'engineer123')
    r = c.post(f'/api/v2/change-requests/{cr_id}/vote', json={'vote_type': 'approve'})
    body = r.get_json()
    check('engineer approve', body.get('success'), str(body))
    check('still pending (1 of 2)', body['data']['status'] == 'pending', str(body))

    c.get('/auth/logout')
    login(c, 'admin', 'admin123')
    r = c.post(f'/api/v2/change-requests/{cr_id}/vote', json={'vote_type': 'approve'})
    body = r.get_json()
    check('admin approve', body.get('success'), str(body))
    check('auto-approved by 2 votes', body['data']['status'] == 'approved', str(body))

    with app.app_context():
        cr = db.session.get(ChangeRequest, cr_id)
        check('record status approved in DB', cr.status.value == 'approved')

    with app.app_context():
        vers = PartVersion.query.filter_by(part_id=part_id).all()
        check('no auto-version created (versioning disabled)',
              len([v for v in vers if v.version_number > 2]) == 0, str(len(vers)))

    r = c.post(f'/api/v2/change-requests/{cr_id}/vote', json={'vote_type': 'reject'})
    check('duplicate vote rejected (400)', r.status_code == 400, str(r.status_code))

    c.get('/auth/logout')
    login(c, 'admin', 'admin123')
    r = c.put(f'/api/v2/change-requests/{cr_id}', json={'status': 'approved'})
    check('admin review (PUT approved)', r.status_code == 200, str(r.status_code))

    print(f'\nRESULT: {PASS} passed, {FAIL} failed')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())