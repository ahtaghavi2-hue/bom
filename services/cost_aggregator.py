"""Cost Aggregation Engine.

Computes total project cost from a CPM schedule, combining:
  - Direct costs: material + labor + overhead per part
  - Storage costs: daily_rate × wait_days for each part
  - Resource costs: hourly_rate × duration for assigned resources
  - Risk reserve: configurable percentage on top
"""

from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

from services.cpm_engine import CpmResult, ScheduleEntry
from repositories.bom_repository import BomNode
from services.resource_leveling import ResourceCapacity


@dataclass
class CostBreakdown:
    """Detailed cost breakdown of the project."""
    # Direct costs (sum across all parts)
    total_material: float = 0.0
    total_labor: float = 0.0
    total_overhead: float = 0.0
    total_direct: float = 0.0
    # Storage costs
    total_storage: float = 0.0
    # Resource operating costs
    total_resource_ops: float = 0.0
    # Subtotals
    subtotal: float = 0.0
    # Risk
    risk_reserve_pct: float = 0.0
    risk_reserve_amount: float = 0.0
    # Grand total
    grand_total: float = 0.0
    # Penalty estimate
    daily_penalty: float = 0.0
    estimated_delay_days: float = 0.0
    estimated_penalty: float = 0.0
    # Per-part breakdown
    part_costs: Dict[str, dict] = None

    def __post_init__(self):
        if self.part_costs is None:
            self.part_costs = {}

    def to_dict(self) -> dict:
        return {
            'total_material': self.total_material,
            'total_labor': self.total_labor,
            'total_overhead': self.total_overhead,
            'total_direct': self.total_direct,
            'total_storage': self.total_storage,
            'total_resource_ops': self.total_resource_ops,
            'subtotal': self.subtotal,
            'risk_reserve_pct': self.risk_reserve_pct,
            'risk_reserve_amount': self.risk_reserve_amount,
            'grand_total': self.grand_total,
            'daily_penalty': self.daily_penalty,
            'estimated_delay_days': self.estimated_delay_days,
            'estimated_penalty': self.estimated_penalty,
        }


def aggregate_costs(
    cpm_result: CpmResult,
    nodes: Dict[str, BomNode],
    resources: Optional[Dict[str, ResourceCapacity]] = None,
    project_settings: Optional[dict] = None,
    hours_per_day: float = 8.0,
) -> CostBreakdown:
    """Compute full cost breakdown from a CPM schedule.

    Args:
        cpm_result: CPM schedule result.
        nodes: BOM tree.
        resources: Resource definitions for operating cost calculation.
        project_settings: Dict with 'daily_penalty', 'risk_reserve_pct', 'total_budget',
                          'target_delivery_date'.
        hours_per_day: Hours per working day.
    """
    breakdown = CostBreakdown()
    settings = project_settings or {}
    breakdown.daily_penalty = settings.get('daily_penalty', 0)
    breakdown.risk_reserve_pct = settings.get('risk_reserve_pct', 0)

    hours_per_day_val = hours_per_day  # local alias

    for nid, entry in cpm_result.entries.items():
        if entry.node_type not in ('part', 'stage'):
            continue
        node = nodes.get(nid)
        if not node:
            continue

        # Direct costs
        mat = node.cost_material or 0
        lab = node.cost_labor or 0
        ovh = node.cost_overhead or 0
        breakdown.total_material += mat
        breakdown.total_labor += lab
        breakdown.total_overhead += ovh

        # Storage cost (for parts that wait before starting)
        if node.storage_cost_per_day and entry.early_start > 0:
            wait_days = entry.early_start / hours_per_day_val
            storage = node.storage_cost_per_day * wait_days
            breakdown.total_storage += storage

        # Store per-part breakdown
        breakdown.part_costs[nid] = {
            'name': node.name,
            'material': mat,
            'labor': lab,
            'overhead': ovh,
            'direct': mat + lab + ovh,
            'storage': node.storage_cost_per_day * (entry.early_start / hours_per_day_val) if node.storage_cost_per_day and entry.early_start > 0 else 0,
        }

    # Resource operating costs
    if resources:
        for nid, entry in cpm_result.entries.items():
            if entry.resource_type and entry.duration > 0:
                cap = resources.get(entry.resource_type)
                if cap:
                    breakdown.total_resource_ops += cap.cost_per_hour * entry.duration

    # Subtotals
    breakdown.total_direct = breakdown.total_material + breakdown.total_labor + breakdown.total_overhead
    breakdown.subtotal = breakdown.total_direct + breakdown.total_storage + breakdown.total_resource_ops

    # Risk reserve
    breakdown.risk_reserve_amount = breakdown.subtotal * (breakdown.risk_reserve_pct / 100.0)
    breakdown.grand_total = breakdown.subtotal + breakdown.risk_reserve_amount

    # Penalty estimate
    if breakdown.daily_penalty > 0:
        # Compare project duration with target delivery
        target_hours = settings.get('target_delivery_hours')
        if target_hours and target_hours > 0:
            delay_hours = max(0, cpm_result.project_duration - target_hours)
            breakdown.estimated_delay_days = delay_hours / hours_per_day_val
            breakdown.estimated_penalty = breakdown.estimated_delay_days * breakdown.daily_penalty
            breakdown.grand_total += breakdown.estimated_penalty

    return breakdown
