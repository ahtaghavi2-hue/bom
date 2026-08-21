"""Monte Carlo Simulation Engine for project scheduling.

Runs N iterations (default 1000), sampling random durations from
a Triangular distribution (O, M, P) for each activity, then runs CPM
to get the project duration and cost for that iteration.

Outputs:
  - Distribution of project completion times
  - Distribution of total costs
  - P10, P50, P90 percentiles
  - Probability of completing before a deadline
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from services.pert_calculator import pert_time, pert_std_dev
from services.cpm_engine import run_cpm, CpmResult, CyclicGraphError
from repositories.bom_repository import BomNode


@dataclass
class MonteCarloResult:
    """Aggregated result of a Monte Carlo simulation."""
    iterations: int = 0
    # Duration distribution
    duration_samples: List[float] = field(default_factory=list)
    duration_p10: float = 0.0
    duration_p50: float = 0.0
    duration_p90: float = 0.0
    duration_mean: float = 0.0
    duration_std: float = 0.0
    # Cost distribution
    cost_samples: List[float] = field(default_factory=list)
    cost_p10: float = 0.0
    cost_p50: float = 0.0
    cost_p90: float = 0.0
    cost_mean: float = 0.0
    # Deadline analysis
    probability_on_time: Optional[float] = None  # 0-1
    target_delivery_date: Optional[str] = None
    # Critical path frequency (how often each node appears on CP)
    critical_frequency: Dict[str, int] = field(default_factory=dict)
    # Per-node schedule stats (average start/finish across all iterations)
    avg_schedule: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    # Cost snapshots (day_number -> cumulative_total)
    cost_curve: List[Tuple[int, float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'iterations': self.iterations,
            'duration': {
                'p10': self.duration_p10,
                'p50': self.duration_p50,
                'p90': self.duration_p90,
                'mean': self.duration_mean,
                'std': self.duration_std,
                'samples': self.duration_samples,
            },
            'cost': {
                'p10': self.cost_p10,
                'p50': self.cost_p50,
                'p90': self.cost_p90,
                'mean': self.cost_mean,
                'samples': self.cost_samples,
            },
            'probability_on_time': self.probability_on_time,
            'critical_frequency': self.critical_frequency,
            'avg_schedule': {
                k: {'start': v[0], 'finish': v[1]}
                for k, v in self.avg_schedule.items()
            },
            'cost_curve': [{'day': d, 'cumulative': c} for d, c in self.cost_curve],
        }


def _sample_triangular(optimistic: float, most_likely: float, pessimistic: float) -> float:
    """Sample from a Triangular distribution using inverse CDF."""
    if optimistic == pessimistic:
        return optimistic

    u = random.random()
    fc = (most_likely - optimistic) / (pessimistic - optimistic)

    if u < fc:
        return optimistic + math.sqrt(u * (pessimistic - optimistic) * (most_likely - optimistic))
    else:
        return pessimistic - math.sqrt(
            (1 - u) * (pessimistic - optimistic) * (pessimistic - most_likely)
        )


def _percentile(data: List[float], p: float) -> float:
    """Compute the p-th percentile (0-100) of a sorted list."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def run_monte_carlo(
    nodes: Dict[str, BomNode],
    iterations: int = 1000,
    target_hours: Optional[float] = None,
    project_settings: Optional[dict] = None,
    seed: Optional[int] = None,
) -> MonteCarloResult:
    """Run Monte Carlo simulation on a BOM tree.

    Args:
        nodes: Full BOM tree from bom_repository.load_bom_tree().
        iterations: Number of simulation runs.
        target_hours: If set, compute probability of finishing within this time.
        project_settings: Optional dict with 'daily_penalty', 'total_budget', etc.
        seed: Optional random seed for reproducibility.

    Returns:
        MonteCarloResult with all statistics.
    """
    if seed is not None:
        random.seed(seed)

    duration_samples: List[float] = []
    cost_samples: List[float] = []
    cp_counter: Dict[str, int] = defaultdict(int)
    node_start_sums: Dict[str, float] = defaultdict(float)
    node_finish_sums: Dict[str, float] = defaultdict(float)
    node_count: Dict[str, int] = defaultdict(int)

    # Identify parts with PERT estimates
    pert_parts = {nid: node for nid, node in nodes.items() if node.has_pert}

    for _ in range(iterations):
        # Create a copy of nodes with sampled durations
        sampled_nodes: Dict[str, BomNode] = {}
        for nid, node in nodes.items():
            if nid in pert_parts:
                sampled_duration = _sample_triangular(
                    node.time_optimistic, node.time_most_likely, node.time_pessimistic
                )
                # We need to adjust the PERT values to force CPM to use sampled duration
                # Easiest: set all three equal to the sampled value
                sampled_nodes[nid] = BomNode(
                    id=node.id, name=node.name, node_type=node.node_type,
                    parent_id=node.parent_id, children=node.children,
                    time_optimistic=sampled_duration,
                    time_most_likely=sampled_duration,
                    time_pessimistic=sampled_duration,
                    cost_material=node.cost_material,
                    cost_labor=node.cost_labor,
                    cost_overhead=node.cost_overhead,
                    required_resource_type=node.required_resource_type,
                    storage_cost_per_day=node.storage_cost_per_day,
                    quantity=node.quantity,
                    required_quantity=node.required_quantity,
                )
            else:
                sampled_nodes[nid] = node

        try:
            result = run_cpm(sampled_nodes)
        except CyclicGraphError:
            continue  # skip invalid iterations

        duration_samples.append(result.project_duration)

        # Compute cost for this iteration
        total_cost = _compute_cost(result, nodes, project_settings)
        cost_samples.append(total_cost)

        # Track critical path frequency
        for nid in result.critical_path:
            cp_counter[nid] += 1

        # Track per-node schedule
        for nid, entry in result.entries.items():
            node_start_sums[nid] += entry.early_start
            node_finish_sums[nid] += entry.early_finish
            node_count[nid] += 1

    if not duration_samples:
        return MonteCarloResult(iterations=0)

    # ── Compute statistics ──
    mc = MonteCarloResult(iterations=len(duration_samples))
    mc.duration_samples = sorted(duration_samples)
    mc.duration_p10 = _percentile(duration_samples, 10)
    mc.duration_p50 = _percentile(duration_samples, 50)
    mc.duration_p90 = _percentile(duration_samples, 90)
    mc.duration_mean = sum(duration_samples) / len(duration_samples)
    mc.duration_std = (
        sum((d - mc.duration_mean) ** 2 for d in duration_samples) / len(duration_samples)
    ) ** 0.5

    mc.cost_samples = sorted(cost_samples)
    mc.cost_p10 = _percentile(cost_samples, 10)
    mc.cost_p50 = _percentile(cost_samples, 50)
    mc.cost_p90 = _percentile(cost_samples, 90)
    mc.cost_mean = sum(cost_samples) / len(cost_samples)

    # Critical frequency
    mc.critical_frequency = dict(cp_counter)

    # Average schedule
    for nid in node_start_sums:
        if node_count[nid] > 0:
            mc.avg_schedule[nid] = (
                node_start_sums[nid] / node_count[nid],
                node_finish_sums[nid] / node_count[nid],
            )

    # Probability on time
    if target_hours is not None and target_hours > 0:
        on_time = sum(1 for d in duration_samples if d <= target_hours)
        mc.probability_on_time = on_time / len(duration_samples)

    # Cost curve (daily cumulative cost approximation)
    mc.cost_curve = _build_cost_curve(mc, nodes)

    return mc


def _compute_cost(
    result: CpmResult,
    original_nodes: Dict[str, BomNode],
    project_settings: Optional[dict] = None,
) -> float:
    """Compute total project cost for a single Monte Carlo iteration."""
    total = 0.0

    for nid, entry in result.entries.items():
        if entry.node_type not in ('part', 'stage'):
            continue
        node = original_nodes.get(nid)
        if not node:
            continue

        # Direct costs
        total += (node.cost_material or 0)
        total += (node.cost_labor or 0)
        total += (node.cost_overhead or 0)

        # Storage cost (for non-leaf parts that have waiting time)
        if node.storage_cost_per_day and entry.early_start > 0:
            wait_days = entry.early_start / 8.0  # assume 8h per day
            total += node.storage_cost_per_day * wait_days

    # Risk reserve
    if project_settings:
        risk_pct = project_settings.get('risk_reserve_pct', 0) / 100.0
        total *= (1 + risk_pct)

    return total


def _build_cost_curve(
    mc: MonteCarloResult,
    nodes: Dict[str, BomNode],
) -> List[Tuple[int, float]]:
    """Build a daily cumulative cost curve (S-Curve) from the average schedule."""
    if not mc.avg_schedule:
        return []

    # Collect daily costs from the average schedule
    daily_costs: Dict[int, float] = defaultdict(float)
    hours_per_day = 8.0

    for nid, (start_h, finish_h) in mc.avg_schedule.items():
        node = nodes.get(nid)
        if not node or node.node_type not in ('part', 'stage'):
            continue

        daily_cost = (node.cost_material or 0) + (node.cost_labor or 0) + (node.cost_overhead or 0)
        if finish_h > start_h:
            # Distribute cost evenly over the duration
            duration_days = max(1, int((finish_h - start_h) / hours_per_day))
            start_day = int(start_h / hours_per_day)
            cost_per_day = daily_cost / duration_days
            for d in range(start_day, start_day + duration_days):
                daily_costs[d] += cost_per_day

        # Storage cost
        if node.storage_cost_per_day and start_h > 0:
            start_day = int(start_h / hours_per_day)
            daily_costs[start_day] += node.storage_cost_per_day

    if not daily_costs:
        return []

    # Sort by day and compute cumulative
    sorted_days = sorted(daily_costs.keys())
    curve: List[Tuple[int, float]] = []
    cumulative = 0.0
    for day in sorted_days:
        cumulative += daily_costs[day]
        curve.append((day, cumulative))

    return curve
