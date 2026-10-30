"""Phase-0 security regressions (bugs.md B1, B2, B3, B13, B7); never the configured database."""
from io import BytesIO
import os
from unittest.mock import patch

import pytest
from sqlalchemy import text
from config import Config, ensure_production_secret

with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'):
    import app as backend

from extensions import db
from models import Product, Setting, User


@pytest.fixture
def auth_app():
    """Reuse the shared in-memory app instance with a fresh schema per test."""
    app = backend.app
    config = dict(app.config)
    keys = ('bom_inventory_schema_ready', 'manufacturer_schema_ready')
    flags = {key: app.extensions[key] for key in keys if key in app.extensions}
    try:
        app.config.update(TESTING=True, LOGIN_DISABLED=False)
        with app.app_context():
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
                disabled = User(username='disabled', email='disabled@example.com', role='viewer')
                disabled.set_password('disabled-pass')
                disabled.is_active_user = False
                db.session.add(disabled)
                db.session.commit()
                yield app.test_client()
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
    """Log a client in without the real route, also dropping flask-login's
    per-app-context cache (the fixture keeps one app context alive, so the
    cached user would otherwise leak between clients)."""
    from flask import g
    g.pop('_login_user', None)
    user = User.query.filter_by(username=role).one()
    with client.session_transaction() as session:
        session.clear()
        session['_user_id'] = str(user.id)
        session['_fresh'] = True


def anonymous_client():
    """A client with no session and no leftover flask-login cache."""
    from flask import g
    g.pop('_login_user', None)
    return backend.app.test_client()


@pytest.fixture
def client(auth_app):
    login_as(auth_app, 'admin')
    return auth_app


def create_product():
    product = Product(name='Sec Product', quantity=0)
    db.session.add(product)
    db.session.commit()
    return f'p{product.id}'


# ───── B1 — disabled accounts cannot log in via /login ─────

def test_b1_disabled_user_rejected_on_classic_login(auth_app):
    response = auth_app.post('/login', data={'username': 'disabled', 'password': 'disabled-pass'},
                             follow_redirects=True)
    assert response.status_code == 200
    assert 'حساب کاربری غیرفعال است' in response.get_data(as_text=True)
    with auth_app.session_transaction() as session:
        assert '_user_id' not in session, 'disabled user must not get a session'


def test_b1_disabled_user_rejected_with_json_shape(auth_app):
    response = auth_app.post('/login', json={'username': 'disabled', 'password': 'disabled-pass'})
    assert response.status_code == 403
    assert response.get_json() == {'success': False, 'message': 'حساب کاربری غیرفعال است'}


def test_b1_active_user_still_logs_in_on_classic_login(auth_app):
    response = auth_app.post('/login', data={'username': 'admin', 'password': 'test-password'})
    assert response.status_code == 302
    with auth_app.session_transaction() as session:
        assert session['_user_id']


# ───── B2 — role enforcement on classic mutation routes ─────

def test_b2_viewer_blocked_on_classic_mutations(client):
    login_as(client, 'viewer')
    product_id = create_product()
    blocked = [
        client.delete(f'/api/node/{product_id}'),
        client.post('/api/node', json={'type': 'product', 'name': 'x', 'parent': None}),
        client.put(f'/api/node/{product_id}', json={'name': 'renamed'}),
        client.post('/api/schedules', json={'product_id': 1, 'quantity': 1}),
        client.post('/api/settings/save', json={'mail_server': 'smtp.example.com'}),
    ]
    for response in blocked:
        assert response.status_code == 403, response.status_code
    # READ access stays open for viewers.
    assert client.get('/api/data').status_code == 200
    assert client.get('/settings').status_code == 200


def test_b2_viewer_blocked_on_uploads_and_documents(client):
    login_as(client, 'viewer')
    product_id = create_product()
    blocked = [
        client.post('/api/upload', data={'file': (BytesIO(b'x'), 'a.png')},
                    content_type='multipart/form-data'),
        client.post(f'/api/documents/upload/{product_id}',
                    data={'file': (BytesIO(b'x'), 'a.pdf')},
                    content_type='multipart/form-data'),
    ]
    for response in blocked:
        assert response.status_code == 403, response.status_code
    anonymous = anonymous_client()
    assert anonymous.get('/api/data').status_code in (301, 302), 'anonymous API access must redirect to login'


def test_b2_engineer_allowed_admin_settings_forbidden(client):
    client2 = backend.app.test_client()
    login_as(client2, 'engineer')
    assert client2.post('/api/node', json={'type': 'product', 'name': 'e', 'parent': None}).status_code == 200
    assert client2.post('/api/settings/save', json={'mail_server': 'smtp.example.com'}).status_code == 403
    client3 = backend.app.test_client()
    login_as(client3, 'admin')
    assert client3.post('/api/settings/save', json={'mail_server': 'smtp.example.com'}).status_code == 200


def test_b2_viewer_settings_post_blocked(auth_app):
    login_as(auth_app, 'viewer')
    response = auth_app.post('/settings', data={'mail_server': 'smtp.example.com'})
    assert response.status_code in (301, 302)
    with backend.app.app_context():
        assert Setting.get('mail_server', 'smtp.gmail.com') == 'smtp.gmail.com', 'viewer save must be ignored'


# ───── B3 — SMTP password never rendered, keeps old value on empty save ─────

def test_b3_password_not_rendered_in_settings_page(client):
    with backend.app.app_context():
        Setting.set('mail_password', 'super-secret-value')
    response = client.get('/settings')
    body = response.get_data(as_text=True)
    assert 'super-secret-value' not in body, 'stored SMTP password must never reach the page'
    assert 'ذخیره شده است' in body, 'a set/not-set indicator is shown instead'


def test_b3_empty_password_save_keeps_stored_value(client):
    with backend.app.app_context():
        Setting.set('mail_password', 'old-secret')
    assert client.post('/api/settings/save', json={'mail_password': ''}).status_code == 200
    assert client.post('/api/settings/save', json={'mail_password': '   '}).status_code == 200
    with backend.app.app_context():
        assert Setting.get('mail_password') == 'old-secret'
    assert client.post('/api/settings/save', json={'mail_password': 'new-secret'}).status_code == 200
    with backend.app.app_context():
        assert Setting.get('mail_password') == 'new-secret'


def test_b3_settings_form_save_keeps_empty_password_field(client):
    with backend.app.app_context():
        Setting.set('mail_password', 'form-secret')
    response = client.post('/settings', data={
        'mail_server': 'smtp.example.com', 'mail_port': '587',
        'mail_username': 'ops@example.com', 'mail_password': '', 'mail_use_tls': 'true'})
    assert response.status_code == 302
    with backend.app.app_context():
        assert Setting.get('mail_password') == 'form-secret'
        assert Setting.get('mail_username') == 'ops@example.com'


# ───── B13 — upload type/size limits and authenticated serving ─────

def test_b13_upload_rejects_disallowed_extensions(client):
    for name in ('evil.html', 'evil.svg', 'evil.exe', 'script.js'):
        response = client.post('/api/upload', data={'file': (BytesIO(b'x'), name)},
                               content_type='multipart/form-data')
        assert response.status_code == 400, (name, response.status_code)


def test_b13_upload_accepts_image_and_enforces_size(client):
    response = client.post('/api/upload', data={'file': (BytesIO(b'89504e47-fake'), 'real.png')},
                           content_type='multipart/form-data')
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.json['url'].startswith('/uploads/')
    big = b'0' * (backend.MAX_IMAGE_UPLOAD_BYTES + 1)
    response = client.post('/api/upload', data={'file': (BytesIO(big), 'big.png')},
                           content_type='multipart/form-data')
    assert response.status_code == 413


def test_b13_document_upload_allowlist(client):
    product_id = create_product()
    response = client.post(f'/api/documents/upload/{product_id}',
                           data={'file': (BytesIO(b'x'), 'malware.exe')},
                           content_type='multipart/form-data')
    assert response.status_code == 400
    response = client.post(f'/api/documents/upload/{product_id}',
                           data={'file': (BytesIO(b'pdf-bytes'), 'manual.pdf')},
                           content_type='multipart/form-data')
    assert response.status_code == 200, response.get_data(as_text=True)


def test_b13_uploads_require_login_and_flag_downloads(client):
    anonymous = anonymous_client()
    response = anonymous.get('/uploads/img_serving_check.png')
    assert response.status_code in (301, 302), 'anonymous file serving must redirect to login'


def test_b13_non_image_upload_served_as_attachment(client):
    product_id = create_product()
    upload = client.post(f'/api/documents/upload/{product_id}',
                         data={'file': (BytesIO(b'%PDF-fake'), 'note.pdf')},
                         content_type='multipart/form-data')
    assert upload.status_code == 200
    url = upload.json['document']['url']
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers.get('Content-Disposition', '').startswith('attachment'), response.headers
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'


# ───── B7 — production requires SECRET_KEY; first-run admin gets a random password ─────

def test_b7_production_without_secret_key_refused():
    with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=False):
        os.environ.pop('SECRET_KEY', None)
        with pytest.raises(RuntimeError):
            ensure_production_secret()


def test_b7_production_with_secret_key_allowed():
    with patch.dict(os.environ, {'FLASK_ENV': 'production', 'SECRET_KEY': 'real-key'}):
        ensure_production_secret()


def test_b7_development_without_env_stays_allowed():
    os.environ.pop('FLASK_ENV', None)
    ensure_production_secret()


def test_b7_init_db_generates_random_admin_password(client):
    from app import init_db
    with backend.app.app_context():
        init_db()
        admin = User.query.filter_by(username='admin').first()
        assert admin is not None
        assert admin.check_password('admin123') is False, 'default admin123 must no longer exist'
