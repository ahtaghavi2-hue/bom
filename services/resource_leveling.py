"""Resource Leveling Heuristic.

Shifts non-critical tasks within their float window to resolve
resource over-allocation without extending the project duration.

Algorithm (Greedy):
  1. Run CPM to get schedule + float for each task
  2. Sort tasks by resource type
  3. For each time slot, check if resource demand exceeds capacity
  4. If over-allocated, shift a non-critical task later (within its float)
  5. Repeat until no over-allocation or no more moves possible
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from services.cpm_engine import CpmResult, ScheduleEntry
from repositories.bom_repository import BomNode


@dataclass
class ResourceCapacity:
    """Capacity definition for a resource type."""
    resource_type: str
    capacity: int = 1          # max simultaneous tasks
    shift_hours: float = 8.0
    cost_per_hour: float = 0.0


@dataclass
class LeveledSchedule:
    """Result of resource leveling."""
    entries: Dict[str, ScheduleEntry] = field(default_factory=dict)
    resource_utilization: Dict[str, List[Tuple[float, float, int]]] = field(default_factory=dict)
    # resource_type -> list of (start_day, end_day, count) for overload periods
    over_allocations_resolved: int = 0
    project_duration: float = 0.0  # may be same or slightly longer than original

    def to_dict(self) -> dict:
        return {
            'entries': {
                k: {
                    'node_id': v.node_id, 'name': v.name,
                    'early_start': v.early_start, 'early_finish': v.early_finish,
                    'late_start': v.late_start, 'late_finish': v.late_finish,
                    'duration': v.duration, 'total_float': v.total_float,
                    'is_critical': v.is_critical, 'resource_type': v.resource_type,
                }
                for k, v in self.entries.items()
            },
            'over_allocations_resolved': self.over_allocations_resolved,
            'project_duration': self.project_duration,
        }


def level_resources(
    cpm_result: CpmResult,
    resources: Dict[str, ResourceCapacity],
    nodes: Dict[str, BomNode],
    hours_per_day: float = 8.0,
) -> LeveledSchedule:
    """Apply greedy resource leveling to a CPM schedule.

    Args:
        cpm_result: Result from run_cpm().
        resources: Dict of resource_type -> ResourceCapacity.
        nodes: BOM tree for reference.
        hours_per_day: Hours per working day.

    Returns:
        LeveledSchedule with adjusted start/finish times.
    """
    # Deep copy entries
    entries: Dict[str, ScheduleEntry] = {}
    for nid, entry in cpm_result.entries.items():
        entries[nid] = ScheduleEntry(
            node_id=entry.node_id, name=entry.name, node_type=entry.node_type,
            duration=entry.duration, early_start=entry.early_start,
            early_finish=entry.early_finish, late_start=entry.late_start,
            late_finish=entry.late_finish, total_float=entry.total_float,
            is_critical=entry.is_critical, resource_type=entry.resource_type,
        )

    # Group tasks by resource type
    resource_tasks: Dict[str, List[str]] = defaultdict(list)
    for nid, entry in entries.items():
        if entry.resource_type and entry.duration > 0:
            resource_tasks[entry.resource_type].append(nid)

    over_allocations_resolved = 0

    # For each resource type, check and fix over-allocation
    for rtype, task_ids in resource_tasks.items():
        cap = resources.get(rtype)
        if not cap:
            continue

        max_capacity = cap.capacity

        # Build a timeline of task assignments
        # Try to resolve over-allocation by shifting non-critical tasks
        for _ in range(100):  # max iterations to prevent infinite loop
            # Find over-allocated time slots
            daily_load: Dict[int, int] = defaultdict(int)
            task_days: Dict[str, List[int]] = {}

            for nid in task_ids:
                entry = entries[nid]
                start_day = int(entry.early_start / hours_per_day)
                duration_days = max(1, int(entry.duration / hours_per_day))
                end_day = start_day + duration_days
                task_days[nid] = list(range(start_day, end_day))
                for d in task_days[nid]:
                    daily_load[d] += 1

            # Find over-loaded days
            overloaded_days = [d for d, load in daily_load.items() if load > max_capacity]
            if not overloaded_days:
                break

            # Find a task on an overloaded day that can be shifted
            shifted = False
            for day in sorted(overloaded_days):
                tasks_on_day = [nid for nid in task_ids if day in task_days.get(nid, [])]

                # Priority 1: shift non-critical tasks within their float
                non_critical = [
                    nid for nid in tasks_on_day
                    if not entries[nid].is_critical and entries[nid].total_float > 0
                ]
                if non_critical:
                    task_to_shift = max(non_critical, key=lambda n: entries[n].total_float)
                    entry = entries[task_to_shift]
                    shift_hours = hours_per_day
                    new_start = entry.early_start + shift_hours
                    new_finish = entry.early_finish + shift_hours
                    if new_finish <= entry.late_finish:
                        entry.early_start = new_start
                        entry.early_finish = new_finish
                        over_allocations_resolved += 1
                        shifted = True
                        break

                # Priority 2: shift any task (even critical) — extends project
                if tasks_on_day:
                    # Pick the shortest task (least impact on project duration)
                    task_to_shift = min(tasks_on_day, key=lambda n: entries[n].duration)
                    entry = entries[task_to_shift]
                    entry.early_start += hours_per_day
                    entry.early_finish += hours_per_day
                    entry.total_float = entry.late_start - entry.early_start
                    entry.is_critical = abs(entry.total_float) < 1e-9 and entry.duration > 0
                    over_allocations_resolved += 1
                    shifted = True
                    break

            if not shifted:
                break  # can't resolve more

    # Recompute project duration
    project_duration = max(e.early_finish for e in entries.values()) if entries else 0.0

    return LeveledSchedule(
        entries=entries,
        over_allocations_resolved=over_allocations_resolved,
        project_duration=project_duration,
    )
