from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='viewer')
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    products = db.relationship('Product', backref='creator', lazy='dynamic')
    schedules = db.relationship('ProductionSchedule', backref='creator', lazy='dynamic')
    work_orders = db.relationship('WorkOrder', backref='assignee', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(100))
    description = db.Column(db.Text)
    specs = db.Column(db.Text)
    notes = db.Column(db.Text)
    order_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assemblies = db.relationship('Assembly', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('ProductionSchedule', backref='product', lazy='dynamic', cascade='all, delete-orphan')

class Assembly(db.Model):
    __tablename__ = 'assemblies'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    children = db.relationship('Assembly', backref=db.backref('parent', remote_side='Assembly.id'))
    parts = db.relationship('Part', backref='assembly', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('Image', backref='assembly_ref', lazy='dynamic',
                             primaryjoin='and_(Image.assembly_id==Assembly.id, Image.part_id==None)',
                             cascade='all, delete-orphan')

class Part(db.Model):
    __tablename__ = 'parts'
    id = db.Column(db.Integer, primary_key=True)
    assembly_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    part_code = db.Column(db.String(100))
    specs = db.Column(db.Text)
    part_type = db.Column(db.String(20), default='make')
    quantity = db.Column(db.Integer, default=0)
    required_quantity = db.Column(db.Integer, default=1)
    supplier = db.Column(db.String(200))
    supplier_email = db.Column(db.String(200))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='not_started')
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stages = db.relationship('Stage', backref='part', lazy='dynamic', cascade='all, delete-orphan',
                             order_by='Stage.sort_order')
    images = db.relationship('Image', backref='part_ref', lazy='dynamic',
                             primaryjoin='and_(Image.part_id==Part.id, Image.assembly_id==None)',
                             cascade='all, delete-orphan')
    work_orders = db.relationship('WorkOrder', backref='part', lazy='dynamic')
    notifications = db.relationship('NotificationLog', backref='part', lazy='dynamic')
    documents = db.relationship('Document', backref='part', lazy='dynamic',
                                primaryjoin='and_(Document.part_id==Part.id, Document.assembly_id==None)',
                                cascade='all, delete-orphan')

class Stage(db.Model):
    __tablename__ = 'stages'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='not_started')
    sort_order = db.Column(db.Integer, default=0)

    estimated_material_cost = db.Column(db.Float, default=0.0)
    actual_material_cost = db.Column(db.Float, default=0.0)
    estimated_labor_cost = db.Column(db.Float, default=0.0)
    actual_labor_cost = db.Column(db.Float, default=0.0)
    estimated_overhead = db.Column(db.Float, default=0.0)
    actual_overhead = db.Column(db.Float, default=0.0)
    estimated_hours = db.Column(db.Float, default=0.0)
    actual_hours = db.Column(db.Float, default=0.0)

    @property
    def estimated_total(self):
        return self.estimated_material_cost + self.estimated_labor_cost + self.estimated_overhead

    @property
    def actual_total(self):
        return self.actual_material_cost + self.actual_labor_cost + self.actual_overhead

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)
    assembly_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    label = db.Column(db.String(100))

class ProductionSchedule(db.Model):
    __tablename__ = 'production_schedules'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='planned')
    priority = db.Column(db.String(20), default='normal')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    work_orders = db.relationship('WorkOrder', backref='schedule', lazy='dynamic', cascade='all, delete-orphan')

class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('production_schedules.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    due_date = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)
    assembly_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=True)
    filename = db.Column(db.String(200), nullable=False)
    original_name = db.Column(db.String(200))
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer, default=0)
    url = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.String(500))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=''):
        s = cls.query.filter_by(key=key).first()
        return s.value if s else default

    @classmethod
    def set(cls, key, value):
        s = cls.query.filter_by(key=key).first()
        if s:
            s.value = value
        else:
            s = cls(key=key, value=value)
            db.session.add(s)
        db.session.commit()

class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    notification_type = db.Column(db.String(20), default='email')
    sent_to = db.Column(db.String(200))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))
    message = db.Column(db.Text)

# ───── Manufacturers ─────

part_manufacturers = db.Table('part_manufacturers',
    db.Column('part_id', db.Integer, db.ForeignKey('parts.id'), primary_key=True),
    db.Column('manufacturer_id', db.Integer, db.ForeignKey('manufacturers.id'), primary_key=True)
)

class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    emails = db.relationship('ManufacturerEmail', backref='manufacturer', lazy='dynamic', cascade='all, delete-orphan')
    socials = db.relationship('ManufacturerSocial', backref='manufacturer', lazy='dynamic', cascade='all, delete-orphan')
    phones = db.relationship('ManufacturerPhone', backref='manufacturer', lazy='dynamic', cascade='all, delete-orphan')

    parts = db.relationship('Part', secondary=part_manufacturers, backref=db.backref('manufacturers', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'emails': [e.to_dict() for e in self.emails.all()],
            'socials': [s.to_dict() for s in self.socials.all()],
            'phones': [p.to_dict() for p in self.phones.all()]
        }

class ManufacturerEmail(db.Model):
    __tablename__ = 'manufacturer_emails'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'email': self.email}

class ManufacturerPhone(db.Model):
    __tablename__ = 'manufacturer_phones'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'), nullable=False)
    phone = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'phone': self.phone}

class ManufacturerSocial(db.Model):
    __tablename__ = 'manufacturer_socials'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'), nullable=False)
    platform = db.Column(db.String(100), nullable=False)
    handle = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'platform': self.platform, 'handle': self.handle}

# ───── Stage Details ─────

class StageDetail(db.Model):
    __tablename__ = 'stage_details'
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)
    step_number = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stage = db.relationship('Stage', backref=db.backref('details', lazy='dynamic', cascade='all, delete-orphan', order_by='StageDetail.step_number'))

    def to_dict(self):
        return {
            'id': self.id,
            'stage_id': self.stage_id,
            'step_number': self.step_number,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
