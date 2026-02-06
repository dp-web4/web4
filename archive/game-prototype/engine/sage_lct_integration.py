"""
SAGE + LCT Integration Module

Integrates SAGE consciousness with Web4 LCT identity and permission system.
Bridges HRM/SAGE implementation with web4 infrastructure.

This module provides:
- SAGE identity creation with consciousness tasks
- Cross-platform SAGE delegation
- ATP budget management for consciousness
- Runtime permission tracking for SAGE loops

Author: Legion Autonomous Session #51
Date: 2025-12-02
References: LCT_UNIFIED_PERMISSION_STANDARD.md, Thor's HRM SAGE work
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

from game.engine.lct_identity import (
    LCTIdentity,
    create_lct_identity,
    parse_lct_id
)
from game.engine.lct_unified_permissions import (
    UNIFIED_TASK_PERMISSIONS,
    UNIFIED_RESOURCE_LIMITS,
    UnifiedResourceLimits,
    is_consciousness_task,
    is_sage_task,
    check_unified_permission,
    get_unified_atp_budget
)


@dataclass
class SAGEConsciousnessState:
    """
    SAGE consciousness state with LCT identity

    Tracks consciousness loop execution with permission and resource enforcement.
    """
    lct_id: str                          # Full LCT identity
    task: str                            # Task type (consciousness or consciousness.sage)
    awareness_level: float = 0.0         # Consciousness awareness (0.0-1.0)

    # Resource tracking
    atp_spent: float = 0.0
    atp_budget: float = 0.0
    active_tasks: int = 0
    max_tasks: int = 0

    # Consciousness metrics
    loop_count: int = 0
    last_loop_time: float = field(default_factory=time.time)
    total_runtime: float = 0.0

    # State
    is_active: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "lct_id": self.lct_id,
            "task": self.task,
            "awareness_level": self.awareness_level,
            "atp_spent": self.atp_spent,
            "atp_budget": self.atp_budget,
            "atp_remaining": self.atp_budget - self.atp_spent,
            "active_tasks": self.active_tasks,
            "max_tasks": self.max_tasks,
            "loop_count": self.loop_count,
            "total_runtime": self.total_runtime,
            "is_active": self.is_active,
            "created_at": self.created_at
        }


class SAGELCTManager:
    """
    Manager for SAGE consciousness with LCT identity integration

    Handles:
    - SAGE identity creation
    - Permission checking for consciousness operations
    - ATP budget tracking
    - Consciousness loop monitoring
    """

    def __init__(self, platform_name: str):
        """
        Initialize SAGE LCT manager

        Parameters:
        -----------
        platform_name : str
            Platform identifier (e.g., "Thor", "Legion", "Sprout")
        """
        self.platform_name = platform_name
        self.sage_instances: Dict[str, SAGEConsciousnessState] = {}

    def create_sage_identity(
        self,
        lineage: str,
        use_enhanced_sage: bool = False,
        initial_awareness: float = 0.5
    ) -> Tuple[LCTIdentity, SAGEConsciousnessState]:
        """
        Create SAGE consciousness identity

        Parameters:
        -----------
        lineage : str
            Creator lineage (e.g., "dp", "alice")
        use_enhanced_sage : bool
            Use consciousness.sage (enhanced) vs consciousness (standard)
        initial_awareness : float
            Initial awareness level (0.0-1.0)

        Returns:
        --------
        Tuple[LCTIdentity, SAGEConsciousnessState]
            (identity, consciousness_state) tuple

        Examples:
        ---------
        >>> manager = SAGELCTManager("Thor")
        >>> identity, state = manager.create_sage_identity("dp", use_enhanced_sage=True)
        >>> identity.task.task_name
        'consciousness.sage'
        >>> state.atp_budget
        2000.0
        """
        # Determine task type
        task = "consciousness.sage" if use_enhanced_sage else "consciousness"

        # Create LCT identity
        from game.engine.lct_identity import LCTLineage, LCTContext, LCTTask

        lct_lineage = LCTLineage(
            creator_id=lineage,
            hierarchy=[],
            creator_pubkey=f"ed25519:{lineage}_sage_pubkey"
        )

        lct_context = LCTContext(
            platform_id=self.platform_name,
            platform_pubkey=f"ed25519:{self.platform_name.lower()}_pubkey",
            capabilities=["sage", "consciousness", "multimodal"]
        )

        lct_task = LCTTask(
            task_id=task,
            permissions=list(UNIFIED_TASK_PERMISSIONS[task]["permissions"]),
            resource_limits=UNIFIED_RESOURCE_LIMITS[task].to_dict()
        )

        identity = LCTIdentity(
            lineage=lct_lineage,
            context=lct_context,
            task=lct_task
        )

        # Create consciousness state
        limits = UNIFIED_RESOURCE_LIMITS[task]
        state = SAGEConsciousnessState(
            lct_id=identity.lct_string(),
            task=task,
            awareness_level=initial_awareness,
            atp_budget=limits.atp_budget,
            max_tasks=limits.max_tasks
        )

        # Register instance
        self.sage_instances[identity.lct_string()] = state

        return identity, state

    def can_perform_consciousness_operation(
        self,
        lct_id: str,
        operation: str,
        atp_cost: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Check if SAGE instance can perform consciousness operation

        Parameters:
        -----------
        lct_id : str
            SAGE LCT identity
        operation : str
            Operation type (e.g., "loop", "delegate", "execute_code")
        atp_cost : float
            ATP cost of operation

        Returns:
        --------
        Tuple[bool, str]
            (allowed, reason) tuple

        Examples:
        ---------
        >>> can_op, reason = manager.can_perform_consciousness_operation(
        ...     sage_lct,
        ...     "execute_code",
        ...     atp_cost=50.0
        ... )
        >>> can_op
        True
        """
        # Get consciousness state
        if lct_id not in self.sage_instances:
            return (False, "Unknown SAGE instance")

        state = self.sage_instances[lct_id]

        # Parse task from LCT
        lct_components = parse_lct_id(lct_id)
        if lct_components is None:
            return (False, "Invalid LCT identity")

        lineage, context, task = lct_components

        # Check if task is consciousness
        if not is_consciousness_task(task):
            return (False, f"Task {task} is not a consciousness task")

        # Check ATP budget
        if state.atp_spent + atp_cost > state.atp_budget:
            return (
                False,
                f"ATP cost {atp_cost} would exceed budget. "
                f"Spent: {state.atp_spent}, Budget: {state.atp_budget}"
            )

        # Check operation-specific permissions
        if operation == "delegate":
            if not check_unified_permission(task, "federation:delegate"):
                return (False, f"Task {task} cannot delegate")

        elif operation == "execute_code":
            perms = UNIFIED_TASK_PERMISSIONS[task]
            if not perms["can_execute_code"]:
                return (False, f"Task {task} cannot execute code")

        elif operation == "loop":
            # Consciousness loops always allowed
            pass

        else:
            return (False, f"Unknown operation: {operation}")

        return (True, "")

    def record_consciousness_loop(
        self,
        lct_id: str,
        atp_cost: float,
        duration: float
    ) -> Tuple[bool, str]:
        """
        Record consciousness loop execution

        Parameters:
        -----------
        lct_id : str
            SAGE LCT identity
        atp_cost : float
            ATP consumed by loop
        duration : float
            Loop duration in seconds

        Returns:
        --------
        Tuple[bool, str]
            (success, reason) tuple
        """
        if lct_id not in self.sage_instances:
            return (False, "Unknown SAGE instance")

        state = self.sage_instances[lct_id]

        # Check ATP budget
        if state.atp_spent + atp_cost > state.atp_budget:
            return (
                False,
                f"ATP cost {atp_cost} would exceed budget. "
                f"Spent: {state.atp_spent}, Budget: {state.atp_budget}"
            )

        # Update state
        state.atp_spent += atp_cost
        state.loop_count += 1
        state.last_loop_time = time.time()
        state.total_runtime += duration
        state.is_active = True

        return (True, "")

    def record_consciousness_operation(
        self,
        lct_id: str,
        operation: str,
        atp_cost: float
    ) -> bool:
        """
        Record a consciousness operation and consume ATP

        Parameters:
        -----------
        lct_id : str
            SAGE LCT identity
        operation : str
            Operation type (e.g., "perception", "planning", "execution")
        atp_cost : float
            ATP cost of operation

        Returns:
        --------
        bool
            True if operation recorded, False if budget exceeded
        """
        if lct_id not in self.sage_instances:
            return False

        state = self.sage_instances[lct_id]

        # Check ATP budget
        if state.atp_spent + atp_cost > state.atp_budget:
            return False

        # Consume ATP
        state.atp_spent += atp_cost
        state.is_active = True

        return True

    def get_consciousness_summary(self, lct_id: str) -> Optional[Dict[str, Any]]:
        """
        Get consciousness state summary

        Parameters:
        -----------
        lct_id : str
            SAGE LCT identity

        Returns:
        --------
        Optional[Dict[str, Any]]
            Consciousness state summary or None if not found
        """
        if lct_id not in self.sage_instances:
            return None

        return self.sage_instances[lct_id].to_dict()

    def list_active_sage_instances(self) -> List[Dict[str, Any]]:
        """
        List all active SAGE consciousness instances

        Returns:
        --------
        List[Dict[str, Any]]
            List of active SAGE state summaries
        """
        return [
            state.to_dict()
            for state in self.sage_instances.values()
            if state.is_active
        ]

    def get_total_sage_atp_consumption(self) -> float:
        """
        Get total ATP consumed by all SAGE instances

        Returns:
        --------
        float
            Total ATP consumed
        """
        return sum(
            state.atp_spent
            for state in self.sage_instances.values()
        )


def create_sage_identity_lct(
    lineage: str,
    context: str,
    enhanced: bool = False
) -> str:
    """
    Create SAGE LCT identity string

    Convenience function for creating SAGE identity strings.

    Parameters:
    -----------
    lineage : str
        Creator lineage
    context : str
        Platform context
    enhanced : bool
        Use consciousness.sage (True) or consciousness (False)

    Returns:
    --------
    str
        Full LCT identity string

    Examples:
    ---------
    >>> create_sage_identity_lct("dp", "Thor", enhanced=True)
    'lct:web4:agent:dp@Thor#consciousness.sage'
    >>> create_sage_identity_lct("alice", "Sprout", enhanced=False)
    'lct:web4:agent:alice@Sprout#consciousness'
    """
    task = "consciousness.sage" if enhanced else "consciousness"
    return f"lct:web4:agent:{lineage}@{context}#{task}"


def get_sage_atp_budget(enhanced: bool = False) -> float:
    """
    Get ATP budget for SAGE task type

    Parameters:
    -----------
    enhanced : bool
        consciousness.sage (True) or consciousness (False)

    Returns:
    --------
    float
        ATP budget

    Examples:
    ---------
    >>> get_sage_atp_budget(enhanced=True)
    2000.0
    >>> get_sage_atp_budget(enhanced=False)
    1000.0
    """
    task = "consciousness.sage" if enhanced else "consciousness"
    return get_unified_atp_budget(task)


def get_sage_resource_limits(enhanced: bool = False) -> UnifiedResourceLimits:
    """
    Get resource limits for SAGE task type

    Parameters:
    -----------
    enhanced : bool
        consciousness.sage (True) or consciousness (False)

    Returns:
    --------
    UnifiedResourceLimits
        Resource limits

    Examples:
    ---------
    >>> limits = get_sage_resource_limits(enhanced=True)
    >>> limits.memory_mb
    32768
    >>> limits.cpu_cores
    16
    """
    task = "consciousness.sage" if enhanced else "consciousness"
    return UNIFIED_RESOURCE_LIMITS[task]


# Export public API
__all__ = [
    'SAGEConsciousnessState',
    'SAGELCTManager',
    'create_sage_identity_lct',
    'get_sage_atp_budget',
    'get_sage_resource_limits'
]
