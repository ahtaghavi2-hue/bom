from flask import Blueprint, request, jsonify, url_for, current_app
from bom_calculation import validate_quantities
from flask_login import login_required, current_user
from extensions import db
from models import Product, Assembly, Part, Stage, Image, ProductionSchedule, WorkOrder, NotificationLog
from models import Manufacturer, ManufacturerEmail, ManufacturerPhone, ManufacturerSocial, StageDetail, part_manufacturers
from models import Category, Tag, StageManufacturer
from manufacturer_service import (json_object, validate_ids, validate_manufacturer, apply_manufacturer,
    replace_stage_manufacturers, stage_manufacturers, manufacturer_usage, filter_manufacturers,
    manufacturer_workbook)
from datetime import datetime
import os
import uuid
from pathlib import Path

api_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')


def _inventory_data(fields):
    from werkzeug.exceptions import BadRequest
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest('JSON object required')
    try:
        data.update(validate_quantities(data, fields))
    except ValueError as error:
        raise BadRequest(str(error)) from error
    return data


@api_bp.errorhandler(400)
def invalid_inventory(error):
    return jsonify({'error': error.description}), 400


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
    data = _inventory_data(('quantity', 'order_count'))
    product = Product(
        name=data.get('name', 'محصول جدید'),
        code=data.get('code', ''),
        description=data.get('description', ''),
        specs=data.get('specs', ''),
        notes=data.get('notes', ''),
        order_count=data.get('order_count', 0),
        quantity=data.get('quantity', 0),
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
    data = _inventory_data(('quantity', 'order_count'))
    for key in ('name', 'code', 'description', 'specs', 'notes', 'order_count', 'quantity', 'status'):
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
            'quantity': a.quantity, 'required_quantity': a.required_quantity,
            'parts': [p.to_dict() for p in a.parts.order_by(Part.sort_order).all()],
            'children': [build_tree(c) for c in children]
        }
    return jsonify({'success': True, 'data': [build_tree(a) for a in assemblies]})

@api_bp.route('/assemblies', methods=['POST'])
@admin_required
def create_assembly():
    data = _inventory_data(('quantity', 'required_quantity'))
    product = db.session.get(Product, data.get('product_id'))
    parent = db.session.get(Assembly, data['parent_id']) if data.get('parent_id') is not None else None
    if not product or (data.get('parent_id') is not None and (not parent or parent.product_id != product.id)):
        return jsonify({'error': 'Invalid product or assembly parent'}), 400
    assembly = Assembly(
        product_id=data['product_id'],
        parent_id=data.get('parent_id'),
        name=data['name'],
        description=data.get('description', ''),
        quantity=data.get('quantity', 0),
        required_quantity=data.get('required_quantity', 1),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(assembly)
    db.session.commit()
    return jsonify({'success': True, 'data': assembly.to_dict()}), 201

@api_bp.route('/assemblies/<int:assembly_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_assembly(assembly_id):
    assembly = Assembly.query.get_or_404(assembly_id)
    data = _inventory_data(('quantity', 'required_quantity'))
    for key in ('name', 'description', 'sort_order', 'quantity', 'required_quantity'):
        if key in data:
            setattr(assembly, key, data[key])
    db.session.commit()
    return jsonify({'success': True, 'data': assembly.to_dict()})


# ───── Parts ─────

@api_bp.route('/assemblies/<int:assembly_id>/parts', methods=['GET'])
@login_required
def list_parts(assembly_id):
    parts = Part.query.filter_by(assembly_id=assembly_id).order_by(Part.sort_order).all()
    return jsonify({'success': True, 'data': [p.to_dict(full=True) for p in parts]})

@api_bp.route('/parts', methods=['POST'])
@admin_required
def create_part():
    data = _inventory_data(('quantity', 'required_quantity'))
    if not db.session.get(Assembly, data.get('assembly_id')):
        return jsonify({'error': 'Invalid assembly parent'}), 400
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
    data = _inventory_data(('quantity', 'required_quantity'))
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
    data = json_object(request)
    try:
        ids = validate_ids(data['manufacturer_ids'], Manufacturer, 'manufacturer_ids') if 'manufacturer_ids' in data else None
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    if type(data.get('part_id')) is not int or not db.session.get(Part, data['part_id']):
        return jsonify({'error': 'Invalid part_id'}), 400
    if not isinstance(data.get('name'), str) or not data['name'].strip():
        return jsonify({'error': 'Invalid stage name'}), 400
    stage = Stage(
        part_id=data['part_id'],
        name=data['name'],
        sort_order=data.get('sort_order', 0),
        estimated_material_cost=data.get('estimated_material_cost', 0),
        estimated_labor_cost=data.get('estimated_labor_cost', 0),
        estimated_overhead=data.get('estimated_overhead', 0),
        estimated_hours=data.get('estimated_hours', 0)
    )
    if ids is not None:
        replace_stage_manufacturers(stage, ids)
    db.session.add(stage)
    db.session.commit()
    return jsonify({'success': True, 'data': stage.to_dict()}), 201

@api_bp.route('/stages/<int:stage_id>', methods=['PUT'])
@admin_required
def update_stage(stage_id):
    stage = Stage.query.get_or_404(stage_id)
    data = json_object(request)
    try:
        ids = validate_ids(data['manufacturer_ids'], Manufacturer, 'manufacturer_ids') if 'manufacturer_ids' in data else None
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    if ids is not None:
        replace_stage_manufacturers(stage, ids)
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
    nodes = current_app.extensions['bom_load_data']()['nodes']
    low_stock_parts = sum(1 for node in nodes.values()
                          if node['type'] == 'part' and node['shortage'] > 0)
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

# ───── Manufacturers ─────

@api_bp.route('/manufacturers', methods=['GET'])
@login_required
def list_manufacturers():
    try:
        manufacturers = filter_manufacturers(request.args).all()
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    return jsonify({'success': True, 'data': [m.to_dict() for m in manufacturers]})

@api_bp.route('/manufacturers', methods=['POST'])
@admin_required
def create_manufacturer():
    try:
        values = validate_manufacturer(json_object(request), creating=True)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    mfr = Manufacturer(name=values['name'])
    apply_manufacturer(mfr, values)
    db.session.add(mfr)
    db.session.commit()
    return jsonify({'success': True, 'data': mfr.to_dict()}), 201

@api_bp.route('/manufacturers/<int:mfr_id>', methods=['PUT'])
@admin_required
def update_manufacturer(mfr_id):
    mfr = Manufacturer.query.get_or_404(mfr_id)
    try:
        values = validate_manufacturer(json_object(request))
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    apply_manufacturer(mfr, values)
    db.session.commit()
    return jsonify({'success': True, 'data': mfr.to_dict()})

@api_bp.route('/manufacturers/<int:mfr_id>', methods=['DELETE'])
@admin_required
def delete_manufacturer(mfr_id):
    mfr = Manufacturer.query.get_or_404(mfr_id)
    if mfr.parts or mfr.stage_links:
        return jsonify({'error': 'Manufacturer is referenced; deactivate using is_active=false instead'}), 409
    db.session.delete(mfr)
    db.session.commit()
    return jsonify({'success': True, 'message': 'سازنده حذف شد'})


@api_bp.route('/manufacturers/<int:mfr_id>', methods=['GET'])
@login_required
def get_manufacturer(mfr_id):
    manufacturer = Manufacturer.query.get_or_404(mfr_id)
    return jsonify({'success': True, 'data': dict(manufacturer.to_dict(), usage_stages=manufacturer_usage(manufacturer))})


@api_bp.route('/manufacturers/export/excel')
@api_bp.route('/manufacturers/<int:mfr_id>/export/excel')
@login_required
def export_manufacturers(mfr_id=None):
    from flask import send_file
    try:
        manufacturers = [Manufacturer.query.get_or_404(mfr_id)] if mfr_id is not None else filter_manufacturers(request.args).all()
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    return send_file(manufacturer_workbook(manufacturers), as_attachment=True,
        download_name='manufacturers.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@api_bp.route('/stages/<int:stage_id>/manufacturers', methods=['GET', 'PUT'])
@login_required
def stage_manufacturer_list(stage_id):
    if request.method == 'PUT' and current_user.role not in ('admin', 'engineer'):
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403
    stage = Stage.query.get_or_404(stage_id)
    if request.method == 'PUT':
        try:
            ids = validate_ids(json_object(request).get('manufacturer_ids'), Manufacturer, 'manufacturer_ids')
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        replace_stage_manufacturers(stage, ids)
        db.session.commit()
    return jsonify({'success': True, 'data': stage_manufacturers(stage)})


def _definition_payload(model, item=None):
    data = json_object(request)
    name = data.get('name', item.name if item else None)
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
        raise ValueError('name must be a nonempty string (maximum 200 characters)')
    values = {'name': name.strip()}
    duplicate = model.query.filter_by(name=values['name'])
    if model is Tag:
        category_id = data.get('category_id', item.category_id if item else None)
        if type(category_id) is not int or not db.session.get(Category, category_id):
            raise ValueError('Invalid category_id')
        values['category_id'] = category_id
        duplicate = duplicate.filter_by(category_id=category_id)
    if item:
        duplicate = duplicate.filter(model.id != item.id)
    if duplicate.first():
        raise ValueError('Definition already exists in this category')
    return values


def _definitions(model, item_id=None):
    if request.method != 'GET' and current_user.role not in ('admin', 'engineer'):
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403
    item = model.query.get_or_404(item_id) if item_id is not None else None
    if request.method == 'GET':
        query = model.query.order_by(model.id)
        if model is Tag and request.args.get('category_id') is not None:
            raw = request.args['category_id']
            if not raw.isdecimal() or int(raw) <= 0:
                return jsonify({'error': 'Invalid category_id'}), 400
            query = query.filter_by(category_id=int(raw))
        return jsonify({'success': True, 'data': [row.to_dict() for row in query.all()]})
    if request.method == 'DELETE':
        if (model is Category and item.tags) or (model is Tag and item.manufacturers):
            return jsonify({'error': 'Definition is in use'}), 409
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    try:
        values = _definition_payload(model, item)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    if item is None:
        item = model(**values)
        db.session.add(item)
    else:
        for key, value in values.items():
            setattr(item, key, value)
    db.session.commit()
    return jsonify({'success': True, 'data': item.to_dict()}), 201 if request.method == 'POST' else 200


@api_bp.route('/manufacturer-categories', methods=['GET', 'POST'])
@api_bp.route('/manufacturer-categories/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def manufacturer_categories(item_id=None):
    return _definitions(Category, item_id)


@api_bp.route('/manufacturer-tags', methods=['GET', 'POST'])
@api_bp.route('/manufacturer-tags/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def manufacturer_tags_api(item_id=None):
    return _definitions(Tag, item_id)

# ───── Part-Manufacturer Association ─────

@api_bp.route('/parts/<int:part_id>/manufacturers', methods=['GET'])
@login_required
def list_part_manufacturers(part_id):
    part = Part.query.get_or_404(part_id)
    return jsonify({'success': True, 'data': [m.to_dict() for m in part.manufacturers.all()]})

@api_bp.route('/parts/<int:part_id>/manufacturers', methods=['POST'])
@admin_required
def add_part_manufacturer(part_id):
    part = Part.query.get_or_404(part_id)
    data = request.get_json()
    mfr_id = data.get('manufacturer_id')
    if not mfr_id:
        return jsonify({'error': 'شناسه سازنده الزامی است'}), 400
    mfr = Manufacturer.query.get(mfr_id)
    if not mfr:
        return jsonify({'error': 'سازنده یافت نشد'}), 404
    if mfr in part.manufacturers.all():
        return jsonify({'success': True, 'message': 'قبلاً اضافه شده'})
    part.manufacturers.append(mfr)
    db.session.commit()
    return jsonify({'success': True, 'data': mfr.to_dict()}), 201

@api_bp.route('/parts/<int:part_id>/manufacturers/<int:mfr_id>', methods=['DELETE'])
@admin_required
def remove_part_manufacturer(part_id, mfr_id):
    part = Part.query.get_or_404(part_id)
    mfr = Manufacturer.query.get_or_404(mfr_id)
    part.manufacturers.remove(mfr)
    db.session.commit()
    return jsonify({'success': True, 'message': 'سازنده حذف شد'})

# ───── Stage Details ─────

@api_bp.route('/stages/<int:stage_id>/details', methods=['GET'])
@login_required
def list_stage_details(stage_id):
    details = StageDetail.query.filter_by(stage_id=stage_id).order_by(StageDetail.step_number).all()
    return jsonify({'success': True, 'data': [d.to_dict() for d in details]})

@api_bp.route('/stage-details', methods=['POST'])
@admin_required
def create_stage_detail():
    data = request.get_json()
    detail = StageDetail(
        stage_id=data['stage_id'],
        step_number=data.get('step_number', 1),
        description=data.get('description', '')
    )
    db.session.add(detail)
    db.session.commit()
    return jsonify({'success': True, 'data': detail.to_dict()}), 201

@api_bp.route('/stage-details/<int:detail_id>', methods=['PUT'])
@admin_required
def update_stage_detail(detail_id):
    detail = StageDetail.query.get_or_404(detail_id)
    data = request.get_json()
    if 'step_number' in data: detail.step_number = data['step_number']
    if 'description' in data: detail.description = data['description']
    db.session.commit()
    return jsonify({'success': True, 'data': detail.to_dict()})

@api_bp.route('/stage-details/<int:detail_id>', methods=['DELETE'])
@admin_required
def delete_stage_detail(detail_id):
    detail = StageDetail.query.get_or_404(detail_id)
    db.session.delete(detail)
    db.session.commit()
    return jsonify({'success': True, 'message': 'جزئیات مرحله حذف شد'})

# ───── Helpers ─────

def _auto_generate_work_orders(schedule):
    assemblies = Assembly.query.filter_by(product_id=schedule.product_id, parent_id=None).all()
    def collect_parts(assembly):
        parts = []
        for p in assembly.parts.all():
            parts.append(p)
        for sub in assembly.children:
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
         ['id', 'name', 'code', 'status', 'order_count', 'quantity', 'created_at'],
         ['id', 'name', 'code', 'description', 'specs', 'notes', 'order_count', 'quantity', 'status',
          'created_by', 'created_at', 'updated_at']),
        (Assembly,
         ['id', 'product_id', 'parent_id', 'name', 'quantity', 'required_quantity', 'sort_order'],
         ['id', 'product_id', 'parent_id', 'name', 'description', 'quantity', 'required_quantity', 'sort_order', 'created_at']),
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
        def make_to_dict(short_fields, fs):
            def to_dict(self, full=False):
                result = {}
                for f in (fs if full else short_fields):
                    val = getattr(self, f)
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    result[f] = val
                if isinstance(self, Stage):
                    result.update(stage_manufacturers(self))
                    result['details'] = [detail.to_dict() for detail in self.details.all()]
                return result
            return to_dict
        cls.to_dict = make_to_dict(tuple(fields), tuple(full_fields))

_add_to_dict_methods()
