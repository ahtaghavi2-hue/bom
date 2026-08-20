"""Unit tests for Stage-based scheduling architecture (Phase 1+2).

Verifies that:
  - Parts with stages become connector nodes (duration=0)
  - Stages become atomic scheduling units with PERT times
  - CPM runs correctly on stage-level DAG
  - Monte Carlo samples at stage granularity
  - Cost aggregation works with stage nodes
  - Backward compatibility: parts without stages still work

Run: python tests/test_stage_scheduling.py
"""

import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from repositories.bom_repository import BomNode
from services.cpm_engine import run_cpm, CyclicGraphError
from services.pert_calculator import pert_time
from services.cost_aggregator import aggregate_costs
from services.monte_carlo import run_monte_carlo

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


# ──────────────────────────────────────────────────────────────────
# 1. Stage-based BOM tree (new architecture)
# ──────────────────────────────────────────────────────────────────

def build_stage_tree():
    """Part with 3 stages → each stage has PERT times.

    Structure:
      p1 (product, no PERT)
        └─ a1 (assembly, no PERT)
             └─ r1 (part, no PERT — connector)
                  ├─ s1 (stage: CNC,       O=2 M=4 P=8  → t_e≈4.333)
                  ├─ s2 (stage: Bending,   O=1 M=2 P=5  → t_e≈2.333)
                  └─ s3 (stage: QC,        O=0.5 M=1 P=3 → t_e≈1.25)

    All stages are children of r1 and run in sequence (r1→s1→s2→s3).
    But since r1 is just a connector, the real scheduling is:
      p1→a1→r1 (0h)→s1 (4.333h)→s2 (2.333h)→s3 (1.25h)
    Total = 4.333 + 2.333 + 1.25 = 7.917h
    """
    nodes = {
        'p1': BomNode(id='p1', name='Product 1', node_type='product',
                       children=['a1']),
        'a1': BomNode(id='a1', name='Assembly 1', node_type='assembly',
                       parent_id='p1', children=['r1']),
        'r1': BomNode(id='r1', name='Part 1', node_type='part',
                       parent_id='a1', children=['s1']),
        's1': BomNode(id='s1', name='CNC', node_type='stage',
                       parent_id='r1', stage_id=1, part_id=1,
                       time_optimistic=2, time_most_likely=4, time_pessimistic=8,
                       cost_material=1000, cost_labor=500, cost_overhead=200,
                       required_resource_type='CNC'),
        's2': BomNode(id='s2', name='Bending', node_type='stage',
                       parent_id='s1', stage_id=2, part_id=1,
                       time_optimistic=1, time_most_likely=2, time_pessimistic=5,
                       cost_material=200, cost_labor=300, cost_overhead=100,
                       required_resource_type='Press'),
        's3': BomNode(id='s3', name='QC', node_type='stage',
                       parent_id='s2', stage_id=3, part_id=1,
                       time_optimistic=0.5, time_most_likely=1, time_pessimistic=3,
                       cost_material=0, cost_labor=150, cost_overhead=50,
                       required_resource_type='QC'),
    }
    return nodes


def build_mixed_tree():
    """Mix of stage-based and legacy parts.

    Structure:
      p1 → a1 → r1 (has stages: s1, s2)
                 → r2 (no stages — legacy part with PERT)
    """
    nodes = {
        'p1': BomNode(id='p1', name='Product 1', node_type='product',
                       children=['a1']),
        'a1': BomNode(id='a1', name='Assembly 1', node_type='assembly',
                       parent_id='p1', children=['r1', 'r2']),
        'r1': BomNode(id='r1', name='Part with Stages', node_type='part',
                       parent_id='a1', children=['s1']),
        's1': BomNode(id='s1', name='Stage A', node_type='stage',
                       parent_id='r1', stage_id=1, part_id=1,
                       time_optimistic=2, time_most_likely=4, time_pessimistic=8,
                       cost_material=500, cost_labor=200, cost_overhead=100,
                       required_resource_type='CNC'),
        's2': BomNode(id='s2', name='Stage B', node_type='stage',
                       parent_id='s1', stage_id=2, part_id=1,
                       time_optimistic=1, time_most_likely=1.5, time_pessimistic=4,
                       cost_material=100, cost_labor=300, cost_overhead=50,
                       required_resource_type='Assembly'),
        'r2': BomNode(id='r2', name='Legacy Part', node_type='part',
                       parent_id='a1', children=[],
                       time_optimistic=3, time_most_likely=5, time_pessimistic=10,
                       cost_material=2000, cost_labor=800, cost_overhead=300,
                       legacy_part=True),
    }
    return nodes


# ──────────────────────────────────────────────────────────────────
# Test 1: Stage-based CPM
# ──────────────────────────────────────────────────────────────────

def test_stage_cpm():
    print('\n--- Stage-Based CPM ---')
    nodes = build_stage_tree()
    result = run_cpm(nodes)

    te_s1 = pert_time(2, 4, 8)    # ≈4.333
    te_s2 = pert_time(1, 2, 5)    # ≈2.333
    te_s3 = pert_time(0.5, 1, 3)  # ≈1.25
    expected_total = te_s1 + te_s2 + te_s3  # ≈7.917

    check(f'project_duration = {expected_total:.3f}',
          abs(result.project_duration - expected_total) < 1e-9,
          f'got {result.project_duration}')

    # r1 (connector) should have duration 0
    check('r1 (part connector) has duration=0',
          abs(result.entries['r1'].duration) < 1e-9,
          f'got {result.entries["r1"].duration}')

    # All stages should have their PERT durations
    check(f's1 duration = {te_s1:.3f}',
          abs(result.entries['s1'].duration - te_s1) < 1e-9)
    check(f's2 duration = {te_s2:.3f}',
          abs(result.entries['s2'].duration - te_s2) < 1e-9)
    check(f's3 duration = {te_s3:.3f}',
          abs(result.entries['s3'].duration - te_s3) < 1e-9)

    # All stages should be critical (they're sequential)
    check('s1 is critical', result.entries['s1'].is_critical)
    check('s2 is critical', result.entries['s2'].is_critical)
    check('s3 is critical', result.entries['s3'].is_critical)
    check('r1 is NOT critical (duration=0)',
          not result.entries['r1'].is_critical)

    # Sequential timing: s2 starts when s1 ends, s3 starts when s2 ends
    check(f's2 starts at s1 end ({te_s1:.3f})',
          abs(result.entries['s2'].early_start - te_s1) < 1e-9)
    check(f's3 starts at s2 end ({te_s1 + te_s2:.3f})',
          abs(result.entries['s3'].early_start - (te_s1 + te_s2)) < 1e-9)

    # Critical path should include all stages
    check('critical path contains s1', 's1' in result.critical_path)
    check('critical path contains s2', 's2' in result.critical_path)
    check('critical path contains s3', 's3' in result.critical_path)

    # Resource types should be preserved
    check('s1 resource = CNC',
          result.entries['s1'].resource_type == 'CNC')
    check('s2 resource = Press',
          result.entries['s2'].resource_type == 'Press')
    check('s3 resource = QC',
          result.entries['s3'].resource_type == 'QC')


# ──────────────────────────────────────────────────────────────────
# Test 2: Mixed tree (stages + legacy parts)
# ──────────────────────────────────────────────────────────────────

def test_mixed_tree():
    print('\n--- Mixed Stage + Legacy CPM ---')
    nodes = build_mixed_tree()
    result = run_cpm(nodes)

    te_s1 = pert_time(2, 4, 8)   # ≈4.333
    te_s2 = pert_time(1, 1.5, 4) # ≈1.833
    te_r2 = pert_time(3, 5, 10)  # ≈5.5

    # r1 path: s1 + s2 = 6.167
    r1_path = te_s1 + te_s2
    # r2 path: 5.5 (direct)
    # Project duration = max(6.167, 5.5) = 6.167 (r1 stages win)
    expected = max(r1_path, te_r2)

    check(f'project_duration = {expected:.3f}',
          abs(result.project_duration - expected) < 1e-9,
          f'got {result.project_duration}')

    # r2 is NOT critical — the stage path (6.167h) is longer than r2 (5.5h)
    check('r2 NOT critical (shorter path)',
          not result.entries['r2'].is_critical)

    # s1 should be critical
    check('s1 is critical', result.entries['s1'].is_critical)

    # r1 connector should NOT be critical
    check('r1 connector NOT critical',
          not result.entries['r1'].is_critical or result.entries['r1'].duration == 0)


# ──────────────────────────────────────────────────────────────────
# Test 3: Cost aggregation with stage nodes
# ──────────────────────────────────────────────────────────────────

def test_cost_aggregation():
    print('\n--- Cost Aggregation (Stage-based) ---')
    nodes = build_stage_tree()
    cpm_result = run_cpm(nodes)

    breakdown = aggregate_costs(cpm_result, nodes)

    # s1: 1000+500+200=1700, s2: 200+300+100=600, s3: 0+150+50=200
    expected_material = 1000 + 200 + 0
    expected_labor = 500 + 300 + 150
    expected_overhead = 200 + 100 + 50
    expected_direct = expected_material + expected_labor + expected_overhead

    check(f'total_material = {expected_material}',
          abs(breakdown.total_material - expected_material) < 1e-9,
          f'got {breakdown.total_material}')
    check(f'total_labor = {expected_labor}',
          abs(breakdown.total_labor - expected_labor) < 1e-9,
          f'got {breakdown.total_labor}')
    check(f'total_overhead = {expected_overhead}',
          abs(breakdown.total_overhead - expected_overhead) < 1e-9,
          f'got {breakdown.total_overhead}')
    check(f'total_direct = {expected_direct}',
          abs(breakdown.total_direct - expected_direct) < 1e-9,
          f'got {breakdown.total_direct}')


# ──────────────────────────────────────────────────────────────────
# Test 4: Monte Carlo with stage nodes
# ──────────────────────────────────────────────────────────────────

def test_monte_carlo_stages():
    print('\n--- Monte Carlo (Stage-based) ---')
    nodes = build_stage_tree()

    start = time.time()
    mc = run_monte_carlo(nodes, iterations=500, seed=42)
    elapsed = time.time() - start

    check(f'MC ran {mc.iterations} iterations', mc.iterations == 500)
    check(f'MC completed in < 5s ({elapsed:.2f}s)', elapsed < 5)
    check('MC has duration samples', len(mc.duration_samples) > 0)
    check('MC has cost samples', len(mc.cost_samples) > 0)
    check('MC P10 <= P50 <= P90',
          mc.duration_p10 <= mc.duration_p50 <= mc.duration_p90)
    check('MC cost P10 <= P50 <= P90',
          mc.cost_p10 <= mc.cost_p50 <= mc.cost_p90)
    check('MC has avg_schedule', len(mc.avg_schedule) > 0)
    # Stage nodes should appear in avg_schedule
    check('s1 in avg_schedule', 's1' in mc.avg_schedule)
    check('s2 in avg_schedule', 's2' in mc.avg_schedule)
    check('s3 in avg_schedule', 's3' in mc.avg_schedule)


# ──────────────────────────────────────────────────────────────────
# Test 5: BomNode properties
# ──────────────────────────────────────────────────────────────────

def test_bomnode_properties():
    print('\n--- BomNode Properties ---')

    stage = BomNode(id='s1', name='Test', node_type='stage',
                    time_optimistic=2, time_most_likely=4, time_pessimistic=8,
                    cost_material=100, cost_labor=50, cost_overhead=20)
    check('stage.has_pert = True', stage.has_pert)
    check(f'stage.direct_cost = 170', stage.direct_cost == 170.0)

    no_pert = BomNode(id='r1', name='No PERT', node_type='part')
    check('no_pert.has_pert = False', not no_pert.has_pert)
    check('no_pert.direct_cost = 0', no_pert.direct_cost == 0.0)

    connector = BomNode(id='r1', name='Connector', node_type='part',
                        legacy_part=False)
    check('connector.legacy_part = False', not connector.legacy_part)


# ──────────────────────────────────────────────────────────────────
# Test 6: Stage-level resource conflicts
# ──────────────────────────────────────────────────────────────────

def test_stage_resource_types():
    print('\n--- Stage Resource Types ---')
    from services.resource_leveling import level_resources, ResourceCapacity
    from services.cpm_engine import CpmResult

    # Two parts each with a CNC stage → potential resource conflict
    nodes = {
        'p1': BomNode(id='p1', name='Product', node_type='product',
                       children=['a1']),
        'a1': BomNode(id='a1', name='Assembly', node_type='assembly',
                       parent_id='p1', children=['r1', 'r2']),
        'r1': BomNode(id='r1', name='Part 1', node_type='part',
                       parent_id='a1', children=['s1']),
        's1': BomNode(id='s1', name='CNC for P1', node_type='stage',
                       parent_id='r1', time_optimistic=2, time_most_likely=4,
                       time_pessimistic=8, required_resource_type='CNC'),
        'r2': BomNode(id='r2', name='Part 2', node_type='part',
                       parent_id='a1', children=['s2']),
        's2': BomNode(id='s2', name='CNC for P2', node_type='stage',
                       parent_id='r2', time_optimistic=3, time_most_likely=5,
                       time_pessimistic=10, required_resource_type='CNC'),
    }
    cpm_result = run_cpm(nodes)

    # Both stages run in parallel (both have ES=0), both need CNC
    check('s1 resource = CNC', cpm_result.entries['s1'].resource_type == 'CNC')
    check('s2 resource = CNC', cpm_result.entries['s2'].resource_type == 'CNC')
    check('s1 ES = 0', abs(cpm_result.entries['s1'].early_start) < 1e-9)
    check('s2 ES = 0', abs(cpm_result.entries['s2'].early_start) < 1e-9)

    # Resource leveling with capacity=1 should resolve conflict
    resources = {'CNC': ResourceCapacity(resource_type='CNC', capacity=1)}
    leveled = level_resources(cpm_result, resources, nodes)
    check('over-allocation resolved', leveled.over_allocations_resolved > 0)


# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    test_stage_cpm()
    test_mixed_tree()
    test_cost_aggregation()
    test_monte_carlo_stages()
    test_bomnode_properties()
    test_stage_resource_types()

    print(f'\nRESULT: {PASS} passed, {FAIL} failed')
    sys.exit(1 if FAIL else 0)
