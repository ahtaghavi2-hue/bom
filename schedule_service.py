"""Shared production-schedule validation and work-order generation.

Both the classic routes (`app.py`) and `/api/v2` (`api_v2.py`) use these helpers so
payload rules and BOM multipliers stay single-sourced.
"""
from datetime import datetime

from extensions import db
from models import Assembly, Product, WorkOrder

SCHEDULE_STATUSES = ('planned', 'in_progress', 'completed', 'cancelled')
SCHEDULE_PRIORITIES = ('low', 'normal', 'high', 'urgent')


class ScheduleValidationError(ValueError):
    """Raised for a payload a schedule route must reject with 400."""


def _parse_date(value, field):
    if value in (None, ''):
        return None
    if not isinstance(value, str):
        raise ScheduleValidationError(f'{field} must be an ISO date string')
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ScheduleValidationError(f'{field} must be an ISO date string') from None


def validate_schedule_payload(data, partial=False):
    """Validate a schedule payload and return only the supplied fields.

    ``partial`` is used by updates: absent keys are left untouched and dates may
    be cleared with ``null``.
    """
    if not isinstance(data, dict):
        raise ScheduleValidationError('JSON object required')
    clean = {}
    if not partial or 'product_id' in data:
        product_id = data.get('product_id')
        if type(product_id) is not int or not db.session.get(Product, product_id):
            raise ScheduleValidationError('Invalid product_id')
        clean['product_id'] = product_id
    if not partial or 'quantity' in data:
        quantity = data.get('quantity', 1)
        if type(quantity) is not int or quantity < 1:
            raise ScheduleValidationError('quantity must be a positive integer')
        clean['quantity'] = quantity
    if 'status' in data:
        if data['status'] not in SCHEDULE_STATUSES:
            raise ScheduleValidationError('status must be one of: ' + ', '.join(SCHEDULE_STATUSES))
        clean['status'] = data['status']
    if 'priority' in data:
        if data['priority'] not in SCHEDULE_PRIORITIES:
            raise ScheduleValidationError('priority must be one of: ' + ', '.join(SCHEDULE_PRIORITIES))
        clean['priority'] = data['priority']
    for field in ('start_date', 'end_date'):
        if field in data:
            clean[field] = _parse_date(data[field], field)
    if 'notes' in data:
        notes = data['notes']
        if notes is not None and not isinstance(notes, str):
            raise ScheduleValidationError('notes must be a string')
        clean['notes'] = notes or ''
    return clean


def part_requirement_totals(product_id, quantity):
    """Return ``{part_id: units}`` for one production run of ``quantity``.

    Every level multiplies its own ``required_quantity``, so a 4×3×2 chain for
    five units yields 120 — the same coefficients ``attach_calculations`` uses.
    """
    totals = {}

    def walk(assembly, multiplier):
        for part in assembly.parts.all():
            coefficient = part.required_quantity if part.required_quantity is not None else 1
            totals[part.id] = totals.get(part.id, 0) + multiplier * coefficient
        for child in Assembly.query.filter_by(parent_id=assembly.id).all():
            child_required = child.required_quantity if child.required_quantity is not None else 1
            walk(child, multiplier * child_required)

    for root in Assembly.query.filter_by(product_id=product_id, parent_id=None).all():
        # The product → assembly edge also carries the assembly's coefficient.
        walk(root, root.required_quantity if root.required_quantity is not None else 1)
    return {part_id: total * quantity for part_id, total in totals.items()}


def generate_work_orders(schedule):
    """Create pending work orders for a schedule with nested BOM quantities."""
    for part_id, total in part_requirement_totals(schedule.product_id, schedule.quantity).items():
        db.session.add(WorkOrder(schedule_id=schedule.id, part_id=part_id, quantity=total,
                                 status='pending', due_date=schedule.end_date))
    db.session.commit()
