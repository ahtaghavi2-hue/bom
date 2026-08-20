from app import app, db
from models import *
from sqlalchemy import text

with app.app_context():
    db.create_all()

    inspector = db.inspect(db.engine)
    part_cols = [c['name'] for c in inspector.get_columns('parts')]
    if 'vector_embedding' not in part_cols:
        db.session.execute(text('ALTER TABLE parts ADD COLUMN vector_embedding TEXT'))
        print('[OK] Added parts.vector_embedding')

    mfr_cols = [c['name'] for c in inspector.get_columns('manufacturers')]
    for col, ddl in [
        ('quality_score', 'FLOAT DEFAULT 70.0'),
        ('reliability_score', 'FLOAT DEFAULT 70.0'),
        ('delivery_days', 'INTEGER DEFAULT 7'),
        ('rating_count', 'INTEGER DEFAULT 0'),
    ]:
        if col not in mfr_cols:
            db.session.execute(text(f'ALTER TABLE manufacturers ADD COLUMN {col} {ddl}'))
            print(f'[OK] Added manufacturers.{col}')

    db.session.commit()
    print('AI migration completed')
