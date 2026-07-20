from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Product, Assembly, Part, Stage, Image, ProductionSchedule, WorkOrder, NotificationLog
from datetime import datetime
import os
import uuid
from pathlib import Path

api_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ('admin', 'engineer'):
            return jsonify({'error': 'دسترسی غیرمجاز'}), 403
        return f(*args, **kwargs)
    return decorated

# ───── Products ─────

@api_bp.route('/products', methods=['GET'])
@login_required
def list_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in products]
    })

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({'success': True, 'data': product.to_dict(full=True)})

@api_bp.route('/products', methods=['POST'])
@admin_required
def create_product():
    data = request.get_json()
    product = Product(
        name=data.get('name', 'محصول جدید'),
        code=data.get('code', ''),
        description=data.get('description', ''),
        specs=data.get('specs', ''),
        notes=data.get('notes', ''),
        order_count=data.get('order_count', 0),
        status=data.get('status', 'active'),
        created_by=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'success': True, 'data': product.to_dict()}), 201

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    for key in ('name', 'code', 'description', 'specs', 'notes', 'order_count', 'status'):
        if key in data:
            setattr(product, key, data[key])
    db.session.commit()
    return jsonify({'success': True, 'data': product.to_dict()})

@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'محصول حذف شد'})

# ───── Assemblies ─────

@api_bp.route('/products/<int:product_id>/assemblies', methods=['GET'])
@login_required
def list_assemblies(product_id):
    assemblies = Assembly.query.filter_by(product_id=product_id, parent_id=None).order_by(Assembly.sort_order).all()
    def build_tree(a):
        children = Assembly.query.filter_by(parent_id=a.id).order_by(Assembly.sort_order).all()
        return {
            'id': a.id, 'name': a.name, 'description': a.description,
            'parts': [p.to_dict() for p in a.parts.order_by(Part.sort_order).all()],
            'children': [build_tree(c) for c in children]
        }
    return jsonify({'success': True, 'data': [build_tree(a) for a in assemblies]})

@api_bp.route('/assemblies', methods=['POST'])
@admin_required
def create_assembly():
    data = request.get_json()
    assembly = Assembly(
        product_id=data['product_id'],
        parent_id=data.get('parent_id'),
        name=data['name'],
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(assembly)
    db.session.commit()
    return jsonify({'success': True, 'data': assembly.to_dict()}), 201

# ───── Parts ─────

@api_bp.route('/assemblies/<int:assembly_id>/parts', methods=['GET'])
@login_required
def list_parts(assembly_id):
    parts = Part.query.filter_by(assembly_id=assembly_id).order_by(Part.sort_order).all()
    return jsonify({'success': True, 'data': [p.to_dict(full=True) for p in parts]})

@api_bp.route('/parts', methods=['POST'])
@admin_required
def create_part():
    data = request.get_json()
    part = Part(
        assembly_id=data['assembly_id'],
        name=data.get('name', 'قطعه جدید'),
        part_code=data.get('part_code', ''),
        specs=data.get('specs', ''),
        part_type=data.get('part_type', 'make'),
        quantity=data.get('quantity', 0),
        required_quantity=data.get('required_quantity', 1),
        supplier=data.get('supplier', ''),
        supplier_email=data.get('supplier_email', ''),
        notes=data.get('notes', ''),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(part)
    db.session.commit()
    return jsonify({'success': True, 'data': part.to_dict()}), 201

@api_bp.route('/parts/<int:part_id>', methods=['PUT'])
@admin_required
def update_part(part_id):
    part = Part.query.get_or_404(part_id)
    data = request.get_json()
    for key in ('name', 'part_code', 'specs', 'part_type', 'quantity',
                'required_quantity', 'supplier', 'supplier_email', 'notes', 'status'):
        if key in data:
            setattr(part, key, data[key])
    db.session.commit()
    return jsonify({'success': True, 'data': part.to_dict()})

@api_bp.route('/parts/<int:part_id>', methods=['DELETE'])
@admin_required
def delete_part(part_id):
    part = Part.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    return jsonify({'success': True, 'message': 'قطعه حذف شد'})

# ───── Stages / Cost Tracking ─────

@api_bp.route('/parts/<int:part_id>/stages', methods=['GET'])
@login_required
def list_stages(part_id):
    stages = Stage.query.filter_by(part_id=part_id).order_by(Stage.sort_order).all()
    return jsonify({'success': True, 'data': [s.to_dict() for s in stages]})

@api_bp.route('/stages', methods=['POST'])
@admin_required
def create_stage():
    data = request.get_json()
    stage = Stage(
        part_id=data['part_id'],
        name=data['name'],
        sort_order=data.get('sort_order', 0),
        estimated_material_cost=data.get('estimated_material_cost', 0),
        estimated_labor_cost=data.get('estimated_labor_cost', 0),
        estimated_overhead=data.get('estimated_overhead', 0),
        estimated_hours=data.get('estimated_hours', 0)
    )
    db.session.add(stage)
    db.session.commit()
    return jsonify({'success': True, 'data': stage.to_dict()}), 201

@api_bp.route('/stages/<int:stage_id>', methods=['PUT'])
@admin_required
def update_stage(stage_id):
    stage = Stage.query.get_or_404(stage_id)
    data = request.get_json()
    for key in ('name', 'status', 'sort_order',
                'estimated_material_cost', 'actual_material_cost',
                'estimated_labor_cost', 'actual_labor_cost',
                'estimated_overhead', 'actual_overhead',
                'estimated_hours', 'actual_hours'):
        if key in data:
            setattr(stage, key, data[key])
    db.session.commit()
    return jsonify({'success': True, 'data': stage.to_dict()})

@api_bp.route('/stages/<int:stage_id>', methods=['DELETE'])
@admin_required
def delete_stage(stage_id):
    stage = Stage.query.get_or_404(stage_id)
    db.session.delete(stage)
    db.session.commit()
    return jsonify({'success': True, 'message': 'مرحله حذف شد'})

# ───── Production Scheduling ─────

@api_bp.route('/schedules', methods=['GET'])
@login_required
def list_schedules():
    schedules = ProductionSchedule.query.order_by(ProductionSchedule.created_at.desc()).all()
    return jsonify({'success': True, 'data': [s.to_dict() for s in schedules]})

@api_bp.route('/schedules', methods=['POST'])
@admin_required
def create_schedule():
    data = request.get_json()
    schedule = ProductionSchedule(
        product_id=data['product_id'],
        quantity=data.get('quantity', 1),
        start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
        end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
        priority=data.get('priority', 'normal'),
        notes=data.get('notes', ''),
        created_by=current_user.id
    )
    db.session.add(schedule)
    db.session.commit()
    _auto_generate_work_orders(schedule)
    return jsonify({'success': True, 'data': schedule.to_dict()}), 201

@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@admin_required
def update_schedule(schedule_id):
    schedule = ProductionSchedule.query.get_or_404(schedule_id)
    data = request.get_json()
    for key in ('quantity', 'status', 'priority', 'notes'):
        if key in data:
            setattr(schedule, key, data[key])
    if 'start_date' in data:
        schedule.start_date = datetime.fromisoformat(data['start_date'])
    if 'end_date' in data:
        schedule.end_date = datetime.fromisoformat(data['end_date'])
    db.session.commit()
    return jsonify({'success': True, 'data': schedule.to_dict()})

# ───── Work Orders ─────

@api_bp.route('/work-orders', methods=['GET'])
@login_required
def list_work_orders():
    status = request.args.get('status')
    q = WorkOrder.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(WorkOrder.created_at.desc()).all()
    return jsonify({'success': True, 'data': [o.to_dict() for o in orders]})

@api_bp.route('/work-orders/<int:order_id>/status', methods=['PATCH'])
@admin_required
def update_work_order_status(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    if new_status in ('pending', 'in_progress', 'completed', 'cancelled'):
        order.status = new_status
        if new_status == 'in_progress':
            order.started_at = datetime.utcnow()
        elif new_status == 'completed':
            order.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'data': order.to_dict()})

# ───── Dashboard Stats ─────

@api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    total_products = Product.query.count()
    total_parts = Part.query.count()
    active_schedules = ProductionSchedule.query.filter(
        ProductionSchedule.status.in_(['planned', 'in_progress'])
    ).count()
    low_stock_parts = 0
    for p in Part.query.all():
        required = p.required_quantity or 1
        if (p.quantity or 0) < required:
            low_stock_parts += 1
    stages_completed = Stage.query.filter_by(status='completed').count()
    stages_total = Stage.query.count()
    total_estimated_cost = db.session.query(db.func.sum(Stage.estimated_material_cost + Stage.estimated_labor_cost + Stage.estimated_overhead)).scalar() or 0
    total_actual_cost = db.session.query(db.func.sum(Stage.actual_material_cost + Stage.actual_labor_cost + Stage.actual_overhead)).scalar() or 0
    return jsonify({
        'success': True,
        'data': {
            'total_products': total_products,
            'total_parts': total_parts,
            'active_schedules': active_schedules,
            'low_stock_parts': low_stock_parts,
            'stages_completed': stages_completed,
            'stages_total': stages_total,
            'progress_percent': round((stages_completed / stages_total * 100) if stages_total else 0),
            'total_estimated_cost': total_estimated_cost,
            'total_actual_cost': total_actual_cost,
            'recent_schedules': [s.to_dict() for s in ProductionSchedule.query.order_by(ProductionSchedule.created_at.desc()).limit(5).all()],
            'recent_products': [p.to_dict() for p in Product.query.order_by(Product.created_at.desc()).limit(5).all()]
        }
    })

# ───── Helpers ─────

def _auto_generate_work_orders(schedule):
    assemblies = Assembly.query.filter_by(product_id=schedule.product_id, parent_id=None).all()
    def collect_parts(assembly):
        parts = []
        for p in assembly.parts.all():
            parts.append(p)
        for sub in assembly.sub_assemblies:
            parts.extend(collect_parts(sub))
        return parts
    for assembly in assemblies:
        for part in collect_parts(assembly):
            wo = WorkOrder(
                schedule_id=schedule.id,
                part_id=part.id,
                quantity=part.required_quantity * schedule.quantity,
                status='pending',
                due_date=schedule.end_date
            )
            db.session.add(wo)
    db.session.commit()

# ───── Model serialization helpers ─────

def _add_to_dict_methods():
    for cls, fields, full_fields in [
        (Product,
         ['id', 'name', 'code', 'status', 'order_count', 'created_at'],
         ['id', 'name', 'code', 'description', 'specs', 'notes', 'order_count', 'status',
          'created_by', 'created_at', 'updated_at']),
        (Assembly,
         ['id', 'product_id', 'parent_id', 'name', 'sort_order'],
         ['id', 'product_id', 'parent_id', 'name', 'description', 'sort_order', 'created_at']),
        (Part,
         ['id', 'assembly_id', 'name', 'part_code', 'part_type', 'quantity', 'required_quantity', 'status'],
         ['id', 'assembly_id', 'name', 'part_code', 'specs', 'part_type', 'quantity',
          'required_quantity', 'supplier', 'supplier_email', 'notes', 'status', 'sort_order']),
        (Stage,
         ['id', 'part_id', 'name', 'status', 'sort_order', 'estimated_total', 'actual_total'],
         ['id', 'part_id', 'name', 'status', 'sort_order',
          'estimated_material_cost', 'actual_material_cost',
          'estimated_labor_cost', 'actual_labor_cost',
          'estimated_overhead', 'actual_overhead',
          'estimated_hours', 'actual_hours',
          'estimated_total', 'actual_total']),
        (ProductionSchedule,
         ['id', 'product_id', 'quantity', 'status', 'priority', 'start_date', 'end_date', 'created_at'],
         ['id', 'product_id', 'quantity', 'status', 'priority',
          'start_date', 'end_date', 'created_by', 'created_at', 'notes']),
        (WorkOrder,
         ['id', 'schedule_id', 'part_id', 'quantity', 'status', 'due_date', 'created_at'],
         ['id', 'schedule_id', 'part_id', 'quantity', 'status',
          'assigned_to', 'due_date', 'started_at', 'completed_at', 'notes', 'created_at']),
    ]:
        def make_to_dict(fs):
            def to_dict(self, full=False):
                result = {}
                for f in (fs if full else fields):
                    val = getattr(self, f)
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    result[f] = val
                return result
            return to_dict
        cls.to_dict = make_to_dict(full_fields)

_add_to_dict_methods()
