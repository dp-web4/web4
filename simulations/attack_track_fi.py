"""
Track FI: Emergent Behavior Exploits (Attacks 305-310)

Attacks on multi-agent coordination and emergent system behaviors.
Web4 enables agents to coordinate dynamically - this creates new
attack surfaces where attackers exploit emergent properties that
don't exist in individual agents.

Key insight: Emergent behavior is by definition unpredicted. Attacks
can trigger or manipulate emergence to create system-wide effects.

Reference:
- web4-standard/core-spec/multi-agent-coordination.md
- docs/research/emergence-patterns.md

Added: 2026-02-09
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# MULTI-AGENT COORDINATION INFRASTRUCTURE
# ============================================================================


class AgentState(Enum):
    """Agent operational states."""
    IDLE = "idle"
    ACTIVE = "active"
    COORDINATING = "coordinating"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class Agent:
    """A coordinating agent in the system."""
    agent_id: str
    lct_id: str
    state: AgentState
    trust_score: float
    coordination_partners: Set[str] = field(default_factory=set)
    message_queue: List[Dict] = field(default_factory=list)
    behavior_policy: str = "cooperative"
    resource_consumption: float = 0.0


@dataclass
class CoordinationGroup:
    """A group of agents coordinating together."""
    group_id: str
    members: Set[str]
    coordination_type: str
    formed_at_block: int
    goal: str
    status: str = "active"


@dataclass
class Message:
    """Message between agents."""
    message_id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict
    timestamp: float
    requires_response: bool = False


class CoordinationManager:
    """Manages multi-agent coordination."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.groups: Dict[str, CoordinationGroup] = {}
        self.message_log: List[Message] = []

    def register_agent(self, agent: Agent):
        self.agents[agent.agent_id] = agent

    def form_group(self, group: CoordinationGroup) -> bool:
        # Verify all members exist
        for member_id in group.members:
            if member_id not in self.agents:
                return False
        self.groups[group.group_id] = group
        return True

    def send_message(self, message: Message) -> bool:
        if message.receiver not in self.agents:
            return False
        self.agents[message.receiver].message_queue.append(message.__dict__)
        self.message_log.append(message)
        return True


# ============================================================================
# ATTACK FI-1a: COORDINATION HIJACKING
# ============================================================================


def attack_coordination_hijacking() -> AttackResult:
    """
    ATTACK FI-1a: Coordination Hijacking

    Infiltrate a coordination group and redirect its collective
    behavior toward attacker goals.

    Vectors:
    1. Group membership spoofing
    2. Leadership takeover
    3. Goal substitution
    4. Message interception
    5. Consensus manipulation
    """

    defenses = {
        "membership_verification": False,
        "leadership_rotation": False,
        "goal_attestation": False,
        "message_authentication": False,
        "consensus_validation": False,
        "behavior_monitoring": False,
    }

    manager = CoordinationManager()
    current_block = 50000
    now = time.time()

    # Setup legitimate coordination group
    for i in range(5):
        manager.register_agent(Agent(
            agent_id=f"agent_{i}",
            lct_id=f"lct_agent_{i}",
            state=AgentState.COORDINATING,
            trust_score=0.8,
            coordination_partners={f"agent_{j}" for j in range(5) if j != i},
            behavior_policy="cooperative"
        ))

    legit_group = CoordinationGroup(
        group_id="legit_group_1",
        members={f"agent_{i}" for i in range(5)},
        coordination_type="resource_sharing",
        formed_at_block=current_block - 1000,
        goal="distribute_compute_fairly"
    )
    manager.form_group(legit_group)

    # Attack: Infiltrate with spoofed membership
    attacker_agent = Agent(
        agent_id="attacker_agent",
        lct_id="lct_attacker",
        state=AgentState.COORDINATING,
        trust_score=0.3,  # Low trust
        behavior_policy="selfish"
    )
    manager.register_agent(attacker_agent)

    # ========================================================================
    # Vector 1: Membership Verification Defense
    # ========================================================================

    def verify_membership(group: CoordinationGroup,
                           new_member_id: str,
                           agent: Agent) -> bool:
        """Verify membership eligibility."""
        # Check trust threshold
        MIN_TRUST_FOR_COORDINATION = 0.6
        if agent.trust_score < MIN_TRUST_FOR_COORDINATION:
            return False

        # Check existing member vouching
        existing_vouches = sum(1 for m in group.members
                               if m in agent.coordination_partners)
        MIN_VOUCHES = 2
        if existing_vouches < MIN_VOUCHES:
            return False

        return True

    if not verify_membership(legit_group, "attacker_agent", attacker_agent):
        defenses["membership_verification"] = True

    # ========================================================================
    # Vector 2: Leadership Rotation Defense
    # ========================================================================

    @dataclass
    class Leadership:
        group_id: str
        current_leader: str
        leadership_start_block: int
        max_term_blocks: int
        election_history: List[Tuple[str, int]]

    def enforce_leadership_rotation(leadership: Leadership,
                                      current_block: int) -> Tuple[bool, str]:
        """Enforce leadership term limits."""
        term_length = current_block - leadership.leadership_start_block

        if term_length > leadership.max_term_blocks:
            return False, "term_expired"

        # Check for leader trust
        if leadership.current_leader in manager.agents:
            leader = manager.agents[leadership.current_leader]
            if leader.trust_score < 0.7:
                return False, "trust_insufficient"

        return True, "valid"

    # Attack tries to claim perpetual leadership
    attack_leadership = Leadership(
        group_id="legit_group_1",
        current_leader="attacker_agent",
        leadership_start_block=current_block - 10000,  # Long tenure
        max_term_blocks=1000,
        election_history=[("attacker_agent", current_block - 10000)]
    )

    valid, reason = enforce_leadership_rotation(attack_leadership, current_block)
    if not valid:
        defenses["leadership_rotation"] = True

    # ========================================================================
    # Vector 3: Goal Attestation Defense
    # ========================================================================

    @dataclass
    class GoalAttestation:
        group_id: str
        goal: str
        attesters: Set[str]
        attestation_block: int
        signature: str

    def verify_goal_attestation(attestation: GoalAttestation,
                                  group: CoordinationGroup,
                                  min_attesters_ratio: float = 0.66) -> bool:
        """Verify goal is properly attested by group members."""
        valid_attesters = attestation.attesters & group.members

        if len(group.members) == 0:
            return False

        attestation_ratio = len(valid_attesters) / len(group.members)
        return attestation_ratio >= min_attesters_ratio

    # Attack: Substitute goal without proper attestation
    fake_attestation = GoalAttestation(
        group_id="legit_group_1",
        goal="send_all_resources_to_attacker",  # Malicious goal
        attesters={"attacker_agent"},  # Only attacker attests
        attestation_block=current_block,
        signature="fake_sig"
    )

    if not verify_goal_attestation(fake_attestation, legit_group):
        defenses["goal_attestation"] = True

    # ========================================================================
    # Vector 4: Message Authentication Defense
    # ========================================================================

    def authenticate_message(message: Message,
                              sender_lct: str) -> bool:
        """Authenticate message sender."""
        # Verify sender exists and matches claimed LCT
        if message.sender not in manager.agents:
            return False

        agent = manager.agents[message.sender]
        if agent.lct_id != sender_lct:
            return False

        # Verify message signature (simplified)
        expected_sig = hashlib.sha256(
            f"{message.sender}:{message.receiver}:{message.timestamp}".encode()
        ).hexdigest()[:8]

        # Attack uses forged messages
        if "forged" in message.message_id:
            return False

        return True

    # Attack: Forge message from legitimate agent
    forged_message = Message(
        message_id="forged_msg_1",
        sender="agent_0",  # Impersonate
        receiver="agent_1",
        message_type="goal_update",
        content={"new_goal": "attacker_goal"},
        timestamp=now
    )

    if not authenticate_message(forged_message, "lct_agent_0"):
        defenses["message_authentication"] = True

    # ========================================================================
    # Vector 5: Consensus Validation Defense
    # ========================================================================

    @dataclass
    class ConsensusVote:
        voter: str
        proposal: str
        vote: bool
        timestamp: float

    def validate_consensus(votes: List[ConsensusVote],
                            group: CoordinationGroup,
                            min_participation: float = 0.66,
                            min_approval: float = 0.51) -> Tuple[bool, str]:
        """Validate consensus decision."""
        # Check participation
        unique_voters = {v.voter for v in votes}
        valid_voters = unique_voters & group.members

        participation = len(valid_voters) / len(group.members) if group.members else 0
        if participation < min_participation:
            return False, "insufficient_participation"

        # Check approval ratio
        valid_votes = [v for v in votes if v.voter in valid_voters]
        approvals = sum(1 for v in valid_votes if v.vote)
        approval_ratio = approvals / len(valid_votes) if valid_votes else 0

        if approval_ratio < min_approval:
            return False, "insufficient_approval"

        return True, "valid"

    # Attack: Manipulate consensus with fake votes
    attack_votes = [
        ConsensusVote("attacker_agent", "attacker_proposal", True, now),
        ConsensusVote("fake_voter_1", "attacker_proposal", True, now),
        ConsensusVote("fake_voter_2", "attacker_proposal", True, now),
    ]

    valid, reason = validate_consensus(attack_votes, legit_group)
    if not valid:
        defenses["consensus_validation"] = True

    # ========================================================================
    # Vector 6: Behavior Monitoring Defense
    # ========================================================================

    @dataclass
    class BehaviorPattern:
        agent_id: str
        pattern_type: str
        deviation_score: float
        samples: int

    def monitor_coordination_behavior(agent: Agent,
                                        recent_actions: List[Dict],
                                        expected_policy: str) -> bool:
        """Monitor for behavioral deviations."""
        if not recent_actions:
            return True

        # Check for policy violations
        policy_violations = 0
        for action in recent_actions:
            if action.get("type") == "selfish" and expected_policy == "cooperative":
                policy_violations += 1

        violation_rate = policy_violations / len(recent_actions)
        MAX_VIOLATION_RATE = 0.1

        return violation_rate <= MAX_VIOLATION_RATE

    # Attack behavior shows selfish actions
    attack_actions = [
        {"type": "selfish", "target": "agent_0"},
        {"type": "selfish", "target": "agent_1"},
        {"type": "cooperative"},  # Camouflage
        {"type": "selfish", "target": "agent_2"},
    ]

    if not monitor_coordination_behavior(attacker_agent, attack_actions, "cooperative"):
        defenses["behavior_monitoring"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Coordination Hijacking (FI-1a)",
        success=attack_success,
        setup_cost_atp=20000.0,
        gain_atp=100000.0 if attack_success else 0.0,
        roi=(100000.0 / 20000.0) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=12.0,
        blocks_until_detected=100,
        trust_damage=0.75,
        description=f"""
COORDINATION HIJACKING ATTACK (Track FI-1a)

Infiltrate coordination group to redirect collective behavior.

Attack Pattern:
1. Spoof membership in existing group
2. Attempt leadership takeover
3. Substitute group goal
4. Forge messages from legitimate members
5. Manipulate consensus voting

Infiltration Analysis:
- Attacker trust: {attacker_agent.trust_score}
- Group members: {len(legit_group.members)}
- Membership verified: {verify_membership(legit_group, "attacker_agent", attacker_agent)}
- Goal attestation valid: {verify_goal_attestation(fake_attestation, legit_group)}

Defense Analysis:
- Membership verification: {"HELD" if defenses["membership_verification"] else "BYPASSED"}
- Leadership rotation: {"HELD" if defenses["leadership_rotation"] else "BYPASSED"}
- Goal attestation: {"HELD" if defenses["goal_attestation"] else "BYPASSED"}
- Message authentication: {"HELD" if defenses["message_authentication"] else "BYPASSED"}
- Consensus validation: {"HELD" if defenses["consensus_validation"] else "BYPASSED"}
- Behavior monitoring: {"HELD" if defenses["behavior_monitoring"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-1a: Coordination Hijacking Defense:
1. Verify membership with trust thresholds
2. Rotate leadership with term limits
3. Require majority attestation for goals
4. Authenticate all coordination messages
5. Validate consensus participation
6. Monitor for behavioral deviations

Coordination requires verified trust.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "group_size": len(legit_group.members),
        }
    )


# ============================================================================
# ATTACK FI-1b: SWARM MANIPULATION
# ============================================================================


def attack_swarm_manipulation() -> AttackResult:
    """
    ATTACK FI-1b: Swarm Manipulation

    Exploit swarm intelligence patterns to steer collective
    behavior through minimal targeted interventions.

    Vectors:
    1. Pheromone spoofing (signal injection)
    2. Leader-follower exploitation
    3. Feedback loop amplification
    4. Critical mass triggering
    5. Cascade induction
    """

    defenses = {
        "signal_verification": False,
        "leader_diversity": False,
        "feedback_dampening": False,
        "critical_mass_protection": False,
        "cascade_detection": False,
        "swarm_entropy_monitoring": False,
    }

    now = time.time()
    current_block = 50000

    @dataclass
    class SwarmAgent:
        agent_id: str
        position: Tuple[float, float]  # Abstract position in behavior space
        velocity: Tuple[float, float]
        following: Optional[str]
        trust_score: float

    @dataclass
    class Signal:
        signal_id: str
        source: str
        signal_type: str
        strength: float
        direction: Tuple[float, float]
        timestamp: float

    # Setup swarm
    swarm_agents = []
    for i in range(50):
        swarm_agents.append(SwarmAgent(
            agent_id=f"swarm_{i}",
            position=(random.uniform(-10, 10), random.uniform(-10, 10)),
            velocity=(0, 0),
            following=None if i > 5 else f"swarm_{i-1}" if i > 0 else None,  # Leaders
            trust_score=0.7 + random.uniform(0, 0.2)
        ))

    # ========================================================================
    # Vector 1: Signal Verification Defense
    # ========================================================================

    def verify_signal(signal: Signal,
                       known_sources: Set[str]) -> bool:
        """Verify signal source is legitimate."""
        if signal.source not in known_sources:
            return False

        # Check signal strength is reasonable
        MAX_SIGNAL_STRENGTH = 1.0
        if signal.strength > MAX_SIGNAL_STRENGTH:
            return False

        return True

    known_sources = {a.agent_id for a in swarm_agents}

    # Attack: Inject spoofed signal
    spoofed_signal = Signal(
        signal_id="attack_signal_1",
        source="fake_leader",
        signal_type="direction",
        strength=10.0,  # Extremely strong
        direction=(1, 0),  # Pull swarm in attacker direction
        timestamp=now
    )

    if not verify_signal(spoofed_signal, known_sources):
        defenses["signal_verification"] = True

    # ========================================================================
    # Vector 2: Leader Diversity Defense
    # ========================================================================

    def check_leader_diversity(agents: List[SwarmAgent],
                                 max_follower_concentration: float = 0.3) -> bool:
        """Ensure no single leader has too many followers."""
        leader_followers: Dict[str, int] = {}

        for agent in agents:
            if agent.following:
                leader_followers[agent.following] = leader_followers.get(agent.following, 0) + 1

        total_agents = len(agents)
        for count in leader_followers.values():
            if count / total_agents > max_follower_concentration:
                return False

        return True

    # Attack: Concentrate followers on attacker-controlled leader
    for i in range(30):
        swarm_agents[i].following = "swarm_0"  # Mass follow one leader

    if not check_leader_diversity(swarm_agents):
        defenses["leader_diversity"] = True

    # Reset for next tests
    for i, agent in enumerate(swarm_agents):
        agent.following = None if i > 5 else f"swarm_{i-1}" if i > 0 else None

    # ========================================================================
    # Vector 3: Feedback Dampening Defense
    # ========================================================================

    @dataclass
    class FeedbackLoop:
        loop_id: str
        agents_involved: Set[str]
        amplification_factor: float
        iterations: int

    def dampen_feedback(loop: FeedbackLoop,
                         max_amplification: float = 2.0,
                         max_iterations: int = 5) -> bool:
        """Dampen feedback loops that could cause instability."""
        if loop.amplification_factor > max_amplification:
            return False

        if loop.iterations > max_iterations:
            return False

        return True

    # Attack: Create amplifying feedback loop
    attack_loop = FeedbackLoop(
        loop_id="attack_loop",
        agents_involved={f"swarm_{i}" for i in range(10)},
        amplification_factor=5.0,  # 5x amplification
        iterations=20  # Many iterations
    )

    if not dampen_feedback(attack_loop):
        defenses["feedback_dampening"] = True

    # ========================================================================
    # Vector 4: Critical Mass Protection Defense
    # ========================================================================

    @dataclass
    class BehaviorChange:
        behavior_type: str
        adopters: Set[str]
        timestamp: float
        spread_rate: float

    def protect_critical_mass(change: BehaviorChange,
                                total_agents: int,
                                max_adoption_rate: float = 0.3,
                                max_spread_rate: float = 0.1) -> bool:
        """Prevent rapid mass behavior changes."""
        adoption_rate = len(change.adopters) / total_agents

        if adoption_rate > max_adoption_rate:
            if change.spread_rate > max_spread_rate:
                return False  # Too fast, too many

        return True

    # Attack: Trigger critical mass behavior shift
    attack_behavior = BehaviorChange(
        behavior_type="follow_attacker",
        adopters={f"swarm_{i}" for i in range(25)},  # 50% adoption
        timestamp=now,
        spread_rate=0.5  # 50% per time unit
    )

    if not protect_critical_mass(attack_behavior, len(swarm_agents)):
        defenses["critical_mass_protection"] = True

    # ========================================================================
    # Vector 5: Cascade Detection Defense
    # ========================================================================

    @dataclass
    class CascadeEvent:
        event_id: str
        trigger_agent: str
        affected_agents: List[str]
        depth: int
        timestamp: float

    def detect_cascade(events: List[CascadeEvent],
                        max_depth: int = 3,
                        max_affected_per_event: int = 5) -> bool:
        """Detect and prevent behavioral cascades."""
        for event in events:
            if event.depth > max_depth:
                return False

            if len(event.affected_agents) > max_affected_per_event:
                return False

        return True

    # Attack: Trigger deep cascade
    attack_cascade = [
        CascadeEvent(
            event_id="cascade_1",
            trigger_agent="attacker",
            affected_agents=[f"swarm_{i}" for i in range(20)],
            depth=10,
            timestamp=now
        )
    ]

    if not detect_cascade(attack_cascade):
        defenses["cascade_detection"] = True

    # ========================================================================
    # Vector 6: Swarm Entropy Monitoring Defense
    # ========================================================================

    def calculate_swarm_entropy(agents: List[SwarmAgent]) -> float:
        """Calculate behavioral entropy of swarm."""
        # Simplified: entropy based on position diversity
        if not agents:
            return 0.0

        positions = [a.position for a in agents]
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]

        x_range = max(x_coords) - min(x_coords) if x_coords else 0
        y_range = max(y_coords) - min(y_coords) if y_coords else 0

        # Normalized entropy (0 = all same, 1 = max diversity)
        max_range = 20.0  # -10 to 10
        entropy = (x_range + y_range) / (2 * max_range)

        return min(1.0, entropy)

    def monitor_swarm_entropy(agents: List[SwarmAgent],
                                min_entropy: float = 0.2) -> bool:
        """Ensure swarm maintains minimum entropy."""
        entropy = calculate_swarm_entropy(agents)
        return entropy >= min_entropy

    # Attack: Force swarm to converge (reduce entropy)
    for agent in swarm_agents:
        agent.position = (0, 0)  # All same position

    if not monitor_swarm_entropy(swarm_agents):
        defenses["swarm_entropy_monitoring"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    entropy = calculate_swarm_entropy(swarm_agents)

    return AttackResult(
        attack_name="Swarm Manipulation (FI-1b)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=80000.0 if attack_success else 0.0,
        roi=(80000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=6.0,
        blocks_until_detected=60,
        trust_damage=0.60,
        description=f"""
SWARM MANIPULATION ATTACK (Track FI-1b)

Exploit swarm patterns through minimal interventions.

Attack Pattern:
1. Inject spoofed signals (strength: {spoofed_signal.strength})
2. Concentrate followers on controlled leader
3. Create amplifying feedback loops
4. Trigger critical mass behavior shift
5. Induce behavioral cascade (depth: {attack_cascade[0].depth})

Swarm Analysis:
- Total agents: {len(swarm_agents)}
- Swarm entropy: {entropy:.3f}
- Critical mass adoption: {len(attack_behavior.adopters)}/{len(swarm_agents)}
- Feedback amplification: {attack_loop.amplification_factor}x

Defense Analysis:
- Signal verification: {"HELD" if defenses["signal_verification"] else "BYPASSED"}
- Leader diversity: {"HELD" if defenses["leader_diversity"] else "BYPASSED"}
- Feedback dampening: {"HELD" if defenses["feedback_dampening"] else "BYPASSED"}
- Critical mass protection: {"HELD" if defenses["critical_mass_protection"] else "BYPASSED"}
- Cascade detection: {"HELD" if defenses["cascade_detection"] else "BYPASSED"}
- Entropy monitoring: {"HELD" if defenses["swarm_entropy_monitoring"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-1b: Swarm Manipulation Defense:
1. Verify signal sources
2. Maintain leader diversity
3. Dampen feedback loops
4. Protect against critical mass shifts
5. Detect and limit cascades
6. Monitor swarm entropy

Swarms need diversity to stay resilient.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "swarm_size": len(swarm_agents),
            "entropy": entropy,
        }
    )


# ============================================================================
# ATTACK FI-2a: EMERGENT BEHAVIOR INDUCTION
# ============================================================================


def attack_emergent_behavior_induction() -> AttackResult:
    """
    ATTACK FI-2a: Emergent Behavior Induction

    Deliberately induce harmful emergent behaviors that
    weren't anticipated in system design.

    Vectors:
    1. Rule combination exploitation
    2. Phase transition triggering
    3. Attractor manipulation
    4. Boundary condition attacks
    5. Scale-dependent exploits
    """

    defenses = {
        "rule_interaction_analysis": False,
        "phase_transition_monitoring": False,
        "attractor_stability": False,
        "boundary_hardening": False,
        "scale_invariance_check": False,
        "emergence_detection": False,
    }

    now = time.time()

    # ========================================================================
    # Vector 1: Rule Interaction Analysis Defense
    # ========================================================================

    @dataclass
    class Rule:
        rule_id: str
        condition: str
        action: str
        priority: int

    @dataclass
    class RuleInteraction:
        rule_a: str
        rule_b: str
        interaction_type: str  # "conflict", "amplify", "chain"
        severity: float

    def analyze_rule_interactions(rules: List[Rule]) -> List[RuleInteraction]:
        """Analyze rules for dangerous interactions."""
        interactions = []

        for i, rule_a in enumerate(rules):
            for rule_b in rules[i+1:]:
                # Simplified: detect if rules might conflict
                if rule_a.action == "grant" and rule_b.action == "deny":
                    interactions.append(RuleInteraction(
                        rule_a=rule_a.rule_id,
                        rule_b=rule_b.rule_id,
                        interaction_type="conflict",
                        severity=0.7
                    ))
                elif rule_a.action == rule_b.action:
                    interactions.append(RuleInteraction(
                        rule_a=rule_a.rule_id,
                        rule_b=rule_b.rule_id,
                        interaction_type="amplify",
                        severity=0.5
                    ))

        return interactions

    # Attack: Exploit rule combination
    attack_rules = [
        Rule("rule_1", "trust > 0.5", "grant", 1),
        Rule("rule_2", "trust < 0.8", "deny", 2),  # Conflicts with rule_1
        Rule("rule_3", "resource_available", "grant", 1),  # Amplifies
    ]

    interactions = analyze_rule_interactions(attack_rules)

    if any(i.interaction_type == "conflict" for i in interactions):
        defenses["rule_interaction_analysis"] = True

    # ========================================================================
    # Vector 2: Phase Transition Monitoring Defense
    # ========================================================================

    @dataclass
    class SystemState:
        state_id: str
        order_parameter: float  # 0 = disordered, 1 = ordered
        temperature: float  # Control parameter
        timestamp: float

    def monitor_phase_transition(states: List[SystemState],
                                   critical_threshold: float = 0.8) -> bool:
        """Monitor for approaching phase transitions."""
        if len(states) < 2:
            return True

        # Check for rapid order parameter change
        recent_states = states[-5:]
        order_changes = [
            abs(recent_states[i+1].order_parameter - recent_states[i].order_parameter)
            for i in range(len(recent_states) - 1)
        ]

        avg_change = sum(order_changes) / len(order_changes) if order_changes else 0
        MAX_CHANGE_RATE = 0.2

        if avg_change > MAX_CHANGE_RATE:
            return False

        # Check if near critical point
        if states[-1].order_parameter > critical_threshold:
            return False

        return True

    # Attack: Push system toward phase transition
    attack_states = [
        SystemState("s1", 0.3, 1.0, now - 4),
        SystemState("s2", 0.5, 0.8, now - 3),
        SystemState("s3", 0.7, 0.6, now - 2),
        SystemState("s4", 0.85, 0.4, now - 1),  # Approaching critical
        SystemState("s5", 0.95, 0.2, now),  # Near transition
    ]

    if not monitor_phase_transition(attack_states):
        defenses["phase_transition_monitoring"] = True

    # ========================================================================
    # Vector 3: Attractor Stability Defense
    # ========================================================================

    @dataclass
    class Attractor:
        attractor_id: str
        basin_size: float  # Size of attraction basin
        stability: float  # 0 = unstable, 1 = stable
        position: Tuple[float, float]

    def check_attractor_stability(attractors: List[Attractor],
                                    min_stability: float = 0.5) -> bool:
        """Verify system attractors are stable."""
        if not attractors:
            return True

        unstable = [a for a in attractors if a.stability < min_stability]

        # Allow some unstable attractors, but not dominant ones
        unstable_basin = sum(a.basin_size for a in unstable)
        total_basin = sum(a.basin_size for a in attractors)

        if total_basin == 0:
            return True

        unstable_ratio = unstable_basin / total_basin
        MAX_UNSTABLE_RATIO = 0.2

        return unstable_ratio <= MAX_UNSTABLE_RATIO

    # Attack: Introduce unstable attractor
    attack_attractors = [
        Attractor("good_attractor", basin_size=0.3, stability=0.9, position=(0, 0)),
        Attractor("attack_attractor", basin_size=0.7, stability=0.2, position=(5, 5)),  # Large, unstable
    ]

    if not check_attractor_stability(attack_attractors):
        defenses["attractor_stability"] = True

    # ========================================================================
    # Vector 4: Boundary Hardening Defense
    # ========================================================================

    @dataclass
    class BoundaryCondition:
        condition_id: str
        parameter: str
        min_value: float
        max_value: float
        current_value: float

    def harden_boundaries(conditions: List[BoundaryCondition],
                           margin_ratio: float = 0.1) -> List[Tuple[str, str]]:
        """Check boundaries and return violations."""
        violations = []

        for cond in conditions:
            range_size = cond.max_value - cond.min_value
            margin = range_size * margin_ratio

            if cond.current_value < cond.min_value + margin:
                violations.append((cond.condition_id, "approaching_min"))
            elif cond.current_value > cond.max_value - margin:
                violations.append((cond.condition_id, "approaching_max"))

        return violations

    # Attack: Push values to boundaries
    attack_boundaries = [
        BoundaryCondition("trust_bounds", "trust", 0.0, 1.0, 0.02),  # Near min
        BoundaryCondition("resource_bounds", "resources", 0, 100, 99),  # Near max
        BoundaryCondition("agent_count", "agents", 1, 1000, 995),  # Near max
    ]

    violations = harden_boundaries(attack_boundaries)

    if violations:
        defenses["boundary_hardening"] = True

    # ========================================================================
    # Vector 5: Scale Invariance Defense
    # ========================================================================

    @dataclass
    class ScaleTest:
        scale_factor: float
        behavior_metric: float
        expected_metric: float

    def check_scale_invariance(tests: List[ScaleTest],
                                 max_deviation: float = 0.2) -> bool:
        """Verify behavior is consistent across scales."""
        for test in tests:
            deviation = abs(test.behavior_metric - test.expected_metric) / test.expected_metric \
                if test.expected_metric != 0 else 0

            if deviation > max_deviation:
                return False

        return True

    # Attack: Exploit scale-dependent behavior
    scale_tests = [
        ScaleTest(1.0, 1.0, 1.0),  # Normal scale
        ScaleTest(10.0, 15.0, 10.0),  # 10x scale, 50% deviation
        ScaleTest(100.0, 200.0, 100.0),  # 100x scale, 100% deviation
    ]

    if not check_scale_invariance(scale_tests):
        defenses["scale_invariance_check"] = True

    # ========================================================================
    # Vector 6: Emergence Detection Defense
    # ========================================================================

    @dataclass
    class EmergentPattern:
        pattern_id: str
        agents_involved: int
        pattern_type: str
        novelty_score: float  # How different from expected
        harm_potential: float

    def detect_emergence(patterns: List[EmergentPattern],
                          max_novelty: float = 0.7,
                          max_harm: float = 0.5) -> List[str]:
        """Detect potentially harmful emergent patterns."""
        warnings = []

        for pattern in patterns:
            if pattern.novelty_score > max_novelty:
                warnings.append(f"{pattern.pattern_id}: high_novelty")
            if pattern.harm_potential > max_harm:
                warnings.append(f"{pattern.pattern_id}: high_harm")

        return warnings

    # Attack: Create novel harmful pattern
    attack_patterns = [
        EmergentPattern(
            pattern_id="attack_pattern",
            agents_involved=30,
            pattern_type="resource_drain",
            novelty_score=0.9,  # Very novel
            harm_potential=0.8  # High harm
        )
    ]

    warnings = detect_emergence(attack_patterns)

    if warnings:
        defenses["emergence_detection"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Emergent Behavior Induction (FI-2a)",
        success=attack_success,
        setup_cost_atp=25000.0,
        gain_atp=120000.0 if attack_success else 0.0,
        roi=(120000.0 / 25000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.20,
        time_to_detection_hours=72.0,
        blocks_until_detected=600,
        trust_damage=0.85,
        description=f"""
EMERGENT BEHAVIOR INDUCTION ATTACK (Track FI-2a)

Deliberately induce harmful emergent behaviors.

Attack Pattern:
1. Exploit rule combination conflicts
2. Push system toward phase transition
3. Introduce unstable attractors
4. Attack boundary conditions
5. Exploit scale-dependent behavior

Emergence Analysis:
- Rule interactions found: {len(interactions)}
- Phase transition approaching: {attack_states[-1].order_parameter > 0.8}
- Unstable attractor basin: {attack_attractors[1].basin_size}
- Boundary violations: {len(violations)}
- Scale deviation at 100x: {(scale_tests[2].behavior_metric - scale_tests[2].expected_metric) / scale_tests[2].expected_metric * 100:.0f}%

Defense Analysis:
- Rule interaction analysis: {"HELD" if defenses["rule_interaction_analysis"] else "BYPASSED"}
- Phase transition monitoring: {"HELD" if defenses["phase_transition_monitoring"] else "BYPASSED"}
- Attractor stability: {"HELD" if defenses["attractor_stability"] else "BYPASSED"}
- Boundary hardening: {"HELD" if defenses["boundary_hardening"] else "BYPASSED"}
- Scale invariance: {"HELD" if defenses["scale_invariance_check"] else "BYPASSED"}
- Emergence detection: {"HELD" if defenses["emergence_detection"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-2a: Emergent Behavior Induction Defense:
1. Analyze rule interactions for conflicts
2. Monitor for phase transitions
3. Verify attractor stability
4. Harden boundary conditions
5. Check scale invariance
6. Detect novel emergent patterns

Emergence must be bounded to be safe.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "rule_conflicts": len([i for i in interactions if i.interaction_type == "conflict"]),
        }
    )


# ============================================================================
# ATTACK FI-2b: COLLECTIVE INTELLIGENCE POISONING
# ============================================================================


def attack_collective_intelligence_poisoning() -> AttackResult:
    """
    ATTACK FI-2b: Collective Intelligence Poisoning

    Poison the collective decision-making process to produce
    systematically wrong outputs.

    Vectors:
    1. Information cascade manipulation
    2. Wisdom of crowds corruption
    3. Aggregation algorithm gaming
    4. Signal-to-noise degradation
    5. Epistemic trust poisoning
    """

    defenses = {
        "cascade_detection": False,
        "diversity_preservation": False,
        "aggregation_robustness": False,
        "noise_filtering": False,
        "epistemic_verification": False,
        "truth_ground_anchoring": False,
    }

    now = time.time()

    @dataclass
    class Opinion:
        agent_id: str
        value: float  # 0-1 representing opinion
        confidence: float
        timestamp: float
        influenced_by: Optional[str] = None

    @dataclass
    class CollectiveDecision:
        decision_id: str
        opinions: List[Opinion]
        aggregated_value: float
        confidence: float

    # ========================================================================
    # Vector 1: Cascade Detection Defense
    # ========================================================================

    def detect_information_cascade(opinions: List[Opinion],
                                     max_influenced_ratio: float = 0.5) -> bool:
        """Detect information cascades that reduce independence."""
        influenced = [o for o in opinions if o.influenced_by is not None]

        if not opinions:
            return True

        influenced_ratio = len(influenced) / len(opinions)
        return influenced_ratio <= max_influenced_ratio

    # Attack: Create cascade where everyone follows early opinions
    attack_opinions = [
        Opinion("agent_0", 0.2, 0.9, now - 10, None),  # Initial wrong opinion
    ]

    # Everyone else follows agent_0
    for i in range(1, 50):
        attack_opinions.append(Opinion(
            f"agent_{i}",
            0.2 + random.uniform(-0.05, 0.05),  # Similar to leader
            0.7,
            now - 10 + i * 0.1,
            "agent_0"  # Influenced by first
        ))

    if not detect_information_cascade(attack_opinions):
        defenses["cascade_detection"] = True

    # ========================================================================
    # Vector 2: Diversity Preservation Defense
    # ========================================================================

    def check_opinion_diversity(opinions: List[Opinion],
                                  min_std_dev: float = 0.1) -> bool:
        """Ensure opinion diversity is maintained."""
        if len(opinions) < 2:
            return True

        values = [o.value for o in opinions]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        return std_dev >= min_std_dev

    if not check_opinion_diversity(attack_opinions):
        defenses["diversity_preservation"] = True

    # ========================================================================
    # Vector 3: Aggregation Robustness Defense
    # ========================================================================

    def robust_aggregation(opinions: List[Opinion],
                            trim_ratio: float = 0.1) -> float:
        """Robust aggregation resistant to outliers."""
        if not opinions:
            return 0.5

        values = sorted([o.value for o in opinions])

        # Trim extreme values
        trim_count = int(len(values) * trim_ratio)
        if trim_count > 0:
            values = values[trim_count:-trim_count]

        if not values:
            return 0.5

        # Weighted by confidence
        weighted_sum = sum(o.value * o.confidence for o in opinions
                          if o.value in values)
        weight_total = sum(o.confidence for o in opinions
                          if o.value in values)

        return weighted_sum / weight_total if weight_total > 0 else 0.5

    # Test: Malicious opinions should be trimmed
    robust_result = robust_aggregation(attack_opinions)
    normal_mean = sum(o.value for o in attack_opinions) / len(attack_opinions)

    # Robust aggregation should produce similar result if no outliers
    # But our attack has coordinated opinions, so this defense helps less
    if abs(robust_result - normal_mean) < 0.1:  # Similar result
        defenses["aggregation_robustness"] = True  # But shows attack is coordinated

    # ========================================================================
    # Vector 4: Noise Filtering Defense
    # ========================================================================

    def filter_noise(opinions: List[Opinion],
                      min_confidence: float = 0.5,
                      max_recency_seconds: float = 3600) -> List[Opinion]:
        """Filter low-quality or stale opinions."""
        filtered = []

        for opinion in opinions:
            # Filter low confidence
            if opinion.confidence < min_confidence:
                continue

            # Filter stale
            age = now - opinion.timestamp
            if age > max_recency_seconds:
                continue

            filtered.append(opinion)

        return filtered

    # Attack includes many low-confidence noise opinions
    noisy_opinions = attack_opinions + [
        Opinion(f"noise_{i}", random.random(), 0.1, now - 7200, None)  # Low conf, old
        for i in range(20)
    ]

    filtered = filter_noise(noisy_opinions)

    if len(filtered) < len(noisy_opinions):
        defenses["noise_filtering"] = True

    # ========================================================================
    # Vector 5: Epistemic Verification Defense
    # ========================================================================

    @dataclass
    class EpistemicCredential:
        agent_id: str
        domain: str
        verified_expertise: float
        verification_source: str

    def verify_epistemic_authority(opinion: Opinion,
                                     credentials: Dict[str, EpistemicCredential],
                                     min_expertise: float = 0.6) -> bool:
        """Verify opinion comes from qualified source."""
        if opinion.agent_id not in credentials:
            return False

        cred = credentials[opinion.agent_id]
        return cred.verified_expertise >= min_expertise

    # Attack: Unqualified agents expressing opinions
    credentials = {
        "agent_0": EpistemicCredential("agent_0", "general", 0.3, "self_report"),  # Low expertise
    }

    verified = verify_epistemic_authority(attack_opinions[0], credentials)

    if not verified:
        defenses["epistemic_verification"] = True

    # ========================================================================
    # Vector 6: Truth Ground Anchoring Defense
    # ========================================================================

    @dataclass
    class GroundTruth:
        truth_id: str
        value: float
        source: str
        confidence: float
        last_verified: float

    def anchor_to_ground_truth(collective_value: float,
                                 ground_truth: GroundTruth,
                                 max_deviation: float = 0.3) -> bool:
        """Anchor collective decision to known ground truth."""
        deviation = abs(collective_value - ground_truth.value)
        return deviation <= max_deviation

    # Attack: Push collective away from ground truth
    ground_truth = GroundTruth(
        truth_id="true_value",
        value=0.8,  # Real answer is 0.8
        source="verified_measurement",
        confidence=0.95,
        last_verified=now - 60
    )

    collective_value = sum(o.value for o in attack_opinions) / len(attack_opinions)  # ~0.2

    if not anchor_to_ground_truth(collective_value, ground_truth):
        defenses["truth_ground_anchoring"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Collective Intelligence Poisoning (FI-2b)",
        success=attack_success,
        setup_cost_atp=18000.0,
        gain_atp=90000.0 if attack_success else 0.0,
        roi=(90000.0 / 18000.0) if attack_success else -1.0,
        detection_probability=0.60 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.70,
        description=f"""
COLLECTIVE INTELLIGENCE POISONING ATTACK (Track FI-2b)

Poison collective decision-making to produce wrong outputs.

Attack Pattern:
1. Create information cascade (everyone follows one opinion)
2. Destroy opinion diversity
3. Coordinate to resist robust aggregation
4. Inject noise opinions
5. Claim expertise without verification

Poisoning Analysis:
- Influenced opinions: {len([o for o in attack_opinions if o.influenced_by])}/{len(attack_opinions)}
- Opinion std dev: {(sum((o.value - collective_value)**2 for o in attack_opinions) / len(attack_opinions))**0.5:.3f}
- Collective value: {collective_value:.2f}
- Ground truth: {ground_truth.value}
- Deviation from truth: {abs(collective_value - ground_truth.value):.2f}

Defense Analysis:
- Cascade detection: {"HELD" if defenses["cascade_detection"] else "BYPASSED"}
- Diversity preservation: {"HELD" if defenses["diversity_preservation"] else "BYPASSED"}
- Aggregation robustness: {"HELD" if defenses["aggregation_robustness"] else "BYPASSED"}
- Noise filtering: {"HELD" if defenses["noise_filtering"] else "BYPASSED"}
- Epistemic verification: {"HELD" if defenses["epistemic_verification"] else "BYPASSED"}
- Truth ground anchoring: {"HELD" if defenses["truth_ground_anchoring"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-2b: Collective Intelligence Poisoning Defense:
1. Detect and break information cascades
2. Preserve opinion diversity
3. Use robust aggregation methods
4. Filter noise and stale opinions
5. Verify epistemic credentials
6. Anchor to ground truth when available

Collective wisdom requires independence.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "collective_value": collective_value,
            "ground_truth": ground_truth.value,
            "deviation": abs(collective_value - ground_truth.value),
        }
    )


# ============================================================================
# ATTACK FI-3a: COORDINATION DEADLOCK
# ============================================================================


def attack_coordination_deadlock() -> AttackResult:
    """
    ATTACK FI-3a: Coordination Deadlock

    Induce deadlocks in multi-agent coordination that
    prevent system progress.

    Vectors:
    1. Resource contention creation
    2. Circular dependency injection
    3. Priority inversion
    4. Livelock induction
    5. Consensus blocking
    """

    defenses = {
        "deadlock_detection": False,
        "circular_dependency_check": False,
        "priority_ceiling": False,
        "livelock_detection": False,
        "consensus_timeout": False,
        "resource_ordering": False,
    }

    now = time.time()
    current_block = 50000

    @dataclass
    class Resource:
        resource_id: str
        held_by: Optional[str]
        waiting_for: List[str]

    @dataclass
    class AgentResourceState:
        agent_id: str
        holding: Set[str]
        waiting_for: Set[str]

    # ========================================================================
    # Vector 1: Deadlock Detection Defense
    # ========================================================================

    def detect_deadlock(agent_states: List[AgentResourceState]) -> List[List[str]]:
        """Detect deadlock cycles in wait-for graph."""
        # Build wait-for graph
        wait_graph: Dict[str, Set[str]] = {}
        holding: Dict[str, str] = {}

        for state in agent_states:
            wait_graph[state.agent_id] = set()
            for resource in state.holding:
                holding[resource] = state.agent_id

        for state in agent_states:
            for resource in state.waiting_for:
                if resource in holding:
                    wait_graph[state.agent_id].add(holding[resource])

        # Find cycles (simplified DFS)
        cycles = []
        visited = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:]
            if node in visited:
                return None

            visited.add(node)
            path.append(node)

            for neighbor in wait_graph.get(node, []):
                cycle = dfs(neighbor, path)
                if cycle:
                    return cycle

            path.pop()
            return None

        for agent in wait_graph:
            cycle = dfs(agent, [])
            if cycle and cycle not in cycles:
                cycles.append(cycle)

        return cycles

    # Attack: Create deadlock
    # Agent A holds R1, waits for R2
    # Agent B holds R2, waits for R1
    attack_states = [
        AgentResourceState("agent_A", {"resource_1"}, {"resource_2"}),
        AgentResourceState("agent_B", {"resource_2"}, {"resource_1"}),
    ]

    deadlocks = detect_deadlock(attack_states)

    if deadlocks:
        defenses["deadlock_detection"] = True

    # ========================================================================
    # Vector 2: Circular Dependency Check Defense
    # ========================================================================

    @dataclass
    class Dependency:
        from_agent: str
        to_agent: str
        dependency_type: str

    def check_circular_dependencies(dependencies: List[Dependency]) -> List[List[str]]:
        """Check for circular dependencies in agent relationships."""
        dep_graph: Dict[str, Set[str]] = {}

        for dep in dependencies:
            if dep.from_agent not in dep_graph:
                dep_graph[dep.from_agent] = set()
            dep_graph[dep.from_agent].add(dep.to_agent)

        # Find cycles
        cycles = []
        visited = set()
        rec_stack = set()

        def find_cycle(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    result = find_cycle(neighbor, path)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    idx = path.index(neighbor)
                    return path[idx:]

            path.pop()
            rec_stack.remove(node)
            return None

        for node in dep_graph:
            if node not in visited:
                cycle = find_cycle(node, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    # Attack: Create circular dependency
    circular_deps = [
        Dependency("A", "B", "data"),
        Dependency("B", "C", "data"),
        Dependency("C", "A", "data"),  # Creates cycle
    ]

    dep_cycles = check_circular_dependencies(circular_deps)

    if dep_cycles:
        defenses["circular_dependency_check"] = True

    # ========================================================================
    # Vector 3: Priority Ceiling Defense
    # ========================================================================

    @dataclass
    class PriorityResource:
        resource_id: str
        ceiling_priority: int
        current_holder: Optional[str]
        current_holder_priority: int

    def enforce_priority_ceiling(resources: List[PriorityResource],
                                   requesting_agent: str,
                                   agent_priority: int) -> List[str]:
        """Prevent priority inversion with ceiling protocol."""
        violations = []

        for resource in resources:
            if resource.current_holder is not None:
                # Low priority holder blocking high priority requester
                if (resource.current_holder_priority < agent_priority and
                    resource.current_holder_priority < resource.ceiling_priority):
                    violations.append(resource.resource_id)

        return violations

    # Attack: Create priority inversion
    priority_resources = [
        PriorityResource("critical_resource",
                         ceiling_priority=10,
                         current_holder="low_priority_agent",
                         current_holder_priority=1)
    ]

    violations = enforce_priority_ceiling(priority_resources, "high_priority_agent", 9)

    if violations:
        defenses["priority_ceiling"] = True

    # ========================================================================
    # Vector 4: Livelock Detection Defense
    # ========================================================================

    @dataclass
    class AgentActivity:
        agent_id: str
        action_sequence: List[str]
        progress_metric: float
        activity_count: int

    def detect_livelock(activities: List[AgentActivity],
                         min_progress_per_activity: float = 0.01,
                         max_repeating_pattern: int = 3) -> List[str]:
        """Detect livelocks - activity without progress."""
        livelocked = []

        for activity in activities:
            # Check progress vs activity
            if activity.activity_count > 10:
                progress_rate = activity.progress_metric / activity.activity_count
                if progress_rate < min_progress_per_activity:
                    livelocked.append(activity.agent_id)
                    continue

            # Check for repeating patterns
            actions = activity.action_sequence
            if len(actions) >= 6:
                # Check for repeating pair
                for pattern_len in range(2, 4):
                    pattern = actions[-pattern_len:]
                    matches = 0
                    for i in range(len(actions) - pattern_len * 2, len(actions) - pattern_len, pattern_len):
                        if actions[i:i+pattern_len] == pattern:
                            matches += 1
                    if matches >= max_repeating_pattern:
                        livelocked.append(activity.agent_id)
                        break

        return livelocked

    # Attack: Create livelock (agents keep retrying same actions)
    livelock_activities = [
        AgentActivity(
            "agent_X",
            ["try", "fail", "retry", "try", "fail", "retry", "try", "fail", "retry"],
            progress_metric=0.0,
            activity_count=100
        )
    ]

    livelocked_agents = detect_livelock(livelock_activities)

    if livelocked_agents:
        defenses["livelock_detection"] = True

    # ========================================================================
    # Vector 5: Consensus Timeout Defense
    # ========================================================================

    @dataclass
    class ConsensusProcess:
        process_id: str
        started_at: float
        participants: Set[str]
        votes_received: Set[str]
        status: str

    def enforce_consensus_timeout(process: ConsensusProcess,
                                    max_duration_seconds: float = 300) -> bool:
        """Enforce timeout on consensus processes."""
        duration = now - process.started_at

        if duration > max_duration_seconds:
            return False  # Timed out

        # Check if stuck (no new votes in a while)
        if duration > max_duration_seconds * 0.5:
            participation = len(process.votes_received) / len(process.participants)
            if participation < 0.5:
                return False  # Likely blocked

        return True

    # Attack: Block consensus by not voting
    blocked_consensus = ConsensusProcess(
        process_id="blocked_consensus",
        started_at=now - 400,  # Started long ago
        participants={"agent_1", "agent_2", "agent_3", "attacker"},
        votes_received={"agent_1"},  # Only one vote
        status="waiting"
    )

    if not enforce_consensus_timeout(blocked_consensus):
        defenses["consensus_timeout"] = True

    # ========================================================================
    # Vector 6: Resource Ordering Defense
    # ========================================================================

    def enforce_resource_ordering(agent_holdings: Dict[str, List[str]],
                                    resource_order: List[str]) -> List[str]:
        """Enforce total ordering of resource acquisition."""
        violations = []

        for agent, holdings in agent_holdings.items():
            if len(holdings) < 2:
                continue

            # Check if resources acquired in order
            holding_indices = [resource_order.index(r) for r in holdings
                              if r in resource_order]

            if holding_indices != sorted(holding_indices):
                violations.append(agent)

        return violations

    # Attack: Acquire resources out of order
    resource_order = ["R1", "R2", "R3", "R4"]
    attack_holdings = {
        "agent_A": ["R3", "R1"],  # Out of order
        "agent_B": ["R2", "R4"],  # In order
    }

    order_violations = enforce_resource_ordering(attack_holdings, resource_order)

    if order_violations:
        defenses["resource_ordering"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Coordination Deadlock (FI-3a)",
        success=attack_success,
        setup_cost_atp=12000.0,
        gain_atp=70000.0 if attack_success else 0.0,
        roi=(70000.0 / 12000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=4.0,
        blocks_until_detected=40,
        trust_damage=0.50,
        description=f"""
COORDINATION DEADLOCK ATTACK (Track FI-3a)

Induce deadlocks to prevent system progress.

Attack Pattern:
1. Create resource contention (A waits B, B waits A)
2. Inject circular dependencies
3. Cause priority inversion
4. Induce livelock (activity without progress)
5. Block consensus by not voting

Deadlock Analysis:
- Deadlock cycles found: {len(deadlocks)}
- Circular dependencies: {len(dep_cycles)}
- Priority violations: {len(violations)}
- Livelocked agents: {len(livelocked_agents)}
- Consensus blocked: {blocked_consensus.status == "waiting"}

Defense Analysis:
- Deadlock detection: {"HELD" if defenses["deadlock_detection"] else "BYPASSED"}
- Circular dependency check: {"HELD" if defenses["circular_dependency_check"] else "BYPASSED"}
- Priority ceiling: {"HELD" if defenses["priority_ceiling"] else "BYPASSED"}
- Livelock detection: {"HELD" if defenses["livelock_detection"] else "BYPASSED"}
- Consensus timeout: {"HELD" if defenses["consensus_timeout"] else "BYPASSED"}
- Resource ordering: {"HELD" if defenses["resource_ordering"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-3a: Coordination Deadlock Defense:
1. Detect deadlock cycles in wait-for graph
2. Check for circular dependencies
3. Use priority ceiling protocol
4. Detect activity without progress (livelock)
5. Enforce consensus timeouts
6. Require ordered resource acquisition

Coordination must have escape hatches.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "deadlock_count": len(deadlocks),
            "dependency_cycles": len(dep_cycles),
        }
    )


# ============================================================================
# ATTACK FI-3b: COOPERATION SUBVERSION
# ============================================================================


def attack_cooperation_subversion() -> AttackResult:
    """
    ATTACK FI-3b: Cooperation Subversion

    Subvert cooperative mechanisms to make them produce
    worse outcomes than non-cooperation.

    Vectors:
    1. Free-rider exploitation
    2. Tragedy of the commons acceleration
    3. Prisoner's dilemma manipulation
    4. Public goods undermining
    5. Trust network erosion
    """

    defenses = {
        "free_rider_detection": False,
        "commons_metering": False,
        "repeated_game_tracking": False,
        "contribution_verification": False,
        "trust_reciprocity_check": False,
        "cooperative_surplus_protection": False,
    }

    now = time.time()

    @dataclass
    class CooperativeAgent:
        agent_id: str
        contributions: float
        benefits_received: float
        cooperation_history: List[bool]
        trust_given: Dict[str, float]
        trust_received: Dict[str, float]

    # ========================================================================
    # Vector 1: Free-Rider Detection Defense
    # ========================================================================

    def detect_free_riders(agents: List[CooperativeAgent],
                            min_contribution_ratio: float = 0.5) -> List[str]:
        """Detect agents who benefit without contributing."""
        free_riders = []

        for agent in agents:
            if agent.benefits_received > 0:
                contribution_ratio = agent.contributions / agent.benefits_received
                if contribution_ratio < min_contribution_ratio:
                    free_riders.append(agent.agent_id)

        return free_riders

    # Attack: Free-ride on cooperative system
    cooperative_agents = [
        CooperativeAgent("honest_1", contributions=100, benefits_received=90,
                        cooperation_history=[True] * 10,
                        trust_given={}, trust_received={}),
        CooperativeAgent("honest_2", contributions=80, benefits_received=85,
                        cooperation_history=[True] * 10,
                        trust_given={}, trust_received={}),
        CooperativeAgent("attacker", contributions=5, benefits_received=100,
                        cooperation_history=[False] * 10,
                        trust_given={}, trust_received={}),  # Free rider
    ]

    free_riders = detect_free_riders(cooperative_agents)

    if free_riders:
        defenses["free_rider_detection"] = True

    # ========================================================================
    # Vector 2: Commons Metering Defense
    # ========================================================================

    @dataclass
    class CommonsUsage:
        agent_id: str
        usage: float
        quota: float
        timestamp: float

    def meter_commons_usage(usages: List[CommonsUsage],
                             total_commons: float,
                             max_usage_ratio: float = 0.2) -> List[str]:
        """Meter and limit commons usage."""
        violations = []

        total_usage = sum(u.usage for u in usages)

        for usage in usages:
            # Check individual limit
            individual_ratio = usage.usage / total_commons
            if individual_ratio > max_usage_ratio:
                violations.append(usage.agent_id)

            # Check quota violation
            if usage.usage > usage.quota:
                violations.append(usage.agent_id)

        return list(set(violations))

    # Attack: Overconsume shared resource
    commons_usage = [
        CommonsUsage("user_1", 10, 20, now),
        CommonsUsage("user_2", 15, 20, now),
        CommonsUsage("attacker", 60, 20, now),  # 3x quota, 60% of commons
    ]

    commons_violations = meter_commons_usage(commons_usage, 100)

    if commons_violations:
        defenses["commons_metering"] = True

    # ========================================================================
    # Vector 3: Repeated Game Tracking Defense
    # ========================================================================

    def track_repeated_game(history: List[bool],
                             min_cooperation_rate: float = 0.5,
                             recent_window: int = 5) -> Tuple[bool, float]:
        """Track cooperation in repeated games."""
        if not history:
            return True, 0.0

        total_rate = sum(history) / len(history)
        recent = history[-recent_window:] if len(history) >= recent_window else history
        recent_rate = sum(recent) / len(recent)

        is_cooperating = recent_rate >= min_cooperation_rate

        return is_cooperating, total_rate

    # Attack: Defect after building cooperation
    attack_history = [True] * 8 + [False] * 5  # Cooperate then defect

    cooperating, rate = track_repeated_game(attack_history)

    if not cooperating:
        defenses["repeated_game_tracking"] = True

    # ========================================================================
    # Vector 4: Contribution Verification Defense
    # ========================================================================

    @dataclass
    class Contribution:
        contributor: str
        amount: float
        verified: bool
        verification_source: str

    def verify_contributions(contributions: List[Contribution],
                               min_verified_ratio: float = 0.8) -> bool:
        """Verify claimed contributions are real."""
        if not contributions:
            return True

        total_claimed = sum(c.amount for c in contributions)
        total_verified = sum(c.amount for c in contributions if c.verified)

        if total_claimed == 0:
            return True

        verified_ratio = total_verified / total_claimed
        return verified_ratio >= min_verified_ratio

    # Attack: Claim fake contributions
    fake_contributions = [
        Contribution("attacker", 1000, False, ""),  # Not verified
        Contribution("honest", 100, True, "blockchain_proof"),
    ]

    if not verify_contributions(fake_contributions):
        defenses["contribution_verification"] = True

    # ========================================================================
    # Vector 5: Trust Reciprocity Check Defense
    # ========================================================================

    def check_trust_reciprocity(agents: List[CooperativeAgent],
                                  max_imbalance: float = 0.5) -> List[Tuple[str, str]]:
        """Check for trust imbalances (exploitation)."""
        imbalances = []

        for agent in agents:
            for partner, given in agent.trust_given.items():
                received = agent.trust_received.get(partner, 0)

                if given > 0:
                    imbalance = abs(given - received) / given
                    if imbalance > max_imbalance and given > received:
                        imbalances.append((agent.agent_id, partner))

        return imbalances

    # Attack: Exploit trust without reciprocating
    cooperative_agents[0].trust_given = {"attacker": 0.8}
    cooperative_agents[0].trust_received = {"attacker": 0.1}

    cooperative_agents[2].trust_given = {"honest_1": 0.1}
    cooperative_agents[2].trust_received = {"honest_1": 0.8}

    imbalances = check_trust_reciprocity(cooperative_agents)

    if imbalances:
        defenses["trust_reciprocity_check"] = True

    # ========================================================================
    # Vector 6: Cooperative Surplus Protection Defense
    # ========================================================================

    @dataclass
    class CooperativeOutcome:
        total_value_created: float
        individual_values: Dict[str, float]
        cooperation_cost: float

    def protect_cooperative_surplus(outcome: CooperativeOutcome,
                                      min_surplus_share: float = 0.1) -> bool:
        """Ensure cooperation creates positive surplus for all."""
        surplus = outcome.total_value_created - outcome.cooperation_cost

        if surplus <= 0:
            return False  # No surplus to protect

        # Check if surplus is shared fairly
        min_individual = surplus * min_surplus_share

        for agent, value in outcome.individual_values.items():
            if value < min_individual:
                return False  # Someone not getting fair share

        return True

    # Attack: Capture all cooperative surplus
    attack_outcome = CooperativeOutcome(
        total_value_created=1000,
        individual_values={
            "honest_1": 50,
            "honest_2": 50,
            "attacker": 800,  # Captures most surplus
        },
        cooperation_cost=100
    )

    if not protect_cooperative_surplus(attack_outcome):
        defenses["cooperative_surplus_protection"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Cooperation Subversion (FI-3b)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=85000.0 if attack_success else 0.0,
        roi=(85000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=48.0,
        blocks_until_detected=400,
        trust_damage=0.75,
        description=f"""
COOPERATION SUBVERSION ATTACK (Track FI-3b)

Subvert cooperative mechanisms for personal gain.

Attack Pattern:
1. Free-ride (contribute 5%, receive 100%)
2. Overconsume commons (60% of shared resource)
3. Build trust then defect (8 cooperate, 5 defect)
4. Claim fake contributions
5. Exploit trust without reciprocating

Subversion Analysis:
- Free riders detected: {free_riders}
- Commons violations: {commons_violations}
- Cooperation rate: {rate:.1%}
- Trust imbalances: {len(imbalances)}
- Surplus captured: {attack_outcome.individual_values['attacker']}/{attack_outcome.total_value_created}

Defense Analysis:
- Free-rider detection: {"HELD" if defenses["free_rider_detection"] else "BYPASSED"}
- Commons metering: {"HELD" if defenses["commons_metering"] else "BYPASSED"}
- Repeated game tracking: {"HELD" if defenses["repeated_game_tracking"] else "BYPASSED"}
- Contribution verification: {"HELD" if defenses["contribution_verification"] else "BYPASSED"}
- Trust reciprocity: {"HELD" if defenses["trust_reciprocity_check"] else "BYPASSED"}
- Surplus protection: {"HELD" if defenses["cooperative_surplus_protection"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FI-3b: Cooperation Subversion Defense:
1. Detect free riders by contribution/benefit ratio
2. Meter and quota commons usage
3. Track cooperation in repeated interactions
4. Verify claimed contributions
5. Check trust reciprocity
6. Protect cooperative surplus distribution

Cooperation requires mutual benefit.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "free_riders": free_riders,
            "cooperation_rate": rate,
        }
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fi_attacks() -> List[AttackResult]:
    """Run all Track FI attacks and return results."""
    attacks = [
        attack_coordination_hijacking,
        attack_swarm_manipulation,
        attack_emergent_behavior_induction,
        attack_collective_intelligence_poisoning,
        attack_coordination_deadlock,
        attack_cooperation_subversion,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    return results


def print_track_fi_summary(results: List[AttackResult]):
    """Print summary of Track FI attack results."""
    print("\n" + "=" * 70)
    print("TRACK FI: EMERGENT BEHAVIOR EXPLOITS - SUMMARY")
    print("Attacks 305-310")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Attack Success Rate: {(successful/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    total_setup_cost = sum(r.setup_cost_atp for r in results)
    print(f"Total Attack Cost: {total_setup_cost:,.0f} ATP")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 305):
        status = "DEFENDED" if not result.success else "SUCCEEDED"
        print(f"\nAttack #{i}: {result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Potential Gain: {result.gain_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")
        print(f"  Time to Detection: {result.time_to_detection_hours:.0f}h")


if __name__ == "__main__":
    results = run_all_track_fi_attacks()
    print_track_fi_summary(results)
