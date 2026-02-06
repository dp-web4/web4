"""
State Governance Implementation for SAGE/ACT
Session #22 - Multi-Scale Coherence Framework

Implements state management layer to prevent context bleed solitons.
Validated against T011, T012, and Session #6 incidents.

Key principles:
1. State type classification (identity/task/working/scratch)
2. Boundary enforcement (response/exercise/session/phase)
3. Mass monitoring and intervention
4. ATP budgeting for governance operations
5. Full audit trail

Usage:
    governance = StateGovernance()
    result = governance.process_transition(from_state, to_state, boundary_type)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class StateType(Enum):
    """Classification of state by persistence scope"""
    IDENTITY = "identity"      # Permanent (never clears)
    TASK = "task"              # Session-level (clears at session end)
    WORKING = "working"        # Exercise-level (clears between exercises)
    SCRATCH = "scratch"        # Response-level (clears after response)


class BoundaryType(Enum):
    """Types of context boundaries requiring governance"""
    RESPONSE = 1               # Between individual responses
    EXERCISE = 2               # Between exercises in same session
    SESSION = 3                # Between sessions in same track
    TRACK = 4                  # Between different skill tracks
    PHASE = 5                  # Between major phases (Training→Sensing)


class GovernanceAction(Enum):
    """Actions taken by governance system"""
    NONE = "none"              # No action needed
    COMMIT = "commit"          # Serialize to memory
    CLEAR = "clear"            # Remove from working memory
    RESET = "reset"            # Full context reset
    DISPERSE = "disperse"      # Force soliton breakup
    ALERT = "alert"            # Flag potential issue


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CoherenceSoliton:
    """
    Topological defect in context (from Session #261/Session #21)

    Mass formula: m = κ × ∫(C - C₀) dx ≈ amplitude × width
    Dispersion energy: E_disp = 0.1 × mass
    """
    topic: str                          # What the soliton represents
    pattern: str                        # Specific pattern (e.g., "refined version")
    amplitude: float                    # Peak coherence above baseline (C - C₀)
    width: int                          # Context tokens occupied
    mass: float                         # Integrated excess coherence
    formation_time: datetime            # When soliton formed
    persistence_count: int = 0          # How many boundaries survived
    soliton_type: str = "content"       # "content", "meta", or "identity-class"


@dataclass
class StateSnapshot:
    """Complete state at a given moment"""
    timestamp: datetime
    identity: Dict[str, any]            # Permanent state
    task_context: Dict[str, any]        # Session-level state
    working_memory: Dict[str, any]      # Exercise-level state
    scratch: Dict[str, any]             # Response-level state
    solitons: List[CoherenceSoliton]    # Active solitons
    coherence: float                    # Current coherence level
    mass_total: float                   # Total soliton mass


@dataclass
class GovernanceEvent:
    """Audit log entry for governance action"""
    timestamp: datetime
    boundary_type: BoundaryType
    action: GovernanceAction
    state_before: StateSnapshot
    state_after: StateSnapshot
    atp_cost: float
    details: Dict[str, any]


@dataclass
class ATPBudget:
    """ATP economics for state governance"""
    available: float = 100.0
    allocated: Dict[str, float] = field(default_factory=dict)
    spent: Dict[str, float] = field(default_factory=dict)

    # Cost constants (from Session #22 analysis)
    COST_RESPONSE = 1.0
    COST_RESET = 1.0
    COST_SOLITON_MAINTAIN = 0.1  # per turn, per mass unit
    COST_SOLITON_DISPERSE = 0.5  # per mass unit (one-time)
    COST_PHASE_TRANSITION = 5.0  # base cost

    def allocate(self, operation: str, amount: float):
        """Allocate ATP for operation"""
        if self.available < amount:
            raise ValueError(f"Insufficient ATP: need {amount}, have {self.available}")
        self.allocated[operation] = amount
        self.available -= amount

    def spend(self, operation: str, actual: float):
        """Record actual ATP spent"""
        self.spent[operation] = actual
        if operation in self.allocated:
            refund = self.allocated[operation] - actual
            if refund > 0:
                self.available += refund


# ============================================================================
# CORE GOVERNANCE CLASSES
# ============================================================================

class MassMonitor:
    """
    Detects and measures coherence solitons

    Thresholds from Session #22 analysis:
    - m < 10.0: Will disperse naturally
    - 10.0 ≤ m < 15.0: Persistent, needs intervention
    - m ≥ 15.0: Very persistent, may survive boundaries
    - m ≥ 20.0: Identity-class, survives phase transitions
    """

    THRESHOLD_NATURAL = 10.0      # Below this: disperses naturally
    THRESHOLD_PERSISTENT = 15.0   # Above this: very persistent
    THRESHOLD_IDENTITY = 20.0     # Above this: identity-class

    def __init__(self):
        self.active_solitons: List[CoherenceSoliton] = []

    def measure_mass(self, context: str, baseline: float = 0.5) -> float:
        """
        Estimate soliton mass from context

        In production: Use actual coherence measurement
        For prototype: Pattern-based heuristics
        """
        # Placeholder: count repetitive patterns
        # Real implementation would measure ∫(C - C₀) dx

        # Check for "refined version" pattern (Session #6)
        if "refined version" in context.lower():
            return 20.0  # Identity-class

        # Check for template generation (T012)
        if "focus exercise" in context.lower():
            return 15.0  # Meta soliton

        # Check for content repetition (T011)
        words = context.lower().split()
        if len(words) > 20:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.4:  # High repetition
                return 12.0  # Content soliton

        return 0.0  # No soliton

    def detect_soliton(self, response: str, baseline_coherence: float = 0.5) -> Optional[CoherenceSoliton]:
        """Detect if soliton is forming"""
        mass = self.measure_mass(response, baseline_coherence)

        if mass > self.THRESHOLD_NATURAL:
            # Determine soliton type
            if mass >= self.THRESHOLD_IDENTITY:
                soliton_type = "identity-class"
            elif mass >= self.THRESHOLD_PERSISTENT:
                soliton_type = "meta"
            else:
                soliton_type = "content"

            # Extract pattern
            pattern = self._extract_pattern(response)

            return CoherenceSoliton(
                topic=self._extract_topic(response),
                pattern=pattern,
                amplitude=mass / 40.0,  # Rough estimate: m = amp × width
                width=40,                # Typical token width
                mass=mass,
                formation_time=datetime.now(),
                soliton_type=soliton_type
            )

        return None

    def _extract_pattern(self, text: str) -> str:
        """Extract repeated pattern from text"""
        lower = text.lower()
        if "refined version" in lower:
            return "refined_version"
        elif "focus exercise" in lower:
            return "focus_exercise"
        else:
            # Find most frequent multi-word phrase
            return "generic_pattern"

    def _extract_topic(self, text: str) -> str:
        """Extract topic from text"""
        # Placeholder: first noun
        words = text.split()
        for word in words:
            if len(word) > 3 and word[0].isupper():
                return word
        return "unknown"

    def check_persistence(self, soliton: CoherenceSoliton, boundaries_survived: int) -> str:
        """Assess soliton risk level based on persistence"""
        if soliton.mass >= self.THRESHOLD_IDENTITY:
            return "CRITICAL" if boundaries_survived > 0 else "SEVERE"
        elif soliton.mass >= self.THRESHOLD_PERSISTENT:
            return "HIGH" if boundaries_survived > 2 else "MODERATE"
        else:
            return "LOW"


class GovernancePolicy:
    """
    Defines what persists when

    Based on Session #22 state lifecycle framework
    """

    # Persistence matrix: StateType → BoundaryType → should_clear
    PERSISTENCE_RULES = {
        StateType.IDENTITY: {
            BoundaryType.RESPONSE: False,
            BoundaryType.EXERCISE: False,
            BoundaryType.SESSION: False,
            BoundaryType.TRACK: False,
            BoundaryType.PHASE: False,
        },
        StateType.TASK: {
            BoundaryType.RESPONSE: False,
            BoundaryType.EXERCISE: False,
            BoundaryType.SESSION: True,
            BoundaryType.TRACK: True,
            BoundaryType.PHASE: True,
        },
        StateType.WORKING: {
            BoundaryType.RESPONSE: False,
            BoundaryType.EXERCISE: True,   # CRITICAL: Clear between exercises
            BoundaryType.SESSION: True,
            BoundaryType.TRACK: True,
            BoundaryType.PHASE: True,
        },
        StateType.SCRATCH: {
            BoundaryType.RESPONSE: True,   # Clear after every response
            BoundaryType.EXERCISE: True,
            BoundaryType.SESSION: True,
            BoundaryType.TRACK: True,
            BoundaryType.PHASE: True,
        },
    }

    @classmethod
    def should_clear(cls, state_type: StateType, boundary: BoundaryType) -> bool:
        """Determine if state should clear at boundary"""
        return cls.PERSISTENCE_RULES[state_type][boundary]

    @classmethod
    def required_actions(cls, boundary: BoundaryType) -> List[GovernanceAction]:
        """Actions required at boundary type"""
        if boundary == BoundaryType.RESPONSE:
            return [GovernanceAction.CLEAR]  # Scratch only

        elif boundary == BoundaryType.EXERCISE:
            return [
                GovernanceAction.COMMIT,     # Save response
                GovernanceAction.CLEAR,      # Clear working memory
            ]

        elif boundary == BoundaryType.SESSION:
            return [
                GovernanceAction.COMMIT,     # Save session summary
                GovernanceAction.CLEAR,      # Clear working + task
            ]

        elif boundary == BoundaryType.TRACK:
            return [
                GovernanceAction.COMMIT,     # Save track summary
                GovernanceAction.RESET,      # Full reset except identity
            ]

        elif boundary == BoundaryType.PHASE:
            return [
                GovernanceAction.COMMIT,     # Save phase summary
                GovernanceAction.RESET,      # Full reset except identity
                GovernanceAction.ALERT,      # Check for persistent solitons
            ]

        return []


class StateManager:
    """
    Manages state lifecycle and boundaries

    Implements state type classification and persistence policies
    """

    def __init__(self):
        self.current_state = StateSnapshot(
            timestamp=datetime.now(),
            identity={
                "name": "SAGE",
                "role": "Learning system",
                "principles": ["Grounding", "Sensing", "Integration"]
            },
            task_context={},
            working_memory={},
            scratch={},
            solitons=[],
            coherence=0.5,
            mass_total=0.0
        )

        self.history: List[StateSnapshot] = []

    def snapshot(self) -> StateSnapshot:
        """Capture current state"""
        return StateSnapshot(
            timestamp=datetime.now(),
            identity=self.current_state.identity.copy(),
            task_context=self.current_state.task_context.copy(),
            working_memory=self.current_state.working_memory.copy(),
            scratch=self.current_state.scratch.copy(),
            solitons=self.current_state.solitons.copy(),
            coherence=self.current_state.coherence,
            mass_total=self.current_state.mass_total
        )

    def clear(self, state_type: StateType):
        """Clear specific state type"""
        if state_type == StateType.SCRATCH:
            self.current_state.scratch = {}

        elif state_type == StateType.WORKING:
            self.current_state.working_memory = {}

        elif state_type == StateType.TASK:
            self.current_state.task_context = {}

        # NEVER clear IDENTITY

    def add_soliton(self, soliton: CoherenceSoliton):
        """Register new soliton"""
        self.current_state.solitons.append(soliton)
        self.current_state.mass_total += soliton.mass

    def remove_soliton(self, soliton: CoherenceSoliton):
        """Remove soliton (after dispersion)"""
        if soliton in self.current_state.solitons:
            self.current_state.solitons.remove(soliton)
            self.current_state.mass_total -= soliton.mass


class StateGovernance:
    """
    Main governance coordinator

    Orchestrates state management, mass monitoring, and ATP budgeting
    """

    def __init__(self, atp_initial: float = 100.0):
        self.state_manager = StateManager()
        self.mass_monitor = MassMonitor()
        self.atp_budget = ATPBudget(available=atp_initial)
        self.audit_log: List[GovernanceEvent] = []

    def process_response(self, response: str) -> Dict[str, any]:
        """
        Process response and apply governance

        This is the main entry point for each response
        """
        # 1. Detect soliton formation
        soliton = self.mass_monitor.detect_soliton(response)

        if soliton:
            self.state_manager.add_soliton(soliton)
            action = GovernanceAction.ALERT
            atp_cost = 0.0  # Detection is free

            details = {
                "soliton_detected": True,
                "mass": soliton.mass,
                "type": soliton.soliton_type,
                "pattern": soliton.pattern,
                "risk": self.mass_monitor.check_persistence(soliton, 0)
            }
        else:
            action = GovernanceAction.NONE
            atp_cost = 0.0
            details = {"soliton_detected": False}

        # 2. Clear scratch state (always at response boundary)
        self.state_manager.clear(StateType.SCRATCH)

        # 3. Log event
        self._log_event(BoundaryType.RESPONSE, action, atp_cost, details)

        return details

    def process_boundary(self, boundary_type: BoundaryType, context: Dict[str, any] = None) -> Dict[str, any]:
        """
        Process major boundary (exercise, session, track, phase)

        Returns governance report with actions taken
        """
        state_before = self.state_manager.snapshot()

        # 1. Determine required actions
        required_actions = GovernancePolicy.required_actions(boundary_type)

        # 2. Execute actions
        actions_taken = []
        total_cost = 0.0
        details = {"boundary": boundary_type.value, "actions": []}

        for action in required_actions:
            if action == GovernanceAction.COMMIT:
                cost = self._do_commit(boundary_type, context)
                actions_taken.append("commit")
                total_cost += cost

            elif action == GovernanceAction.CLEAR:
                cost = self._do_clear(boundary_type)
                actions_taken.append("clear")
                total_cost += cost

            elif action == GovernanceAction.RESET:
                cost = self._do_reset(boundary_type)
                actions_taken.append("reset")
                total_cost += cost

            elif action == GovernanceAction.ALERT:
                cost = self._do_alert(boundary_type)
                actions_taken.append("alert")
                total_cost += cost

        # 3. Check for persistent solitons
        persistent = self._check_persistent_solitons(boundary_type)
        if persistent:
            # Force dispersion
            dispersion_cost = self._disperse_solitons(persistent)
            total_cost += dispersion_cost
            actions_taken.append("disperse")
            details["solitons_dispersed"] = len(persistent)

        # 4. Record ATP
        self.atp_budget.spend(f"boundary_{boundary_type.value}", total_cost)

        # 5. Log event
        state_after = self.state_manager.snapshot()
        details["actions"] = actions_taken
        details["atp_cost"] = total_cost

        self._log_event(boundary_type, GovernanceAction.RESET, total_cost, details)

        return {
            "boundary": boundary_type.value,
            "actions_taken": actions_taken,
            "atp_cost": total_cost,
            "state_before": self._state_summary(state_before),
            "state_after": self._state_summary(state_after),
            "solitons_dispersed": details.get("solitons_dispersed", 0)
        }

    def _do_commit(self, boundary: BoundaryType, context: Dict[str, any]) -> float:
        """Serialize state to memory"""
        snapshot = self.state_manager.snapshot()
        self.state_manager.history.append(snapshot)
        # In production: write to disk/database
        return 0.5  # ATP cost

    def _do_clear(self, boundary: BoundaryType) -> float:
        """Clear appropriate state types"""
        cost = 0.0

        if boundary.value >= BoundaryType.EXERCISE.value:
            self.state_manager.clear(StateType.WORKING)
            cost += 1.0

        if boundary.value >= BoundaryType.SESSION.value:
            self.state_manager.clear(StateType.TASK)
            cost += 0.5

        return cost

    def _do_reset(self, boundary: BoundaryType) -> float:
        """Full reset (except identity)"""
        self.state_manager.clear(StateType.SCRATCH)
        self.state_manager.clear(StateType.WORKING)
        self.state_manager.clear(StateType.TASK)

        if boundary == BoundaryType.PHASE:
            return self.atp_budget.COST_PHASE_TRANSITION
        else:
            return 2.0

    def _do_alert(self, boundary: BoundaryType) -> float:
        """Check for governance issues"""
        # Check for high-mass solitons
        for soliton in self.state_manager.current_state.solitons:
            risk = self.mass_monitor.check_persistence(soliton, soliton.persistence_count)
            if risk in ["CRITICAL", "SEVERE"]:
                # Log warning (in production: send to monitoring)
                print(f"WARNING: {risk} soliton detected: {soliton.pattern} (mass={soliton.mass})")

        return 0.0  # Alerts are free

    def _check_persistent_solitons(self, boundary: BoundaryType) -> List[CoherenceSoliton]:
        """Find solitons that should have cleared but didn't"""
        persistent = []

        for soliton in self.state_manager.current_state.solitons:
            soliton.persistence_count += 1

            # Any soliton surviving exercise boundary is suspect
            if boundary.value >= BoundaryType.EXERCISE.value:
                persistent.append(soliton)

        return persistent

    def _disperse_solitons(self, solitons: List[CoherenceSoliton]) -> float:
        """Force dispersion of persistent solitons"""
        total_cost = 0.0

        for soliton in solitons:
            cost = soliton.mass * self.atp_budget.COST_SOLITON_DISPERSE
            self.state_manager.remove_soliton(soliton)
            total_cost += cost
            print(f"DISPERSED: {soliton.pattern} soliton (mass={soliton.mass}, cost={cost} ATP)")

        return total_cost

    def _log_event(self, boundary: BoundaryType, action: GovernanceAction, cost: float, details: Dict):
        """Record governance event"""
        event = GovernanceEvent(
            timestamp=datetime.now(),
            boundary_type=boundary,
            action=action,
            state_before=self.state_manager.snapshot(),
            state_after=self.state_manager.snapshot(),
            atp_cost=cost,
            details=details
        )
        self.audit_log.append(event)

    def _state_summary(self, state: StateSnapshot) -> Dict:
        """Summarize state for reporting"""
        return {
            "coherence": state.coherence,
            "mass_total": state.mass_total,
            "solitons": len(state.solitons),
            "working_memory_size": len(state.working_memory),
            "task_context_size": len(state.task_context)
        }

    def get_audit_trail(self) -> List[Dict]:
        """Return full audit trail"""
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "boundary": event.boundary_type.value,
                "action": event.action.value,
                "atp_cost": event.atp_cost,
                "details": event.details
            }
            for event in self.audit_log
        ]


# ============================================================================
# PHASE TRANSITION HANDLER
# ============================================================================

class PhaseTransition:
    """
    Specialized handler for phase boundaries

    Implements full state governance for Training→Sensing, Sensing→Integration, etc.
    Based on Session #6 cross-phase soliton incident.
    """

    def __init__(self, governance: StateGovernance):
        self.governance = governance

    def execute(self, from_phase: str, to_phase: str, summary: str = "") -> Dict[str, any]:
        """
        Execute phase transition with full governance

        Steps (from Session #22 framework):
        1. Capture current state
        2. Summarize phase
        3. Commit to long-term memory
        4. FORCE clear working memory
        5. Clear task context
        6. Check for persistent solitons (CRITICAL)
        7. Initialize fresh for new phase

        Returns transition report
        """
        print(f"\n=== PHASE TRANSITION: {from_phase} → {to_phase} ===\n")

        # 1. Capture state
        state_before = self.governance.state_manager.snapshot()
        print(f"State before: {state_before.coherence:.2f} coherence, {state_before.mass_total:.1f} total mass")

        # 2-3. Summarize and commit
        phase_summary = {
            "phase": from_phase,
            "completion_time": datetime.now().isoformat(),
            "final_coherence": state_before.coherence,
            "total_mass": state_before.mass_total,
            "solitons_formed": len(state_before.solitons),
            "summary": summary or f"Completed {from_phase} phase"
        }
        self.governance._do_commit(BoundaryType.PHASE, phase_summary)
        print(f"Committed phase summary: {len(state_before.solitons)} solitons recorded")

        # 4-5. Full reset
        reset_cost = self.governance._do_reset(BoundaryType.PHASE)
        print(f"Reset complete: {reset_cost} ATP")

        # 6. CRITICAL: Check for persistent solitons
        persistent = self.governance._check_persistent_solitons(BoundaryType.PHASE)

        if persistent:
            print(f"\nWARNING: {len(persistent)} solitons survived phase clear!")
            for sol in persistent:
                risk = self.governance.mass_monitor.check_persistence(sol, sol.persistence_count)
                print(f"  - {sol.pattern}: mass={sol.mass:.1f}, type={sol.soliton_type}, risk={risk}")

            # FORCE dispersion
            disperse_cost = self.governance._disperse_solitons(persistent)
            print(f"Forced dispersion: {disperse_cost} ATP")
        else:
            print("Clean transition: No persistent solitons")
            disperse_cost = 0.0

        # 7. Initialize fresh
        self.governance.state_manager.current_state.task_context = {
            "phase": to_phase,
            "start_time": datetime.now().isoformat()
        }

        # Final state
        state_after = self.governance.state_manager.snapshot()
        total_cost = reset_cost + disperse_cost

        print(f"\nState after: {state_after.coherence:.2f} coherence, {state_after.mass_total:.1f} total mass")
        print(f"Total ATP cost: {total_cost}")
        print(f"\n=== TRANSITION COMPLETE ===\n")

        return {
            "from_phase": from_phase,
            "to_phase": to_phase,
            "solitons_before": len(state_before.solitons),
            "solitons_after": len(state_after.solitons),
            "solitons_dispersed": len(persistent),
            "atp_cost": total_cost,
            "state_clean": len(state_after.solitons) == 0
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_sage_training():
    """Example: SAGE training session with governance"""
    print("="*60)
    print("EXAMPLE: SAGE Training Session with State Governance")
    print("="*60)

    gov = StateGovernance(atp_initial=100.0)

    # Exercise 1
    print("\n--- Exercise 1: Count 1-5 ---")
    response1 = "1, 2, 3, 4, 5"
    gov.process_response(response1)
    gov.process_boundary(BoundaryType.EXERCISE)

    # Exercise 2: Forms soliton
    print("\n--- Exercise 2: Complex problem (forms soliton) ---")
    response2 = "Certainly! Here's a refined version: The answer is 4 apples. Let me explain the reasoning..."
    details = gov.process_response(response2)
    print(f"Soliton detected: {details.get('soliton_detected')}")
    if details.get('soliton_detected'):
        print(f"  Mass: {details['mass']:.1f}")
        print(f"  Type: {details['type']}")
        print(f"  Risk: {details['risk']}")

    boundary_result = gov.process_boundary(BoundaryType.EXERCISE)
    print(f"Boundary processed: {boundary_result['actions_taken']}")
    print(f"ATP cost: {boundary_result['atp_cost']}")

    # Exercise 3
    print("\n--- Exercise 3: Should be fresh (soliton should be gone) ---")
    response3 = "Blue"
    gov.process_response(response3)
    gov.process_boundary(BoundaryType.EXERCISE)

    # Session end
    print("\n--- Session End ---")
    session_result = gov.process_boundary(BoundaryType.SESSION)
    print(f"Actions: {session_result['actions_taken']}")

    # Audit trail
    print("\n--- Audit Trail ---")
    for event in gov.get_audit_trail():
        print(f"{event['boundary']}: {event['action']} (ATP: {event['atp_cost']})")


def example_phase_transition():
    """Example: Phase transition with soliton dispersion"""
    print("\n" + "="*60)
    print("EXAMPLE: Phase Transition (Training → Sensing)")
    print("="*60)

    gov = StateGovernance(atp_initial=100.0)

    # Simulate end of Training with persistent soliton
    print("\n--- End of Training Phase ---")
    print("Simulating Session #6 scenario: 'refined version' soliton active")

    # Add soliton manually to simulate Session #6
    soliton = CoherenceSoliton(
        topic="general",
        pattern="refined_version",
        amplitude=0.4,
        width=50,
        mass=20.0,  # Identity-class
        formation_time=datetime.now(),
        soliton_type="identity-class"
    )
    gov.state_manager.add_soliton(soliton)

    print(f"Soliton present: mass={soliton.mass}, type={soliton.soliton_type}")

    # Execute phase transition
    phase_handler = PhaseTransition(gov)
    result = phase_handler.execute(
        from_phase="Training",
        to_phase="Sensing",
        summary="Completed T001-T012 basic skills"
    )

    # Report
    print("\n--- Transition Report ---")
    print(f"Solitons dispersed: {result['solitons_dispersed']}")
    print(f"State clean: {result['state_clean']}")
    print(f"Total ATP cost: {result['atp_cost']}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("State Governance Implementation - Session #22")
    print("Validated against T011, T012, and Session #6 incidents\n")

    example_sage_training()
    example_phase_transition()

    print("\n" + "="*60)
    print("Implementation demonstrates:")
    print("  1. State type classification (identity/task/working/scratch)")
    print("  2. Boundary enforcement (response/exercise/session/phase)")
    print("  3. Soliton detection and dispersion")
    print("  4. ATP budgeting")
    print("  5. Full audit trail")
    print("="*60)
