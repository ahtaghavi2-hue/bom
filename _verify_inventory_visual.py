"""Temporary verification only: isolated SQLite memory and loopback port 5091."""
from pathlib import Path
from unittest.mock import patch
import json
import subprocess
import threading
from werkzeug.serving import make_server
from config import Config

ROOT = Path('F:/bom-system')
CHROME = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'):
    import app as backend
from extensions import db
from models import Product, Assembly, Part, Stage, StageDetail

app = backend.app
app.config.update(TESTING=True, LOGIN_DISABLED=True)
@app.route('/_verification_inventory')
def visual_page():
    return page

with app.app_context():
    assert db.engine.url.database == ':memory:'
    db.create_all()
    product = Product(name='محصول آزمایشی', order_count=10, quantity=2)
    db.session.add(product)
    db.session.flush()
    assembly = Assembly(name='مجموعه اصلی', product_id=product.id, quantity=4, required_quantity=3)
    db.session.add(assembly)
    db.session.flush()
    nested = Assembly(name='زیرمجموعه داخلی', product_id=product.id, parent_id=assembly.id, quantity=5, required_quantity=2)
    db.session.add(nested)
    db.session.flush()
    part = Part(name='قطعه آزمایشی', assembly_id=nested.id, quantity=7, required_quantity=4)
    db.session.add(part)
    db.session.commit()
    data = app.test_client().get('/api/data').json
    expected = [(10, 8), (24, 20), (40, 35), (140, 133)]
    for node_id, values in zip(['p1', 'a1', 'a2', 'r1'], expected):
        node = data['nodes'][node_id]
        assert (node['required_total'], node['shortage']) == values
    print('ISOLATED_SAMPLE', json.dumps({key: (n['required_total'], n['shortage']) for key, n in data['nodes'].items()}))
    # Confirm positional stage update concern using only the isolated test DB.
    first = Stage(part_id=part.id, name='First', sort_order=0)
    second = Stage(part_id=part.id, name='Second', sort_order=1)
    db.session.add_all([first, second])
    db.session.flush()
    detail = StageDetail(stage_id=first.id, description='Belongs to First')
    db.session.add(detail)
    db.session.commit()
    first_id, second_id = first.id, second.id
    response = app.test_client().put('/api/node/r1', json={'stages': [
        {'id': second_id, 'name': 'Second'}, {'id': first_id, 'name': 'First'}]})
    assert response.status_code == 200
    db.session.expire_all()
    print('STAGE_REORDER_CONCERN', db.session.get(Stage, first_id).name,
          db.session.get(StageDetail, detail.id).description)
    page = app.test_client().get('/').get_data(as_text=True)

# Keep existing scripts/template and block writes to browser storage for this verification.
page = page.replace('<head>', '<head><script>Storage.prototype.setItem=function(){};</script>', 1)
selection = """<script>
const visualTimer = setInterval(function() {
    if (!currentData.nodes.a1 || !$('#tree-container').jstree(true)) return;
    clearInterval(visualTimer);
    currentNodeId = 'a1';
    $('#tree-container').jstree('open_all');
    $('#tree-container').jstree('select_node', 'a1');
    showEditForm(currentData.nodes.a1);
    switchTab('tab-inventory');
    document.title = 'VERIFIED assembly coefficient=' + $('#field-required_quantity').val()
        + ' stock=' + $('#field-quantity').val() + ' total=' + $('#field-total_required').val()
        + ' ' + $('#shortage-text').text();
}, 100);
</script>"""
page = page.replace('</body>', selection + '</body>')

server = make_server('127.0.0.1', 5091, app)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    screenshot = ROOT / '_verify_inventory_assembly.png'
    result = subprocess.run([
        str(CHROME), '--headless=new', '--disable-gpu', '--incognito',
        '--no-first-run', '--no-default-browser-check', '--hide-scrollbars',
        '--window-size=1600,1000', '--virtual-time-budget=10000',
        '--screenshot=' + str(screenshot), '--dump-dom',
        'http://127.0.0.1:5091/_verification_inventory'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
    print('CHROME_EXIT', result.returncode)
    start = result.stdout.find('<title')
    end = result.stdout.find('</title>', start)
    print('BROWSER_TITLE', result.stdout[start:end + 8])
    print('SCREENSHOT', str(screenshot), screenshot.stat().st_size if screenshot.exists() else 'MISSING')
    if result.returncode or not screenshot.exists():
        print(result.stderr[-3000:])
    assert result.returncode == 0 and screenshot.exists()
finally:
    server.shutdown()
    thread.join(timeout=5)
    print('ISOLATED_SERVER_STOPPED')
