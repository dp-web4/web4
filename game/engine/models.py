from __future__ import annotations

"""Core data models for the Web4 society simulation game (v0).

These models are intentionally minimal and will evolve over time.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Agent:
    """An agentic actor (human or AI) in the simulation."""

    agent_lct: str
    name: str
    # T3-like trust tensor: axes["T3"]["talent"|"training"|"temperament"|"composite"]
    trust_axes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    capabilities: Dict[str, float] = field(default_factory=dict)
    resources: Dict[str, float] = field(default_factory=dict)
    memberships: List[str] = field(default_factory=list)  # list of society LCTs


@dataclass
class Society:
    """A Web4 society with its own LCT, treasury, and members."""

    society_lct: str
    name: str
    treasury: Dict[str, float] = field(default_factory=dict)
    members: List[str] = field(default_factory=list)  # list of agent LCTs
    policies: Dict[str, str] = field(default_factory=dict)
    # Optional T3-like trust tensor at the society level.
    trust_axes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Minimal per-society blockchain state (v0, in-memory only).
    block_interval_seconds: int = 15
    last_block_time: float = 0.0
    pending_events: List[Dict[str, Any]] = field(default_factory=list)
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    # Optional minimal hardware binding metadata (v0).
    hardware_fingerprint: str | None = None


@dataclass
class ContextEdge:
    """A simple MRH/LCT context edge within the simulation world.

    This mirrors the logical structure of an RDF-style triple with an
    optional MRH profile, without depending on any external storage
    backend.
    """

    subject: str
    predicate: str
    object: str
    mrh: Dict[str, str] = field(default_factory=dict)


@dataclass
class LifeRecord:
    life_id: str
    agent_lct: str
    start_tick: int
    end_tick: int
    life_state: str
    termination_reason: str
    t3_history: List[float] = field(default_factory=list)
    atp_history: List[float] = field(default_factory=list)

    @property
    def final_t3(self) -> float:
        return float(self.t3_history[-1]) if self.t3_history else 0.0

    @property
    def final_atp(self) -> float:
        return float(self.atp_history[-1]) if self.atp_history else 0.0


@dataclass
class World:
    """Top-level simulation state for a single world instance."""

    agents: Dict[str, Agent] = field(default_factory=dict)  # keyed by agent_lct
    societies: Dict[str, Society] = field(default_factory=dict)  # keyed by society_lct
    tick: int = 0
    # MRH/LCT context edges observed in this world (v0, in-memory only).
    context_edges: List[ContextEdge] = field(default_factory=list)
    # LCT registry for full V3/T3 metadata (Session #75 cross-society reputation)
    lct_registry: Dict[str, Dict] = field(default_factory=dict)  # lct_id -> lct_dict
    # Federation structure (Session #70+ federation work)
    federation: Dict[str, List[str]] = field(default_factory=dict)  # society_lct -> [connected_society_lcts]

    # Multi-life tracking (v0): per-agent lineage and coarse state machine.
    life_lineage: Dict[str, List[LifeRecord]] = field(default_factory=dict)  # agent_lct -> [LifeRecord, ...]
    life_state: Dict[str, Dict[str, str]] = field(default_factory=dict)  # agent_lct -> {status, life_id}

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_lct] = agent

    def add_society(self, society: Society) -> None:
        self.societies[society.society_lct] = society

    def get_agent(self, agent_lct: str) -> Optional[Agent]:
        return self.agents.get(agent_lct)

    def get_society(self, society_lct: str) -> Optional[Society]:
        return self.societies.get(society_lct)

    def get_agent_lct(self, agent_lct: str) -> Optional[Dict]:
        """Get full LCT dict for agent (Session #75 cross-society reputation)"""
        return self.lct_registry.get(agent_lct)

    def get_society_lct(self, society_lct: str) -> Optional[Dict]:
        """Get full LCT dict for society (Session #75 cross-society reputation)"""
        return self.lct_registry.get(society_lct)

    def add_context_edge(
        self,
        *,
        subject: str,
        predicate: str,
        object: str,
        mrh: Optional[Dict[str, str]] = None,
    ) -> None:
        """Append a context edge to the world's MRH/LCT context list.

        v0 implementation performs simple deduplication: if an identical
        edge (same subject, predicate, object, and mrh) already exists,
        it is not appended again. This keeps participantIn-style
        heartbeat edges from exploding the context list while preserving
        the logical graph structure.
        """

        edge_mrh = mrh or {}

        for existing in self.context_edges:
            if (
                existing.subject == subject
                and existing.predicate == predicate
                and existing.object == object
                and existing.mrh == edge_mrh
            ):
                return

        self.context_edges.append(
            ContextEdge(
                subject=subject,
                predicate=predicate,
                object=object,
                mrh=edge_mrh,
            )
        )


def make_agent_lct(local_id: str) -> str:
    """Construct a canonical agent LCT for the simulation namespace."""

    return f"lct:web4:agent:{local_id}"


def make_society_lct(local_id: str) -> str:
    """Construct a canonical society LCT for the simulation namespace."""

    return f"lct:web4:society:{local_id}"
