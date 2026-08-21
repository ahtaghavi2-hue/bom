"""Unit tests for CPM Engine + integration test with Monte Carlo.

Uses a small hand-crafted BOM tree to verify:
  - Forward/backward pass correctness
  - Critical path identification
  - Float computation
  - Monte Carlo runs within time budget

Hand-calculated example:
  Product P1
    └─ Assembly A1 (no PERT — duration 0)
         ├─ Part R1: O=2, M=4, P=8  -> t_e=4.33
         ├─ Part R2: O=3, M=5, P=10 -> t_e=5.50
         └─ Part R3: O=1, M=2, P=5  -> t_e=2.33

  Since A1 is parent of all three, and A1 has no PERT (duration 0),
  the DAG edges are:
    A1 -> R1, R1 -> (no children)
    A1 -> R2
    A1 -> R3

  All three parts are parallel from A1.
  Project duration = max(4.33, 5.50, 2.33) = 5.50 (R2 is critical)

Run: python tests/test_cpm.py
"""

import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from repositories.bom_repository import BomNode
from services.cpm_engine import run_cpm, CyclicGraphError
from services.pert_calculator import pert_time

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {detail}')


def build_simple_tree():
    """Build a simple BOM tree for testing.

    Structure:
      p1 (product, no PERT)
        └─ a1 (assembly, no PERT)
             ├─ r1 (part, O=2 M=4 P=8)
             ├─ r2 (part, O=3 M=5 P=10)  ← longest -> critical
             └─ r3 (part, O=1 M=2 P=5)
    """
    nodes = {
        'p1': BomNode(id='p1', name='Product 1', node_type='product', children=['a1']),
        'a1': BomNode(id='a1', name='Assembly 1', node_type='assembly', parent_id='p1', children=['r1', 'r2', 'r3']),
        'r1': BomNode(
            id='r1', name='Part 1', node_type='part', parent_id='a1',
            time_optimistic=2, time_most_likely=4, time_pessimistic=8,
            cost_material=1000, cost_labor=500, cost_overhead=200,
            required_resource_type='CNC',
        ),
        'r2': BomNode(
            id='r2', name='Part 2', node_type='part', parent_id='a1',
            time_optimistic=3, time_most_likely=5, time_pessimistic=10,
            cost_material=2000, cost_labor=800, cost_overhead=300,
            required_resource_type='CNC',
        ),
        'r3': BomNode(
            id='r3', name='Part 3', node_type='part', parent_id='a1',
            time_optimistic=1, time_most_likely=2, time_pessimistic=5,
            cost_material=500, cost_labor=300, cost_overhead=100,
            required_resource_type='Assembly',
        ),
    }
    return nodes


def build_sequential_tree():
    """Build a sequential BOM tree (chain dependency).

    Structure:
      p1 -> a1 -> r1 -> a2 -> r2

    r1: O=2, M=3, P=7 -> t_e = (2+12+7)/6 = 21/6 = 3.5
    r2: O=4, M=6, P=12 -> t_e = (4+24+12)/6 = 40/6 = 6.667

    Project duration = 3.5 + 6.667 = 10.167
    Both r1 and r2 are critical.
    """
    nodes = {
        'p1': BomNode(id='p1', name='Product 1', node_type='product', children=['a1']),
        'a1': BomNode(id='a1', name='Assembly 1', node_type='assembly', parent_id='p1', children=['r1']),
        'r1': BomNode(
            id='r1', name='Part 1', node_type='part', parent_id='a1',
            time_optimistic=2, time_most_likely=3, time_pessimistic=7,
            cost_material=1000, cost_labor=500, cost_overhead=200,
        ),
        'a2': BomNode(id='a2', name='Assembly 2', node_type='assembly', parent_id='r1', children=['r2']),
        'r2': BomNode(
            id='r2', name='Part 2', node_type='part', parent_id='a2',
            time_optimistic=4, time_most_likely=6, time_pessimistic=12,
            cost_material=2000, cost_labor=800, cost_overhead=300,
        ),
    }
    return nodes


def test_simple_parallel():
    """Test parallel tree: all parts start at the same time."""
    print('\n--- CPM: Simple Parallel Tree ---')

    nodes = build_simple_tree()
    result = run_cpm(nodes)

    # Expected durations:
    # r1: (2 + 4*4 + 8)/6 = 26/6 ~ 4.333
    # r2: (3 + 4*5 + 10)/6 = 33/6 = 5.5
    # r3: (1 + 4*2 + 5)/6 = 14/6 ~ 2.333

    te_r1 = pert_time(2, 4, 8)
    te_r2 = pert_time(3, 5, 10)
    te_r3 = pert_time(1, 2, 5)

    check('project_duration = 5.5 (r2 is longest)',
          abs(result.project_duration - te_r2) < 1e-9,
          f'got {result.project_duration}')

    # r2 should be critical
    check('r2 is critical', result.entries['r2'].is_critical)
    check('r1 is NOT critical (has float)', not result.entries['r1'].is_critical)
    check('r3 is NOT critical (has float)', not result.entries['r3'].is_critical)

    # All start at time 0 (parallel)
    check('r1 early_start = 0', abs(result.entries['r1'].early_start) < 1e-9)
    check('r2 early_start = 0', abs(result.entries['r2'].early_start) < 1e-9)
    check('r3 early_start = 0', abs(result.entries['r3'].early_start) < 1e-9)

    # r1 early_finish = 4.333
    check(f'r1 early_finish ~ {te_r1:.3f}',
          abs(result.entries['r1'].early_finish - te_r1) < 1e-9)

    # r3 total_float = 5.5 - 2.333 = 3.167
    expected_float_r3 = te_r2 - te_r3
    check(f'r3 total_float ~ {expected_float_r3:.3f}',
          abs(result.entries['r3'].total_float - expected_float_r3) < 1e-9,
          f'got {result.entries["r3"].total_float}')

    # Critical path should contain r2
    check('critical path contains r2', 'r2' in result.critical_path)


def test_sequential():
    """Test sequential tree: parts run one after another."""
    print('\n--- CPM: Sequential Tree ---')

    nodes = build_sequential_tree()
    result = run_cpm(nodes)

    te_r1 = pert_time(2, 3, 7)  # 3.5
    te_r2 = pert_time(4, 6, 12)  # 6.667
    expected_duration = te_r1 + te_r2

    check(f'project_duration = {expected_duration:.3f}',
          abs(result.project_duration - expected_duration) < 1e-9,
          f'got {result.project_duration}')

    # r1: ES=0, EF=3.5, LS=0, LF=3.5 -> critical
    check('r1 is critical', result.entries['r1'].is_critical)
    check('r1 ES=0', abs(result.entries['r1'].early_start) < 1e-9)
    check(f'r1 EF={te_r1:.3f}',
          abs(result.entries['r1'].early_finish - te_r1) < 1e-9)

    # r2: ES=3.5, EF=10.167, LS=3.5, LF=10.167 -> critical
    check('r2 is critical', result.entries['r2'].is_critical)
    check(f'r2 ES={te_r1:.3f}',
          abs(result.entries['r2'].early_start - te_r1) < 1e-9)

    # Critical path includes all nodes: p1 -> a1 -> r1 -> a2 -> r2
    check('critical path has 5 nodes', len(result.critical_path) == 5)
    check('critical path = [p1, a1, r1, a2, r2]',
          result.critical_path == ['p1', 'a1', 'r1', 'a2', 'r2'],
          f'got {result.critical_path}')
    check('r1 and r2 on critical path',
          'r1' in result.critical_path and 'r2' in result.critical_path)


def test_no_pert_nodes():
    """Test that nodes without PERT have zero duration."""
    print('\n--- CPM: No PERT Nodes ---')

    nodes = {
        'p1': BomNode(id='p1', name='Product', node_type='product', children=['a1']),
        'a1': BomNode(id='a1', name='Assembly', node_type='assembly', parent_id='p1', children=['r1']),
        'r1': BomNode(id='r1', name='Part', node_type='part', parent_id='a1',
                       # No PERT values
                       cost_material=500, cost_labor=200, cost_overhead=100),
    }
    result = run_cpm(nodes)
    check('project_duration = 0 (no PERT)', result.project_duration == 0)
    check('r1 is NOT critical (no duration)', not result.entries['r1'].is_critical)


def test_cyclic_graph():
    """Test that a cyclic graph raises CyclicGraphError."""
    print('\n--- CPM: Cyclic Graph Detection ---')

    # Create a cycle: r1 parent of a1, a1 parent of r1
    nodes = {
        'r1': BomNode(id='r1', name='Part 1', node_type='part', parent_id='a1',
                       time_optimistic=2, time_most_likely=3, time_pessimistic=5),
        'a1': BomNode(id='a1', name='Assembly 1', node_type='assembly', parent_id='r1',
                       time_optimistic=1, time_most_likely=2, time_pessimistic=4),
    }
    # We need to set up the adjacency properly
    # a1 is parent of r1 AND r1 is parent of a1 -> cycle
    try:
        result = run_cpm(nodes)
        check('CyclicGraphError raised', False, 'no error raised')
    except CyclicGraphError:
        check('CyclicGraphError raised', True)


def test_monte_carlo_performance():
    """Test Monte Carlo runs within performance budget (< 5s for small tree)."""
    print('\n--- Monte Carlo Performance ---')

    from services.monte_carlo import run_monte_carlo

    # Build a medium tree (20 parts)
    nodes = {
        'p1': BomNode(id='p1', name='Product', node_type='product', children=['a1']),
        'a1': BomNode(id='a1', name='Assembly', node_type='assembly', parent_id='p1', children=[]),
    }
    for i in range(1, 21):
        nid = f'r{i}'
        parent = 'a1'
        nodes[nid] = BomNode(
            id=nid, name=f'Part {i}', node_type='part', parent_id=parent,
            time_optimistic=1 + i * 0.5,
            time_most_likely=2 + i * 0.5,
            time_pessimistic=4 + i * 0.5,
            cost_material=i * 1000,
            cost_labor=i * 500,
            cost_overhead=i * 200,
        )
        nodes['a1'].children.append(nid)

    start = time.time()
    result = run_monte_carlo(nodes, iterations=1000, seed=42)
    elapsed = time.time() - start

    check('MC iterations = 1000', result.iterations == 1000)
    check(f'MC completed in < 5s (took {elapsed:.2f}s)', elapsed < 5.0)
    check('MC has duration samples', len(result.duration_samples) == 1000)
    check('MC has cost samples', len(result.cost_samples) == 1000)
    check('MC P50 exists', result.duration_p50 > 0)
    check('MC P10 <= P50 <= P90',
          result.duration_p10 <= result.duration_p50 <= result.duration_p90)
    check('MC cost P10 <= P50 <= P90',
          result.cost_p10 <= result.cost_p50 <= result.cost_p90)
    check('MC has avg_schedule', len(result.avg_schedule) > 0)


def test_monte_carlo_with_deadline():
    """Test Monte Carlo probability on time calculation."""
    print('\n--- Monte Carlo Deadline Probability ---')

    from services.monte_carlo import run_monte_carlo

    nodes = build_simple_tree()
    # r2 expected = 5.5h, so a target of 10h should have high probability
    result = run_monte_carlo(nodes, iterations=500, target_hours=10.0, seed=42)

    check('probability_on_time is set', result.probability_on_time is not None)
    check(f'P(finish <= 10h) > 0.9 (got {result.probability_on_time:.3f})',
          result.probability_on_time > 0.9)


if __name__ == '__main__':
    test_simple_parallel()
    test_sequential()
    test_no_pert_nodes()
    test_cyclic_graph()
    test_monte_carlo_performance()
    test_monte_carlo_with_deadline()

    print(f'\nRESULT: {PASS} passed, {FAIL} failed')
    sys.exit(1 if FAIL else 0)
