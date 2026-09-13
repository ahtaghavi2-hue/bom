"""Tests for cumulative BOM inventory requirements used by the classic UI."""

from app import get_total_required


def make_bom(order_count=2):
    return {
        'nodes': {
            'p1': {'id': 'p1', 'type': 'product', 'order_count': order_count,
                   'parent': None, 'children': ['a1']},
            'a1': {'id': 'a1', 'type': 'assembly', 'required_quantity': 2,
                   'parent': 'p1', 'children': ['a2']},
            'a2': {'id': 'a2', 'type': 'assembly', 'required_quantity': 3,
                   'parent': 'a1', 'children': ['r1']},
            'r1': {'id': 'r1', 'type': 'part', 'required_quantity': 4,
                   'parent': 'a2', 'children': []},
        },
        'root_ids': ['p1'],
    }


def test_total_required_multiplies_every_bom_level():
    data = make_bom()

    assert get_total_required('a1', data) == 4
    assert get_total_required('a2', data) == 12
    assert get_total_required('r1', data) == 48


def test_schedule_quantity_overrides_product_order_count():
    data = make_bom(order_count=99)

    assert get_total_required('r1', data, order_count=2) == 48


def test_invalid_or_zero_quantities_use_legacy_minimum_one():
    data = make_bom(order_count=0)
    data['nodes']['a1']['required_quantity'] = 0
    data['nodes']['r1']['required_quantity'] = 'invalid'

    assert get_total_required('r1', data) == 3


def test_cycle_does_not_loop_forever():
    data = make_bom()
    data['nodes']['a1']['parent'] = 'a2'

    assert get_total_required('r1', data) == 24
