"""BOM Repository — loads the Bill of Materials tree from DB into
a flat, calculation-friendly structure.

Each node is a dict with enough info for the CPM / Monte Carlo engine.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class BomNode:
    """Single node in the BOM tree for calculation purposes.

    Phase 1+2: Stage nodes (node_type='stage') are the atomic scheduling
    units.  Parts with stages become connector nodes (duration 0) whose
    children are their Stage BomNodes.  Parts without stages retain legacy
    behaviour (PERT lives on the Part node itself).
    """
    id: str                          # e.g. 'r1', 's3', 'a3', 'p1'
    name: str
    node_type: str                   # 'product' | 'assembly' | 'part' | 'stage'
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    # PERT fields (None = not estimated)
    time_optimistic: Optional[float] = None
    time_most_likely: Optional[float] = None
    time_pessimistic: Optional[float] = None
    # Cost fields
    cost_material: Optional[float] = None
    cost_labor: Optional[float] = None
    cost_overhead: Optional[float] = None
    # Resource
    required_resource_type: Optional[str] = None
    storage_cost_per_day: Optional[float] = None
    # Quantity
    quantity: int = 0
    required_quantity: int = 1
    # Stage-specific: links back to the DB Stage row when node_type='stage'
    stage_id: Optional[int] = None
    part_id: Optional[int] = None     # owning Part DB id (for 'stage' nodes)
    # Backward-compat: for Part nodes that lack child stages, this flag
    # tells CPM to treat the Part as a leaf scheduling unit (legacy mode).
    legacy_part: bool = False

    @property
    def has_pert(self) -> bool:
        return (
            self.time_optimistic is not None
            and self.time_most_likely is not None
            and self.time_pessimistic is not None
        )

    @property
    def direct_cost(self) -> float:
        return (self.cost_material or 0) + (self.cost_labor or 0) + (self.cost_overhead or 0)


def load_bom_tree() -> Dict[str, BomNode]:
    """Load the entire BOM tree from DB into a dict of BomNode.

    Phase 1+2 – Stage-based architecture:
      Each Part that has Stages becomes a *connector* node (duration 0)
      whose children are BomNodes of type 'stage'.  Parts without stages
      fall back to legacy behaviour (PERT lives on the Part node).

    This function must be called within an app context.
    """
    from models import Product, Assembly, Part, Stage

    nodes: Dict[str, BomNode] = {}

    # ── Products ──
    for p in Product.query.all():
        nid = f'p{p.id}'
        children = [f'a{a.id}' for a in Assembly.query.filter_by(product_id=p.id, parent_id=None).all()]
        nodes[nid] = BomNode(
            id=nid, name=p.name, node_type='product',
            children=children,
        )

    # ── Assemblies ──
    for a in Assembly.query.all():
        nid = f'a{a.id}'
        parent = f'p{a.product_id}' if not a.parent_id else f'a{a.parent_id}'
        children = [f'r{part.id}' for part in Part.query.filter_by(assembly_id=a.id).all()]
        children += [f'a{sub.id}' for sub in Assembly.query.filter_by(parent_id=a.id).all()]
        nodes[nid] = BomNode(
            id=nid, name=a.name, node_type='assembly',
            parent_id=parent, children=children,
        )

    # ── Parts + Stages ──
    for r in Part.query.all():
        nid = f'r{r.id}'
        stages = r.stages.order_by(Stage.sort_order).all()
        if stages:
            # Part with stages → connector node (no PERT).
            # Stages are *chained sequentially* via parent_id:
            #   r1 → s1 → s2 → s3  (each stage's parent is the previous)
            stage_chain = [f's{s.id}' for s in stages]
            nodes[nid] = BomNode(
                id=nid, name=r.name, node_type='part',
                parent_id=f'a{r.assembly_id}',
                children=[stage_chain[0]] if stage_chain else [],
                quantity=r.quantity or 0,
                required_quantity=r.required_quantity or 1,
            )
            for idx, s in enumerate(stages):
                sid = f's{s.id}'
                # First stage parent = part; subsequent stages parent = previous stage
                parent_ref = nid if idx == 0 else f's{stages[idx - 1].id}'
                nodes[sid] = BomNode(
                    id=sid, name=s.name, node_type='stage',
                    parent_id=parent_ref,
                    stage_id=s.id,
                    part_id=r.id,
                    time_optimistic=s.time_optimistic,
                    time_most_likely=s.time_most_likely,
                    time_pessimistic=s.time_pessimistic,
                    cost_material=s.estimated_material_cost,
                    cost_labor=s.estimated_labor_cost,
                    cost_overhead=s.estimated_overhead,
                    required_resource_type=s.required_resource_type,
                    storage_cost_per_day=s.storage_cost_per_day,
                    quantity=r.quantity or 0,
                    required_quantity=r.required_quantity or 1,
                )
        else:
            # Part without stages → legacy leaf node (backward compatible)
            nodes[nid] = BomNode(
                id=nid, name=r.name, node_type='part',
                parent_id=f'a{r.assembly_id}',
                time_optimistic=r.time_optimistic,
                time_most_likely=r.time_most_likely,
                time_pessimistic=r.time_pessimistic,
                cost_material=r.cost_material,
                cost_labor=r.cost_labor,
                cost_overhead=r.cost_overhead,
                required_resource_type=r.required_resource_type,
                storage_cost_per_day=r.storage_cost_per_day,
                quantity=r.quantity or 0,
                required_quantity=r.required_quantity or 1,
                legacy_part=True,
            )

    return nodes


def get_critical_parts(nodes: Dict[str, BomNode]) -> List[BomNode]:
    """Return only the leaf parts that have PERT estimates."""
    return [n for n in nodes.values() if n.node_type == 'part' and n.has_pert]


def build_dag(nodes: Dict[str, BomNode]) -> Dict[str, List[str]]:
    """Build adjacency list (parent -> children) for the BOM DAG.

    Only includes nodes that have PERT times (for scheduling).
    """
    dag: Dict[str, List[str]] = {}
    for nid, node in nodes.items():
        if node.has_pert:
            dag[nid] = []
            if node.parent_id and node.parent_id in nodes:
                parent = nodes[node.parent_id]
                if parent.id not in dag:
                    dag[parent.id] = []
                dag[parent.id].append(nid)
    return dag
