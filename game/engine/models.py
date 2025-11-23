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
    # Minimal per-society blockchain state (v0, in-memory only).
    block_interval_seconds: int = 15
    last_block_time: float = 0.0
    pending_events: List[Dict[str, Any]] = field(default_factory=list)
    blocks: List[Dict[str, Any]] = field(default_factory=list)


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
class World:
    """Top-level simulation state for a single world instance."""

    agents: Dict[str, Agent] = field(default_factory=dict)  # keyed by agent_lct
    societies: Dict[str, Society] = field(default_factory=dict)  # keyed by society_lct
    tick: int = 0
    # MRH/LCT context edges observed in this world (v0, in-memory only).
    context_edges: List[ContextEdge] = field(default_factory=list)

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_lct] = agent

    def add_society(self, society: Society) -> None:
        self.societies[society.society_lct] = society

    def get_agent(self, agent_lct: str) -> Optional[Agent]:
        return self.agents.get(agent_lct)

    def get_society(self, society_lct: str) -> Optional[Society]:
        return self.societies.get(society_lct)

    def add_context_edge(
        self,
        *,
        subject: str,
        predicate: str,
        object: str,
        mrh: Optional[Dict[str, str]] = None,
    ) -> None:
        """Append a context edge to the world's MRH/LCT context list."""

        self.context_edges.append(
            ContextEdge(
                subject=subject,
                predicate=predicate,
                object=object,
                mrh=mrh or {},
            )
        )


def make_agent_lct(local_id: str) -> str:
    """Construct a canonical agent LCT for the simulation namespace."""

    return f"lct:web4:agent:{local_id}"


def make_society_lct(local_id: str) -> str:
    """Construct a canonical society LCT for the simulation namespace."""

    return f"lct:web4:society:{local_id}"
