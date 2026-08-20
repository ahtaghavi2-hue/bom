from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum

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
    change_requests = db.relationship('ChangeRequest', backref='requester', lazy='dynamic',
                                       foreign_keys='ChangeRequest.requester_id')
    change_votes = db.relationship('ChangeVote', backref='voter', lazy='dynamic')

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

    # ── Phase 1: PERT / Uncertainty fields (all nullable → backward-compatible) ──
    time_optimistic = db.Column(db.Float, nullable=True)      # best-case duration
    time_most_likely = db.Column(db.Float, nullable=True)     # most-likely duration
    time_pessimistic = db.Column(db.Float, nullable=True)     # worst-case duration

    # ── Phase 1: Cost breakdown (new fields, defaults keep existing rows safe) ──
    cost_material = db.Column(db.Float, nullable=True)        # direct material cost
    cost_labor = db.Column(db.Float, nullable=True)           # direct labor cost
    cost_overhead = db.Column(db.Float, nullable=True)        # overhead allocation

    # ── Phase 1: Resource & storage ──
    required_resource_type = db.Column(db.String(50), nullable=True)   # e.g. "CNC", "Assembly", "QC"
    storage_cost_per_day = db.Column(db.Float, nullable=True)          # daily warehousing cost

    # ── Relationships ──
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
    versions = db.relationship('PartVersion', backref='part', lazy='dynamic',
                                cascade='all, delete-orphan',
                                order_by='PartVersion.version_number.desc()')
    change_requests = db.relationship('ChangeRequest', backref='part', lazy='dynamic',
                                       cascade='all, delete-orphan')
    cost_history = db.relationship('CostHistory', backref='part', lazy='dynamic',
                                    cascade='all, delete-orphan',
                                    order_by='CostHistory.recorded_at')
    vector_embedding = db.Column(db.Text)

    @property
    def pert_expected_time(self):
        """PERT expected time: (O + 4M + P) / 6"""
        if self.time_optimistic is not None and self.time_most_likely is not None and self.time_pessimistic is not None:
            return (self.time_optimistic + 4 * self.time_most_likely + self.time_pessimistic) / 6.0
        return None

    @property
    def pert_std_dev(self):
        """PERT standard deviation: (P - O) / 6"""
        if self.time_optimistic is not None and self.time_pessimistic is not None:
            return (self.time_pessimistic - self.time_optimistic) / 6.0
        return None

    @property
    def total_direct_cost(self):
        """Sum of material + labor + overhead."""
        m = self.cost_material or 0.0
        l = self.cost_labor or 0.0
        o = self.cost_overhead or 0.0
        return m + l + o

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
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'), nullable=True)

    # ── Phase 1+2: Stage as the atomic scheduling unit ──
    time_optimistic = db.Column(db.Float, nullable=True)      # best-case duration (hours)
    time_most_likely = db.Column(db.Float, nullable=True)     # most-likely duration (hours)
    time_pessimistic = db.Column(db.Float, nullable=True)     # worst-case duration (hours)
    required_resource_type = db.Column(db.String(50), nullable=True)   # e.g. "CNC", "Assembly", "QC"
    storage_cost_per_day = db.Column(db.Float, nullable=True)          # daily warehousing cost for this stage

    manufacturer = db.relationship('Manufacturer', lazy='select')

    @property
    def manufacturer_name(self):
        return self.manufacturer.name if self.manufacturer else None

    @property
    def estimated_total(self):
        return self.estimated_material_cost + self.estimated_labor_cost + self.estimated_overhead

    @property
    def actual_total(self):
        return self.actual_material_cost + self.actual_labor_cost + self.actual_overhead

    @property
    def pert_expected_time(self):
        """PERT expected time: (O + 4M + P) / 6 — None if not estimated."""
        if self.time_optimistic is not None and self.time_most_likely is not None and self.time_pessimistic is not None:
            return (self.time_optimistic + 4 * self.time_most_likely + self.time_pessimistic) / 6.0
        return None

    @property
    def pert_std_dev(self):
        """PERT standard deviation: (P - O) / 6 — None if not estimated."""
        if self.time_optimistic is not None and self.time_pessimistic is not None:
            return (self.time_pessimistic - self.time_optimistic) / 6.0
        return None

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
    quality_score = db.Column(db.Float, default=70.0)
    reliability_score = db.Column(db.Float, default=70.0)
    delivery_days = db.Column(db.Integer, default=7)
    rating_count = db.Column(db.Integer, default=0)
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
            'quality_score': self.quality_score,
            'reliability_score': self.reliability_score,
            'delivery_days': self.delivery_days,
            'rating_count': self.rating_count,
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

# ───── PLM: Part Versioning ─────

class PartVersion(db.Model):
    __tablename__ = 'part_versions'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    change_summary = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('part_id', 'version_number', name='uq_part_version'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'version_number': self.version_number,
            'change_summary': self.change_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
        }


# ───── PLM: Change Request ─────

class ChangeRequestStatus(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'


class ChangeRequest(db.Model):
    __tablename__ = 'change_requests'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    justification = db.Column(db.Text)
    status = db.Column(db.Enum(ChangeRequestStatus), default=ChangeRequestStatus.pending, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    votes = db.relationship('ChangeVote', backref='change_request', lazy='dynamic',
                            cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'requester_id': self.requester_id,
            'requester_name': self.requester.username if self.requester else None,
            'description': self.description,
            'justification': self.justification,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'votes': [v.to_dict() for v in self.votes.all()],
        }


# ───── PLM: Change Vote ─────

class VoteType(enum.Enum):
    approve = 'approve'
    reject = 'reject'


class ChangeVote(db.Model):
    __tablename__ = 'change_votes'
    id = db.Column(db.Integer, primary_key=True)
    change_request_id = db.Column(db.Integer, db.ForeignKey('change_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.Enum(VoteType), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('change_request_id', 'user_id', name='uq_change_vote'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'change_request_id': self.change_request_id,
            'user_id': self.user_id,
            'voter_name': self.voter.username if self.voter else None,
            'vote_type': self.vote_type.value if self.vote_type else None,
            'voted_at': self.voted_at.isoformat() if self.voted_at else None,
        }


# ───── AI & Data Analytics ─────

class CostHistory(db.Model):
    __tablename__ = 'cost_history'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False, index=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_total = db.Column(db.Float, default=0.0)
    actual_total = db.Column(db.Float, default=0.0)
    material_cost = db.Column(db.Float, default=0.0)
    labor_cost = db.Column(db.Float, default=0.0)
    overhead = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'estimated_total': self.estimated_total,
            'actual_total': self.actual_total,
            'material_cost': self.material_cost,
            'labor_cost': self.labor_cost,
            'overhead': self.overhead,
            'quantity': self.quantity,
        }


class PartSimilarity(db.Model):
    __tablename__ = 'part_similarity'
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False, index=True)
    similar_part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)

    __table_args__ = (
        db.UniqueConstraint('part_id', 'similar_part_id', name='uq_part_similarity'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'similar_part_id': self.similar_part_id,
            'score': round(self.score, 4),
        }


class Artisan(db.Model):
    __tablename__ = 'artisans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    specialty = db.Column(db.String(200))
    labor_rate = db.Column(db.Float, default=0.0)
    quality_score = db.Column(db.Float, default=70.0)
    accuracy_score = db.Column(db.Float, default=70.0)
    rating_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'specialty': self.specialty,
            'labor_rate': self.labor_rate,
            'quality_score': self.quality_score,
            'accuracy_score': self.accuracy_score,
            'rating_count': self.rating_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class VendorType(enum.Enum):
    supplier = 'supplier'
    artisan = 'artisan'


class VendorRating(db.Model):
    __tablename__ = 'vendor_ratings'
    id = db.Column(db.Integer, primary_key=True)
    vendor_type = db.Column(db.Enum(VendorType), nullable=False)
    vendor_id = db.Column(db.Integer, nullable=False)
    quality_score = db.Column(db.Float, default=0.0)
    accuracy_score = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    rated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vendor_type': self.vendor_type.value if self.vendor_type else None,
            'vendor_id': self.vendor_id,
            'quality_score': self.quality_score,
            'accuracy_score': self.accuracy_score,
            'notes': self.notes,
            'rated_by': self.rated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ════════════════════════════════════════════════════════════════════════════
# Phase 1 – Scheduling & Resource Models
# ════════════════════════════════════════════════════════════════════════════


class Resource(db.Model):
    """Workshop resource: CNC machines, assembly stations, QC stations, etc.

    Each resource has a capacity (number of identical units) and an optional
    per-shift override.  Parts reference a resource by `required_resource_type`.
    """
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False, index=True)  # CNC, Assembly, QC …
    capacity = db.Column(db.Integer, default=1)              # units available simultaneously
    shift_hours = db.Column(db.Float, default=8.0)           # hours per shift
    cost_per_hour = db.Column(db.Float, default=0.0)         # operating cost / hour
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ──
    assignments = db.relationship('ResourceAssignment', backref='resource', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'resource_type': self.resource_type,
            'capacity': self.capacity,
            'shift_hours': self.shift_hours,
            'cost_per_hour': self.cost_per_hour,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ResourceAssignment(db.Model):
    """Tracks which Part (or Stage) is assigned to which Resource in a schedule."""
    __tablename__ = 'resource_assignments'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('production_schedules.id'), nullable=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)
    start_time = db.Column(db.Float, nullable=True)      # hours from project start
    duration = db.Column(db.Float, nullable=True)         # hours required
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'schedule_id': self.schedule_id,
            'part_id': self.part_id,
            'start_time': self.start_time,
            'duration': self.duration,
            'quantity': self.quantity,
        }


class ProjectSettings(db.Model):
    """Per-product project configuration: deadline, daily penalty, budget."""
    __tablename__ = 'project_settings'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), unique=True, nullable=False)
    target_delivery_date = db.Column(db.DateTime, nullable=True)    # final deadline
    daily_penalty = db.Column(db.Float, default=0.0)                 # penalty per day of delay
    total_budget = db.Column(db.Float, default=0.0)                  # overall budget ceiling
    risk_reserve_pct = db.Column(db.Float, default=10.0)             # % buffer on budget
    monte_carlo_runs = db.Column(db.Integer, default=1000)           # iterations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('project_settings', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'target_delivery_date': self.target_delivery_date.isoformat() if self.target_delivery_date else None,
            'daily_penalty': self.daily_penalty,
            'total_budget': self.total_budget,
            'risk_reserve_pct': self.risk_reserve_pct,
            'monte_carlo_runs': self.monte_carlo_runs,
        }


class Scenario(db.Model):
    """A named what-if scenario: "optimistic", "resource shortage", etc."""
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('scenarios', lazy='dynamic'))
    overrides = db.relationship('ScenarioOverride', backref='scenario', lazy='dynamic',
                                cascade='all, delete-orphan')
    results = db.relationship('ScheduleResult', backref='scenario', lazy='dynamic',
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'overrides': [o.to_dict() for o in self.overrides.all()],
        }


class ScenarioOverride(db.Model):
    """Per-part parameter overrides inside a scenario."""
    __tablename__ = 'scenario_overrides'
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)   # e.g. time_optimistic, cost_material
    field_value = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('scenario_id', 'part_id', 'field_name', name='uq_scenario_override'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'part_id': self.part_id,
            'field_name': self.field_name,
            'field_value': self.field_value,
        }


class ScheduleResult(db.Model):
    """Cached output of a simulation / optimization run."""
    __tablename__ = 'schedule_results'
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('production_schedules.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    result_type = db.Column(db.String(30), nullable=False)  # monte_carlo | cpm | resource_leveling
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)
    # JSON-serialised payload – flexible schema for varying output shapes
    result_data = db.Column(db.JSON, nullable=True)
    # High-level summary columns for quick dashboard queries
    estimated_duration = db.Column(db.Float, nullable=True)       # total project duration (hours)
    estimated_cost = db.Column(db.Float, nullable=True)           # total cost estimate
    probability_on_time = db.Column(db.Float, nullable=True)      # 0-1 fraction from Monte Carlo
    critical_path_ids = db.Column(db.Text, nullable=True)        # comma-separated part IDs

    product = db.relationship('Product', backref=db.backref('schedule_results', lazy='dynamic'))
    schedule = db.relationship('ProductionSchedule',
                               backref=db.backref('schedule_results', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'schedule_id': self.schedule_id,
            'product_id': self.product_id,
            'result_type': self.result_type,
            'computed_at': self.computed_at.isoformat() if self.computed_at else None,
            'estimated_duration': self.estimated_duration,
            'estimated_cost': self.estimated_cost,
            'probability_on_time': self.probability_on_time,
            'critical_path_ids': self.critical_path_ids,
        }


class ProjectCostSnapshot(db.Model):
    """Point-in-time cost snapshot for S-Curve visualisation."""
    __tablename__ = 'project_cost_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    day_number = db.Column(db.Integer, nullable=False)         # day from project start
    cumulative_material = db.Column(db.Float, default=0.0)
    cumulative_labor = db.Column(db.Float, default=0.0)
    cumulative_overhead = db.Column(db.Float, default=0.0)
    cumulative_total = db.Column(db.Float, default=0.0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product',
                              backref=db.backref('cost_snapshots', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'day_number': self.day_number,
            'cumulative_material': self.cumulative_material,
            'cumulative_labor': self.cumulative_labor,
            'cumulative_overhead': self.cumulative_overhead,
            'cumulative_total': self.cumulative_total,
        }
