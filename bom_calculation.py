"""Node-local inventory calculation and shared API integer validation."""
import re


def nonnegative_int(value, field):
    """Accept JSON integers or decimal form strings, never truncate floats."""
    if isinstance(value, bool) or not (
        isinstance(value, int) or isinstance(value, str) and re.fullmatch(r'[0-9]+', value)
    ):
        raise ValueError(f'{field} must be a nonnegative integer')
    number = int(value)
    if number < 0:
        raise ValueError(f'{field} must be a nonnegative integer')
    return number


def validate_quantities(data, fields):
    return {field: nonnegative_int(data[field], field) for field in fields if field in data}


def attach_calculations(data):
    """Each incoming edge uses its own coefficient; only shortage propagates.

    Stock is read-only and never pooled, including between same-code siblings.
    Unreachable legacy nodes receive zero demand; cycles are rejected explicitly.
    """
    nodes = data['nodes']
    visited = set()
    active = set()
    for node in nodes.values():
        node.update(required_total=0, shortage=0, stock_used=0)

    def visit(node_id, gross):
        if node_id in active:
            raise ValueError('Cycle in BOM hierarchy')
        if node_id in visited:
            raise ValueError('BOM node has multiple incoming edges')
        node = nodes.get(node_id)
        if node is None:
            return
        active.add(node_id)
        visited.add(node_id)
        stock = node.get('quantity')
        stock = 0 if stock is None else stock
        shortage = max(gross - stock, 0)
        node.update(required_total=gross, shortage=shortage, stock_used=min(gross, stock))
        for child_id in node.get('children', []):
            child = nodes.get(child_id)
            if child is not None:
                coefficient = child.get('required_quantity')
                coefficient = 1 if coefficient is None else coefficient
                visit(child_id, shortage * coefficient)
        active.remove(node_id)

    for root_id in data['root_ids']:
        visit(root_id, nodes[root_id].get('order_count') or 0)
    return data
