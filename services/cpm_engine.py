"""CPM (Critical Path Method) Engine.

Computes schedule for a BOM tree using PERT expected times.

Algorithm:
  1. Topological sort of the BOM DAG
  2. Forward pass: compute Early Start (ES) and Early Finish (EF)
  3. Backward pass: compute Late Start (LS) and Late Finish (LF)
  4. Float = LS - ES (critical nodes have float = 0)
  5. Critical path = chain of zero-float nodes from root to leaves
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from services.pert_calculator import pert_time


@dataclass
class ScheduleEntry:
    """Schedule result for a single BOM node."""
    node_id: str
    name: str
    node_type: str
    duration: float                      # expected time (hours)
    early_start: float = 0.0
    early_finish: float = 0.0
    late_start: float = 0.0
    late_finish: float = 0.0
    total_float: float = 0.0
    is_critical: bool = False
    resource_type: Optional[str] = None


@dataclass
class CpmResult:
    """Full result of a CPM analysis."""
    entries: Dict[str, ScheduleEntry] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    project_duration: float = 0.0        # total project duration in hours
    topological_order: List[str] = field(default_factory=list)

    @property
    def critical_nodes(self) -> List[ScheduleEntry]:
        return [self.entries[nid] for nid in self.critical_path]


class CyclicGraphError(Exception):
    """Raised when the BOM graph contains a cycle."""
    pass


def _topological_sort(adj: Dict[str, List[str]], all_node_ids: set) -> List[str]:
    """Kahn's algorithm for topological sort. Raises CyclicGraphError if cycle exists."""
    # Build in-degree map for ALL nodes (including isolated ones)
    in_degree: Dict[str, int] = defaultdict(int)
    all_nodes = set(all_node_ids)

    for node in all_nodes:
        in_degree.setdefault(node, 0)
    for parent, children in adj.items():
        for child in children:
            in_degree[child] += 1

    queue = deque([n for n in all_nodes if in_degree[n] == 0])
    result: List[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for child in adj.get(node, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(result) != len(all_nodes):
        raise CyclicGraphError(
            f"Cycle detected: sorted {len(result)} of {len(all_nodes)} nodes"
        )
    return result


def run_cpm(
    nodes: Dict[str, 'BomNode'],
    start_time: float = 0.0,
) -> CpmResult:
    """Run the Critical Path Method on a BOM tree.

    Args:
        nodes: Dict of BomNode objects (from bom_repository.load_bom_tree).
        start_time: Project start time in hours (default 0).

    Returns:
        CpmResult with schedule entries, critical path, and project duration.
    """
    from repositories.bom_repository import BomNode

    # ── 1. Build adjacency list (parent -> children) ──
    adj: Dict[str, List[str]] = defaultdict(list)
    for nid, node in nodes.items():
        if node.parent_id and node.parent_id in nodes:
            adj[node.parent_id].append(nid)

    # ── 2. Topological sort ──
    topo = _topological_sort(adj, set(nodes.keys()))

    # ── 3. Compute durations (PERT expected time) ──
    durations: Dict[str, float] = {}
    for nid in topo:
        node = nodes[nid]
        if node.has_pert:
            durations[nid] = pert_time(
                node.time_optimistic, node.time_most_likely, node.time_pessimistic
            )
        else:
            durations[nid] = 0.0  # non-estimated nodes have 0 duration

    # ── 4. Forward pass: ES and EF ──
    es: Dict[str, float] = {}
    ef: Dict[str, float] = {}

    for nid in topo:
        node = nodes[nid]
        # ES = max(EF of all predecessors)
        predecessors = []
        for pid, children in adj.items():
            if nid in children:
                predecessors.append(pid)

        if not predecessors:
            es[nid] = start_time
        else:
            es[nid] = max(ef.get(pid, start_time) for pid in predecessors)

        ef[nid] = es[nid] + durations[nid]

    # Project duration = max EF across all nodes
    project_duration = max(ef.values()) if ef else 0.0

    # ── 5. Backward pass: LF and LS ──
    lf: Dict[str, float] = {}
    ls: Dict[str, float] = {}

    # Reverse topological order
    for nid in reversed(topo):
        node = nodes[nid]
        # Find children
        children = adj.get(nid, [])

        if not children:
            # Leaf node: LF = project duration
            lf[nid] = project_duration
        else:
            # LF = min(LS of all successors)
            lf[nid] = min(ls.get(cid, project_duration) for cid in children)

        ls[nid] = lf[nid] - durations[nid]

    # ── 6. Compute float and identify critical path ──
    entries: Dict[str, ScheduleEntry] = {}
    critical_path: List[str] = []

    for nid in topo:
        node = nodes[nid]
        total_float = ls[nid] - es[nid]
        is_critical = abs(total_float) < 1e-9 and durations[nid] > 0

        entries[nid] = ScheduleEntry(
            node_id=nid,
            name=node.name,
            node_type=node.node_type,
            duration=durations[nid],
            early_start=es[nid],
            early_finish=ef[nid],
            late_start=ls[nid],
            late_finish=lf[nid],
            total_float=total_float,
            is_critical=is_critical,
            resource_type=node.required_resource_type,
        )

    # Build critical path by tracing zero-float nodes from project start
    # Strategy: BFS from root, always follow the child with the latest EF (greedy critical path)
    critical_path = _trace_critical_path(entries, adj, topo, nodes)

    return CpmResult(
        entries=entries,
        critical_path=critical_path,
        project_duration=project_duration,
        topological_order=topo,
    )


def _trace_critical_path(
    entries: Dict[str, ScheduleEntry],
    adj: Dict[str, List[str]],
    topo: List[str],
    nodes: Dict[str, 'BomNode'],
) -> List[str]:
    """Trace the critical path from project start to project end.

    Strategy: Starting from root nodes (no parent or duration=0 connectors),
    follow the child with the highest EF (latest finish).
    """
    # Build reverse adjacency (child -> parents)
    parent_map: Dict[str, List[str]] = defaultdict(list)
    for pid, children in adj.items():
        for cid in children:
            parent_map[cid].append(pid)

    # Find true roots: nodes with no parent in the adjacency
    children_set = set()
    for children in adj.values():
        children_set.update(children)
    all_roots = [nid for nid in topo if nid not in children_set]

    # If no pure roots, pick nodes with highest EF (project end proxies)
    if not all_roots:
        all_roots = topo[:1]  # first in topological order

    best_path: List[str] = []
    for root in all_roots:
        path = _dfs_critical(root, entries, adj, set())
        if len(path) > len(best_path):
            best_path = path

    return best_path


def _dfs_critical(
    nid: str,
    entries: Dict[str, ScheduleEntry],
    adj: Dict[str, List[str]],
    visited: set,
) -> List[str]:
    """DFS to find the longest critical path from a given node.

    Always follows through zero-duration structural nodes to reach
    critical descendants, even when the current node has duration > 0.
    """
    if nid in visited:
        return []
    visited.add(nid)

    path = [nid]
    children = adj.get(nid, [])

    if children:
        # Prefer critical children first
        critical_children = [
            cid for cid in children if entries[cid].is_critical
        ]
        if critical_children:
            best_child = max(critical_children, key=lambda c: entries[c].early_finish)
            path.extend(_dfs_critical(best_child, entries, adj, visited))
        else:
            # No critical child — traverse through zero-duration connectors
            # to discover critical descendants deeper in the graph
            zero_dur_children = [
                cid for cid in children if entries[cid].duration == 0
            ]
            if zero_dur_children:
                best_child = max(zero_dur_children, key=lambda c: entries[c].early_finish)
                path.extend(_dfs_critical(best_child, entries, adj, visited))

    return path
