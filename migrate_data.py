"""
Migrate existing bom_data.json to SQLAlchemy database.
Run: python migrate_data.py
"""
import json
from pathlib import Path
from app import app, db
from models import Product, Assembly, Part, Stage, Image

DATA_FILE = Path("bom_data.json")

def migrate():
    if not DATA_FILE.exists():
        print('No bom_data.json found, skipping migration.')
        return
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    nodes = data.get('nodes', {})
    root_ids = data.get('root_ids', [])

    if Product.query.first():
        print('Database already has data. Skipping migration.')
        return

    node_map = {}

    for node_id, node_data in nodes.items():
        node_type = node_data.get('type')
        if node_type == 'product':
            product = Product(
                name=node_data.get('name', 'Product'),
                code=node_data.get('partCode', ''),
                description='',
                specs=node_data.get('specs', ''),
                notes=node_data.get('notes', ''),
                order_count=node_data.get('order_count', 0),
                status='active'
            )
            db.session.add(product)
            db.session.flush()
            node_map[node_id] = ('product', product.id)

    for node_id, node_data in nodes.items():
        node_type = node_data.get('type')
        if node_type == 'assembly':
            parent_id = node_data.get('parent')
            parent_type, parent_pk = node_map.get(parent_id, (None, None))
            if parent_type != 'product':
                continue
            assembly = Assembly(
                product_id=parent_pk,
                parent_id=None,
                name=node_data.get('name', 'Assembly'),
                description=node_data.get('notes', '')
            )
            db.session.add(assembly)
            db.session.flush()
            node_map[node_id] = ('assembly', assembly.id)

    for node_id, node_data in nodes.items():
        node_type = node_data.get('type')
        if node_type == 'part':
            parent_id = node_data.get('parent')
            parent_type, parent_pk = node_map.get(parent_id, (None, None))
            if parent_type not in ('assembly',):
                continue
            part = Part(
                assembly_id=parent_pk,
                name=node_data.get('name', 'Part'),
                part_code=node_data.get('partCode', ''),
                specs=node_data.get('specs', ''),
                part_type=node_data.get('partType', 'make'),
                quantity=node_data.get('quantity', 0),
                required_quantity=node_data.get('required_quantity', 1),
                supplier=node_data.get('supplier', ''),
                notes=node_data.get('notes', ''),
                status=node_data.get('status', 'not_started')
            )
            db.session.add(part)
            db.session.flush()
            node_map[node_id] = ('part', part.id)

            for img in node_data.get('images', []):
                image = Image(part_id=part.id, url=img.get('url', ''), label=img.get('label', ''))
                db.session.add(image)

            for idx, stage_data in enumerate(node_data.get('stages', [])):
                stage = Stage(
                    part_id=part.id,
                    name=stage_data.get('name', 'Stage'),
                    status=stage_data.get('status', 'not_started'),
                    sort_order=idx
                )
                db.session.add(stage)

    db.session.commit()
    print(f'Migration complete: {len(nodes)} nodes processed.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate()
