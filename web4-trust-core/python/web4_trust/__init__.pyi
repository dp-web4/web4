"""Type stubs for web4_trust module."""

from typing import List, Optional, Tuple, Dict, Any

__version__: str

class T3Tensor:
    """T3 Trust Tensor - 6 dimensions measuring trustworthiness."""

    competence: float
    reliability: float
    consistency: float
    witnesses: float
    lineage: float
    alignment: float

    def __init__(
        self,
        competence: float = 0.5,
        reliability: float = 0.5,
        consistency: float = 0.5,
        witnesses: float = 0.5,
        lineage: float = 0.5,
        alignment: float = 0.5,
    ) -> None: ...

    @staticmethod
    def neutral() -> T3Tensor: ...
    def average(self) -> float: ...
    def level(self) -> str: ...
    def update_from_outcome(self, success: bool, magnitude: float) -> None: ...
    def apply_decay(self, days_inactive: float, decay_rate: float) -> bool: ...


class V3Tensor:
    """V3 Value Tensor - 6 dimensions measuring value contribution."""

    energy: float
    contribution: float
    stewardship: float
    network: float
    reputation: float
    temporal: float

    def __init__(
        self,
        energy: float = 0.5,
        contribution: float = 0.5,
        stewardship: float = 0.5,
        network: float = 0.5,
        reputation: float = 0.5,
        temporal: float = 0.5,
    ) -> None: ...

    @staticmethod
    def neutral() -> V3Tensor: ...
    def average(self) -> float: ...


class EntityTrust:
    """Entity trust combining T3 and V3 tensors with witnessing relationships."""

    entity_id: str
    entity_type: str
    entity_name: str
    action_count: int
    success_count: int
    witness_count: int
    witnessed_by: List[str]
    has_witnessed: List[str]

    # T3 fields
    competence: float
    reliability: float
    consistency: float
    witnesses: float
    lineage: float
    alignment: float

    # V3 fields
    energy: float
    contribution: float
    stewardship: float
    network: float
    reputation: float
    temporal: float

    def __init__(self, entity_id: str) -> None: ...
    def t3_average(self) -> float: ...
    def v3_average(self) -> float: ...
    def trust_level(self) -> str: ...
    def update_from_outcome(self, success: bool, magnitude: float) -> None: ...
    def receive_witness(self, witness_id: str, success: bool, magnitude: float) -> None: ...
    def give_witness(self, target_id: str, success: bool, magnitude: float) -> None: ...
    def days_since_last_action(self) -> float: ...
    def apply_decay(self, days_inactive: float, decay_rate: float) -> bool: ...
    def success_rate(self) -> float: ...
    def to_dict(self) -> Dict[str, Any]: ...


class TrustStore:
    """Persistent storage for entity trust."""

    def __init__(self, path: Optional[str] = None) -> None: ...
    def get(self, entity_id: str) -> EntityTrust: ...
    def save(self, trust: EntityTrust) -> None: ...
    def update(self, entity_id: str, success: bool, magnitude: float) -> EntityTrust: ...
    def witness(
        self,
        witness_id: str,
        target_id: str,
        success: bool,
        magnitude: float,
    ) -> Tuple[EntityTrust, EntityTrust]: ...
    def list_entities(self, entity_type: Optional[str] = None) -> List[str]: ...
    def exists(self, entity_id: str) -> bool: ...
    def delete(self, entity_id: str) -> bool: ...
    def get_by_type(self, entity_type: str) -> List[EntityTrust]: ...


def create_memory_store() -> TrustStore:
    """Create an in-memory trust store (for testing)."""
    ...
