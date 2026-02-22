"""
Law Oracle Procedure Extensions — Reference Implementation

Implements RFC-LAW-PROC-001:
- Time-based triggers: schedule, daily, interval, event, condition
- Multi-threshold logic: graduated responses based on computed values
- Failure actions: reject_transaction, flag_for_review, emergency_halt, notify_authority, escalate_to_quorum
- Immediate execution: emergency bypass of consensus with post-hoc audit
- Action mappings: threshold-to-action bindings for dynamic responses
- Procedure validation: trigger format, immediate+authority, threshold/action key matching
- R6 action grammar binding: r6.procedure.<id>.execute/trigger/validate
- Law dataset compliance: extended procedures in Web4LawDataset format
- Security: timing attack defense, threshold gaming detection, immediate execution audit

Key insight from RFC: "The minimal SAL procedure schema is insufficient for
time-based triggers, multi-threshold logic, and emergency bypass."

Spec: web4-standard/rfcs/RFC_LAW_ORACLE_PROCEDURES.md
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class TriggerType(Enum):
    """Trigger types per §1."""
    EVENT = "event"
    SCHEDULE = "schedule"
    CONDITION = "condition"
    INTERVAL = "interval"
    DAILY = "daily"


class FailureAction(Enum):
    """Standard failure actions per §3."""
    REJECT_TRANSACTION = "reject_transaction"
    FLAG_FOR_REVIEW = "flag_for_review"
    EMERGENCY_HALT = "emergency_halt"
    NOTIFY_AUTHORITY = "notify_authority"
    ESCALATE_TO_QUORUM = "escalate_to_quorum"


class ProcedureState(Enum):
    """Execution state of a procedure."""
    IDLE = "idle"
    TRIGGERED = "triggered"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


class ThresholdLevel(Enum):
    """Standard threshold levels per §2."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TriggerSpec:
    """Trigger specification per §1 TriggerObject."""
    trigger_type: TriggerType
    schedule: Optional[str] = None      # Cron expression
    time: Optional[str] = None          # ISO 8601 time (HH:MM:SSZ)
    timezone_str: Optional[str] = "UTC"
    event_name: Optional[str] = None
    condition: Optional[str] = None     # R6 selector
    interval: Optional[str] = None      # Duration (e.g., "90_days")

    @staticmethod
    def parse(trigger_str: str) -> 'TriggerSpec':
        """Parse simplified trigger string format."""
        if trigger_str.startswith("event:"):
            return TriggerSpec(trigger_type=TriggerType.EVENT,
                               event_name=trigger_str[6:])
        elif trigger_str.startswith("schedule:"):
            return TriggerSpec(trigger_type=TriggerType.SCHEDULE,
                               schedule=trigger_str[9:])
        elif trigger_str.startswith("daily_"):
            # daily_HH:MM_TZ
            parts = trigger_str[6:].rsplit("_", 1)
            time_str = parts[0] if parts else "00:00"
            tz = parts[1] if len(parts) > 1 else "utc"
            return TriggerSpec(trigger_type=TriggerType.DAILY,
                               time=time_str, timezone_str=tz.upper())
        elif trigger_str.startswith("interval_"):
            return TriggerSpec(trigger_type=TriggerType.INTERVAL,
                               interval=trigger_str[9:])
        elif trigger_str.startswith("condition:"):
            return TriggerSpec(trigger_type=TriggerType.CONDITION,
                               condition=trigger_str[10:])
        else:
            # Treat as event
            return TriggerSpec(trigger_type=TriggerType.EVENT,
                               event_name=trigger_str)

    def matches_event(self, event_name: str) -> bool:
        """Check if this trigger matches a given event."""
        if self.trigger_type == TriggerType.EVENT:
            return self.event_name == event_name
        return False

    def matches_time(self, current_time: datetime) -> bool:
        """Check if trigger fires at given time (daily triggers)."""
        if self.trigger_type == TriggerType.DAILY and self.time:
            parts = self.time.replace(":", "")
            try:
                hour = int(parts[:2])
                minute = int(parts[2:4]) if len(parts) >= 4 else 0
                return (current_time.hour == hour and
                        current_time.minute == minute)
            except (ValueError, IndexError):
                return False
        return False

    def matches_interval(self, last_execution: Optional[datetime],
                         now: datetime) -> bool:
        """Check if interval trigger should fire."""
        if self.trigger_type != TriggerType.INTERVAL or not self.interval:
            return False
        if last_execution is None:
            return True

        # Parse interval: "90_days", "24_hours", etc.
        match = re.match(r'(\d+)_(days?|hours?|minutes?)', self.interval)
        if not match:
            return False
        amount = int(match.group(1))
        unit = match.group(2).rstrip('s')  # Normalize
        if unit == "day":
            delta = timedelta(days=amount)
        elif unit == "hour":
            delta = timedelta(hours=amount)
        elif unit == "minute":
            delta = timedelta(minutes=amount)
        else:
            return False

        return (now - last_execution) >= delta


@dataclass
class ThresholdSpec:
    """Multi-threshold definition per §2."""
    levels: Dict[str, float]   # level_name → threshold_value
    actions: Dict[str, str]    # level_name → action_name

    def evaluate(self, value: float) -> Tuple[str, str]:
        """
        Evaluate value against thresholds.
        Returns: (matched_level, action)
        """
        # Sort levels by threshold value ascending
        sorted_levels = sorted(self.levels.items(), key=lambda x: x[1])

        matched_level = None
        matched_action = "continue_normal"

        for level_name, threshold in sorted_levels:
            if value >= threshold:
                matched_level = level_name
                matched_action = self.actions.get(level_name, "continue_normal")

        if matched_level is None:
            # Below all thresholds (or no thresholds defined)
            return ("below_threshold", "continue_normal")

        return (matched_level, matched_action)


@dataclass
class Procedure:
    """Extended procedure per RFC-LAW-PROC-001 §Complete Schema."""
    id: str
    name: str
    description: str = ""

    # Execution control
    trigger: Optional[TriggerSpec] = None
    immediate: bool = False
    authority: Optional[List[str]] = None

    # Witness requirements
    requires_witnesses: Any = None  # bool or int
    witness_types: Optional[List[str]] = None
    witness_count: Optional[int] = None

    # Logic and computation
    method: Optional[str] = None
    thresholds: Optional[ThresholdSpec] = None

    # Failure handling
    failure_action: Optional[FailureAction] = None

    # Additional parameters
    amount: Optional[float] = None
    targets: Optional[List[str]] = None
    cap: Optional[str] = None
    voting_period: Optional[str] = None
    veto_authority: Optional[List[str]] = None
    requires_quorum: Optional[int] = None
    total_participants: Optional[int] = None

    # References
    rfc: Optional[str] = None
    related_norms: Optional[List[str]] = None

    # State
    state: ProcedureState = ProcedureState.IDLE
    last_execution: Optional[datetime] = None
    execution_count: int = 0


@dataclass
class ExecutionRecord:
    """Audit record of a procedure execution."""
    procedure_id: str
    timestamp: datetime
    trigger_event: str
    authority_used: Optional[str]
    immediate: bool
    result: str  # "success", "failure", "halted"
    computed_value: Optional[float] = None
    matched_level: Optional[str] = None
    matched_action: Optional[str] = None
    failure_action_taken: Optional[str] = None
    witness_count: int = 0
    audit_hash: str = ""


@dataclass
class ValidationError:
    """Procedure validation error."""
    procedure_id: str
    field: str
    message: str
    severity: str = "error"  # "error" or "warning"


# ============================================================================
# PROCEDURE VALIDATOR
# ============================================================================

class ProcedureValidator:
    """Validate extended procedures per §Validation."""

    @staticmethod
    def validate(proc: Procedure) -> List[ValidationError]:
        """Validate a procedure for spec compliance."""
        errors = []

        # 1. ID must be non-empty
        if not proc.id:
            errors.append(ValidationError(
                proc.id, "id", "Procedure ID must not be empty"))

        # 2. Name must be non-empty
        if not proc.name:
            errors.append(ValidationError(
                proc.id, "name", "Procedure name must not be empty"))

        # 3. immediate: true requires authority
        if proc.immediate and not proc.authority:
            errors.append(ValidationError(
                proc.id, "authority",
                "immediate=true requires authority field"))

        # 4. Thresholds and actions must have matching keys
        if proc.thresholds:
            threshold_keys = set(proc.thresholds.levels.keys())
            action_keys = set(proc.thresholds.actions.keys())
            missing_actions = threshold_keys - action_keys
            if missing_actions:
                errors.append(ValidationError(
                    proc.id, "actions",
                    f"Missing actions for threshold levels: {missing_actions}"))
            extra_actions = action_keys - threshold_keys
            if extra_actions:
                errors.append(ValidationError(
                    proc.id, "actions",
                    f"Extra action keys without thresholds: {extra_actions}",
                    severity="warning"))

        # 5. Failure action must be recognized
        if proc.failure_action and not isinstance(proc.failure_action, FailureAction):
            errors.append(ValidationError(
                proc.id, "failureAction",
                f"Unrecognized failure action: {proc.failure_action}"))

        # 6. Quorum requires total participants
        if proc.requires_quorum and not proc.total_participants:
            errors.append(ValidationError(
                proc.id, "totalParticipants",
                "requiresQuorum specified without totalParticipants",
                severity="warning"))

        # 7. Quorum must be ≤ total
        if (proc.requires_quorum and proc.total_participants and
                proc.requires_quorum > proc.total_participants):
            errors.append(ValidationError(
                proc.id, "requiresQuorum",
                f"Quorum {proc.requires_quorum} > total {proc.total_participants}"))

        return errors


# ============================================================================
# PROCEDURE EXECUTOR
# ============================================================================

class ProcedureExecutor:
    """Execute procedures with full audit trail."""

    def __init__(self):
        self.execution_log: List[ExecutionRecord] = []
        self.methods: Dict[str, Callable] = {}
        self._hash_chain: str = "genesis"

    def register_method(self, name: str, func: Callable):
        """Register a computation method."""
        self.methods[name] = func

    def execute(self, proc: Procedure, trigger_event: str,
                context: Optional[Dict] = None,
                authority: Optional[str] = None,
                now: Optional[datetime] = None) -> ExecutionRecord:
        """Execute a procedure and return audit record."""
        ts = now or datetime.now(timezone.utc)
        context = context or {}

        # Check authority for immediate procedures
        if proc.immediate:
            if not authority or (proc.authority and authority not in proc.authority):
                record = self._make_record(
                    proc, ts, trigger_event, authority,
                    result="failure",
                    failure_action_taken="unauthorized_immediate")
                self.execution_log.append(record)
                return record

        # Compute value if method specified
        computed_value = None
        matched_level = None
        matched_action = None

        if proc.method and proc.method in self.methods:
            computed_value = self.methods[proc.method](context)

            # Evaluate thresholds
            if proc.thresholds and computed_value is not None:
                matched_level, matched_action = proc.thresholds.evaluate(
                    computed_value)

        # Execute targets (e.g., ATP recharge)
        result = "success"
        failure_action_taken = None

        # Simulate method failure
        if context.get("simulate_failure"):
            result = "failure"
            if proc.failure_action:
                failure_action_taken = proc.failure_action.value
                if proc.failure_action == FailureAction.EMERGENCY_HALT:
                    proc.state = ProcedureState.HALTED

        # Update procedure state (preserve HALTED if set during failure handling)
        if proc.state != ProcedureState.HALTED:
            proc.state = ProcedureState.COMPLETED if result == "success" else ProcedureState.FAILED
        proc.last_execution = ts
        proc.execution_count += 1

        record = self._make_record(
            proc, ts, trigger_event, authority,
            result=result,
            computed_value=computed_value,
            matched_level=matched_level,
            matched_action=matched_action,
            failure_action_taken=failure_action_taken)

        self.execution_log.append(record)
        return record

    def _make_record(self, proc: Procedure, ts: datetime,
                     trigger_event: str, authority: Optional[str],
                     result: str, computed_value: Optional[float] = None,
                     matched_level: Optional[str] = None,
                     matched_action: Optional[str] = None,
                     failure_action_taken: Optional[str] = None) -> ExecutionRecord:
        """Create an audit record with hash chain."""
        record = ExecutionRecord(
            procedure_id=proc.id,
            timestamp=ts,
            trigger_event=trigger_event,
            authority_used=authority,
            immediate=proc.immediate,
            result=result,
            computed_value=computed_value,
            matched_level=matched_level,
            matched_action=matched_action,
            failure_action_taken=failure_action_taken)

        # Hash chain
        content = f"{self._hash_chain}:{proc.id}:{ts.isoformat()}:{result}"
        record.audit_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        self._hash_chain = record.audit_hash

        return record


# ============================================================================
# TRIGGER SCHEDULER
# ============================================================================

class TriggerScheduler:
    """Schedule and evaluate triggers."""

    def __init__(self):
        self.procedures: Dict[str, Procedure] = {}
        self._last_check: Dict[str, datetime] = {}

    def register(self, proc: Procedure):
        """Register a procedure for trigger evaluation."""
        self.procedures[proc.id] = proc

    def check_event(self, event_name: str) -> List[str]:
        """Check which procedures are triggered by an event."""
        triggered = []
        for pid, proc in self.procedures.items():
            if proc.trigger and proc.trigger.matches_event(event_name):
                triggered.append(pid)
        return triggered

    def check_time(self, current_time: datetime) -> List[str]:
        """Check which procedures should fire at given time."""
        triggered = []
        for pid, proc in self.procedures.items():
            if proc.trigger and proc.trigger.matches_time(current_time):
                triggered.append(pid)
        return triggered

    def check_intervals(self, now: datetime) -> List[str]:
        """Check which interval-based procedures should fire."""
        triggered = []
        for pid, proc in self.procedures.items():
            if (proc.trigger and
                    proc.trigger.matches_interval(proc.last_execution, now)):
                triggered.append(pid)
        return triggered


# ============================================================================
# R6 ACTION GRAMMAR BINDING
# ============================================================================

class R6Binding:
    """Map procedures to R6 action selectors per §R6."""

    @staticmethod
    def execute_selector(proc_id: str) -> str:
        return f"r6.procedure.{proc_id}.execute"

    @staticmethod
    def trigger_selector(proc_id: str) -> str:
        return f"r6.procedure.{proc_id}.trigger"

    @staticmethod
    def validate_selector(proc_id: str) -> str:
        return f"r6.procedure.{proc_id}.validate"

    @staticmethod
    def parse_selector(selector: str) -> Optional[Tuple[str, str]]:
        """Parse R6 selector into (procedure_id, action)."""
        match = re.match(r'r6\.procedure\.([^.]+)\.(execute|trigger|validate)',
                         selector)
        if match:
            return (match.group(1), match.group(2))
        return None


# ============================================================================
# LAW DATASET COMPLIANCE
# ============================================================================

class LawDatasetBuilder:
    """Build Web4LawDataset with extended procedures per §LawDataset."""

    def __init__(self, dataset_id: str, version: str = "1.0.0"):
        self.dataset_id = dataset_id
        self.version = version
        self.procedures: List[Dict] = []
        self.extensions: List[str] = []

    def add_procedure(self, proc: Procedure):
        """Add procedure to dataset in JSON format."""
        d: Dict[str, Any] = {
            "id": proc.id,
            "name": proc.name,
        }
        if proc.description:
            d["description"] = proc.description
        if proc.trigger:
            if proc.trigger.trigger_type == TriggerType.DAILY:
                d["trigger"] = f"daily_{proc.trigger.time}_{proc.trigger.timezone_str.lower()}"
            elif proc.trigger.trigger_type == TriggerType.EVENT:
                d["trigger"] = proc.trigger.event_name
            elif proc.trigger.trigger_type == TriggerType.INTERVAL:
                d["trigger"] = f"interval_{proc.trigger.interval}"
            else:
                d["trigger"] = {
                    "type": proc.trigger.trigger_type.value,
                }
        if proc.immediate:
            d["immediate"] = True
        if proc.authority:
            d["authority"] = proc.authority[0] if len(proc.authority) == 1 else proc.authority
        if proc.requires_witnesses is not None:
            d["requiresWitnesses"] = proc.requires_witnesses
        if proc.method:
            d["method"] = proc.method
        if proc.thresholds:
            d["thresholds"] = proc.thresholds.levels
            d["actions"] = proc.thresholds.actions
        if proc.failure_action:
            d["failureAction"] = proc.failure_action.value
        if proc.amount is not None:
            d["amount"] = proc.amount
        if proc.targets:
            d["targets"] = proc.targets
        if proc.rfc:
            d["rfc"] = proc.rfc
        if proc.requires_quorum:
            d["requiresQuorum"] = proc.requires_quorum
        if proc.total_participants:
            d["totalQueens"] = proc.total_participants
        if proc.voting_period:
            d["votingPeriod"] = proc.voting_period
        if proc.veto_authority:
            d["vetoAuthority"] = proc.veto_authority

        self.procedures.append(d)

    def build(self) -> Dict:
        """Build the complete law dataset."""
        has_extensions = any(
            p.get("trigger") or p.get("immediate") or p.get("thresholds")
            for p in self.procedures)

        result = {
            "@context": ["https://web4.io/contexts/law.jsonld"],
            "type": "Web4LawDataset",
            "id": self.dataset_id,
            "version": self.version,
            "complianceLevel": "web4-core-v1.0",
            "procedures": self.procedures,
        }
        if has_extensions:
            result["extensions"] = ["law-oracle-procedures-v1"]

        return result


# ============================================================================
# SECURITY
# ============================================================================

class TimingAttackDetector:
    """Detect timing attacks on scheduled procedures per §Security.timing."""

    def __init__(self, max_clock_skew_seconds: float = 5.0):
        self.max_clock_skew = max_clock_skew_seconds
        self._trigger_times: List[datetime] = []

    def validate_trigger_time(self, expected: datetime,
                               actual: datetime) -> bool:
        """Check if trigger time is within acceptable skew."""
        skew = abs((actual - expected).total_seconds())
        return skew <= self.max_clock_skew

    def detect_manipulation(self, trigger_times: List[datetime],
                            expected_interval_seconds: float) -> bool:
        """Detect suspicious trigger timing patterns."""
        if len(trigger_times) < 3:
            return False

        intervals = []
        for i in range(1, len(trigger_times)):
            delta = (trigger_times[i] - trigger_times[i-1]).total_seconds()
            intervals.append(delta)

        # Check for suspicious regularity or irregularity
        avg = sum(intervals) / len(intervals)
        variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)

        # Too regular (potential replay) or too irregular (potential manipulation)
        # Expected variance should be small but not zero
        if variance == 0 and len(intervals) >= 3:
            return True  # Suspiciously perfect timing
        if variance > expected_interval_seconds ** 2:
            return True  # Too irregular

        return False


class ThresholdGamingDetector:
    """Detect threshold gaming per §Security.thresholds."""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._value_history: Dict[str, List[float]] = {}

    def record_value(self, proc_id: str, value: float):
        """Record a computed value."""
        if proc_id not in self._value_history:
            self._value_history[proc_id] = []
        self._value_history[proc_id].append(value)
        # Keep window
        if len(self._value_history[proc_id]) > self.window_size:
            self._value_history[proc_id] = self._value_history[proc_id][-self.window_size:]

    def detect_gaming(self, proc_id: str,
                       thresholds: ThresholdSpec) -> bool:
        """Detect if values cluster just below thresholds (gaming)."""
        if proc_id not in self._value_history:
            return False

        values = self._value_history[proc_id]
        if len(values) < 3:
            return False

        threshold_values = sorted(thresholds.levels.values())
        margin = 0.05  # Values within 5% below threshold are suspicious

        for tv in threshold_values:
            # Count values just below threshold
            just_below = sum(1 for v in values if (tv - margin) <= v < tv)
            if just_below >= len(values) * 0.6:  # 60% of values cluster below
                return True

        return False


# ============================================================================
# TESTS
# ============================================================================

def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    passed = 0
    total = 0

    def t(label, condition):
        nonlocal passed, total
        total += 1
        if check(label, condition):
            passed += 1

    now = datetime(2026, 2, 22, 0, 0, 0, tzinfo=timezone.utc)

    # ================================================================
    # T1: Trigger parsing
    # ================================================================
    print("T1: Trigger Parsing")
    t1 = TriggerSpec.parse("event:security_breach_detected")
    t("T1.1 Event trigger type", t1.trigger_type == TriggerType.EVENT)
    t("T1.2 Event name parsed", t1.event_name == "security_breach_detected")

    t2 = TriggerSpec.parse("daily_00:00_utc")
    t("T1.3 Daily trigger type", t2.trigger_type == TriggerType.DAILY)
    t("T1.4 Time parsed", t2.time == "00:00")
    t("T1.5 Timezone parsed", t2.timezone_str == "UTC")

    t3 = TriggerSpec.parse("interval_90_days")
    t("T1.6 Interval trigger type", t3.trigger_type == TriggerType.INTERVAL)
    t("T1.7 Interval parsed", t3.interval == "90_days")

    t4 = TriggerSpec.parse("schedule:0 0 * * *")
    t("T1.8 Schedule trigger type", t4.trigger_type == TriggerType.SCHEDULE)
    t("T1.9 Cron parsed", t4.schedule == "0 0 * * *")

    t5 = TriggerSpec.parse("condition:r6.trust.below_threshold")
    t("T1.10 Condition trigger type", t5.trigger_type == TriggerType.CONDITION)
    t("T1.11 Condition parsed", t5.condition == "r6.trust.below_threshold")

    # ================================================================
    # T2: Event matching
    # ================================================================
    print("T2: Event Matching")
    trigger = TriggerSpec.parse("event:network_state_change")
    t("T2.1 Matches correct event",
      trigger.matches_event("network_state_change"))
    t("T2.2 Doesn't match wrong event",
      not trigger.matches_event("security_breach"))

    # ================================================================
    # T3: Daily time matching
    # ================================================================
    print("T3: Daily Time Matching")
    daily = TriggerSpec.parse("daily_00:00_utc")
    midnight = datetime(2026, 2, 22, 0, 0, 0, tzinfo=timezone.utc)
    noon = datetime(2026, 2, 22, 12, 0, 0, tzinfo=timezone.utc)
    t("T3.1 Matches midnight", daily.matches_time(midnight))
    t("T3.2 Doesn't match noon", not daily.matches_time(noon))

    daily2 = TriggerSpec.parse("daily_14:30_utc")
    t230 = datetime(2026, 2, 22, 14, 30, 0, tzinfo=timezone.utc)
    t("T3.3 Matches 14:30", daily2.matches_time(t230))

    # ================================================================
    # T4: Interval matching
    # ================================================================
    print("T4: Interval Matching")
    interval = TriggerSpec.parse("interval_90_days")
    last_exec = now - timedelta(days=100)
    t("T4.1 Fires after interval elapsed",
      interval.matches_interval(last_exec, now))

    recent = now - timedelta(days=10)
    t("T4.2 Doesn't fire before interval",
      not interval.matches_interval(recent, now))

    t("T4.3 Fires if never executed",
      interval.matches_interval(None, now))

    # Hours interval
    hourly = TriggerSpec.parse("interval_24_hours")
    last_h = now - timedelta(hours=25)
    t("T4.4 Hourly interval fires", hourly.matches_interval(last_h, now))

    # ================================================================
    # T5: Threshold evaluation
    # ================================================================
    print("T5: Threshold Evaluation")
    thresholds = ThresholdSpec(
        levels={"low": 0.3, "medium": 0.6, "high": 0.8},
        actions={"low": "continue_normal", "medium": "additional_validation",
                 "high": "witness_request"})

    level, action = thresholds.evaluate(0.1)
    t("T5.1 Below all → below_threshold", level == "below_threshold")
    t("T5.2 Below all → continue", action == "continue_normal")

    level, action = thresholds.evaluate(0.4)
    t("T5.3 0.4 → low level", level == "low")
    t("T5.4 0.4 → continue_normal", action == "continue_normal")

    level, action = thresholds.evaluate(0.7)
    t("T5.5 0.7 → medium level", level == "medium")
    t("T5.6 0.7 → additional_validation", action == "additional_validation")

    level, action = thresholds.evaluate(0.9)
    t("T5.7 0.9 → high level", level == "high")
    t("T5.8 0.9 → witness_request", action == "witness_request")

    # Exact threshold
    level, action = thresholds.evaluate(0.3)
    t("T5.9 Exact threshold → matches", level == "low")

    # ================================================================
    # T6: Procedure creation — Society 4 procedures
    # ================================================================
    print("T6: Society 4 Procedures")

    # PROC-WIT-3: Minimal baseline
    proc_wit = Procedure(id="PROC-WIT-3", name="Minimum Witness Requirement",
                         requires_witnesses=3)
    t("T6.1 Minimal procedure valid", proc_wit.id == "PROC-WIT-3")
    t("T6.2 Witnesses = 3", proc_wit.requires_witnesses == 3)

    # PROC-EMERGENCY
    proc_emergency = Procedure(
        id="PROC-EMERGENCY", name="Emergency Halt Procedure",
        trigger=TriggerSpec.parse("event:security_breach_detected"),
        authority=["security_queen"],
        requires_witnesses=False,
        immediate=True,
        description="Security Queen can immediately halt without quorum")
    t("T6.3 Emergency is immediate", proc_emergency.immediate)
    t("T6.4 Authority = security_queen",
      proc_emergency.authority == ["security_queen"])

    # PROC-ATP-RECHARGE
    proc_recharge = Procedure(
        id="PROC-ATP-RECHARGE", name="Daily ATP Regeneration",
        trigger=TriggerSpec.parse("daily_00:00_utc"),
        amount=20, targets=["all_queens"], cap="initial_allocation")
    t("T6.5 Recharge amount = 20", proc_recharge.amount == 20)
    t("T6.6 Targets = all queens", "all_queens" in proc_recharge.targets)

    # PROC-TEMPORAL-AUTH
    proc_temporal = Procedure(
        id="PROC-TEMPORAL-AUTH", name="Temporal Authentication Check",
        trigger=TriggerSpec.parse("event:network_state_change"),
        method="compute_surprise_factor",
        thresholds=ThresholdSpec(
            levels={"low": 0.3, "medium": 0.6, "high": 0.8},
            actions={"low": "continue_normal", "medium": "additional_validation",
                     "high": "witness_request"}),
        rfc="RFC-TEMP-AUTH-001")
    t("T6.7 Has method", proc_temporal.method == "compute_surprise_factor")
    t("T6.8 Has thresholds", proc_temporal.thresholds is not None)
    t("T6.9 References RFC", proc_temporal.rfc == "RFC-TEMP-AUTH-001")

    # PROC-HARDWARE-VERIFY
    proc_hw = Procedure(
        id="PROC-HARDWARE-VERIFY", name="Hardware Binding Verification",
        trigger=TriggerSpec.parse("event:every_critical_operation"),
        method="extract_and_compare_hash",
        failure_action=FailureAction.REJECT_TRANSACTION)
    t("T6.10 Failure action = reject",
      proc_hw.failure_action == FailureAction.REJECT_TRANSACTION)

    # PROC-QUEEN-CONSENSUS
    proc_consensus = Procedure(
        id="PROC-QUEEN-CONSENSUS", name="Queens Quorum Voting",
        requires_quorum=5, total_participants=8,
        voting_period="48_hours",
        veto_authority=["security_queen"])
    t("T6.11 Quorum = 5", proc_consensus.requires_quorum == 5)
    t("T6.12 Total = 8", proc_consensus.total_participants == 8)

    # ================================================================
    # T7: Procedure validation
    # ================================================================
    print("T7: Validation")
    # Valid minimal procedure
    errors = ProcedureValidator.validate(proc_wit)
    t("T7.1 Minimal procedure valid", len(errors) == 0)

    # Valid emergency procedure
    errors = ProcedureValidator.validate(proc_emergency)
    t("T7.2 Emergency valid", len(errors) == 0)

    # Invalid: immediate without authority
    bad_proc = Procedure(id="BAD-1", name="Bad Proc", immediate=True)
    errors = ProcedureValidator.validate(bad_proc)
    t("T7.3 Immediate without authority fails",
      any(e.field == "authority" for e in errors))

    # Invalid: missing threshold actions
    bad_thresh = Procedure(
        id="BAD-2", name="Bad Thresh",
        thresholds=ThresholdSpec(
            levels={"low": 0.3, "high": 0.8},
            actions={"low": "continue"}))  # Missing "high"
    errors = ProcedureValidator.validate(bad_thresh)
    t("T7.4 Missing action keys detected",
      any(e.field == "actions" for e in errors))

    # Invalid: quorum > total
    bad_quorum = Procedure(
        id="BAD-3", name="Bad Quorum",
        requires_quorum=10, total_participants=5)
    errors = ProcedureValidator.validate(bad_quorum)
    t("T7.5 Quorum > total detected",
      any(e.field == "requiresQuorum" for e in errors))

    # Warning: quorum without total
    warn_quorum = Procedure(id="WARN-1", name="Warn", requires_quorum=3)
    errors = ProcedureValidator.validate(warn_quorum)
    t("T7.6 Warning for quorum without total",
      any(e.severity == "warning" for e in errors))

    # Empty ID
    bad_id = Procedure(id="", name="No ID")
    errors = ProcedureValidator.validate(bad_id)
    t("T7.7 Empty ID fails", any(e.field == "id" for e in errors))

    # ================================================================
    # T8: Procedure execution
    # ================================================================
    print("T8: Execution")
    executor = ProcedureExecutor()

    # Execute simple procedure
    record = executor.execute(proc_wit, "manual_trigger", now=now)
    t("T8.1 Execution succeeds", record.result == "success")
    t("T8.2 Procedure ID logged", record.procedure_id == "PROC-WIT-3")
    t("T8.3 Audit hash present", len(record.audit_hash) > 0)
    t("T8.4 Execution count updated", proc_wit.execution_count == 1)

    # Execute emergency — authorized
    record2 = executor.execute(
        proc_emergency, "security_breach_detected",
        authority="security_queen", now=now)
    t("T8.5 Emergency succeeds with authority", record2.result == "success")
    t("T8.6 Immediate logged", record2.immediate)

    # Execute emergency — unauthorized
    record3 = executor.execute(
        proc_emergency, "security_breach_detected",
        authority="data_queen", now=now)
    t("T8.7 Emergency fails without authority", record3.result == "failure")

    # ================================================================
    # T9: Method execution with thresholds
    # ================================================================
    print("T9: Method + Thresholds")
    executor2 = ProcedureExecutor()
    executor2.register_method("compute_surprise_factor",
                               lambda ctx: ctx.get("surprise", 0.0))

    # Low surprise
    r1 = executor2.execute(proc_temporal, "network_state_change",
                            context={"surprise": 0.2}, now=now)
    t("T9.1 Low surprise → below_threshold", r1.matched_level == "below_threshold")
    t("T9.2 Low surprise → continue", r1.matched_action == "continue_normal")

    # Medium surprise
    r2 = executor2.execute(proc_temporal, "network_state_change",
                            context={"surprise": 0.5}, now=now)
    t("T9.3 Medium surprise → low level", r2.matched_level == "low")

    # High surprise
    r3 = executor2.execute(proc_temporal, "network_state_change",
                            context={"surprise": 0.85}, now=now)
    t("T9.4 High surprise → high level", r3.matched_level == "high")
    t("T9.5 High surprise → witness_request", r3.matched_action == "witness_request")

    # ================================================================
    # T10: Failure handling
    # ================================================================
    print("T10: Failure Handling")
    executor3 = ProcedureExecutor()

    # Normal failure → reject
    proc_fail = Procedure(
        id="FAIL-1", name="Fail Test",
        failure_action=FailureAction.REJECT_TRANSACTION)
    r = executor3.execute(proc_fail, "test",
                           context={"simulate_failure": True}, now=now)
    t("T10.1 Failure detected", r.result == "failure")
    t("T10.2 Reject action taken", r.failure_action_taken == "reject_transaction")

    # Emergency halt
    proc_halt = Procedure(
        id="HALT-1", name="Halt Test",
        failure_action=FailureAction.EMERGENCY_HALT)
    r2 = executor3.execute(proc_halt, "test",
                            context={"simulate_failure": True}, now=now)
    t("T10.3 Halt action taken", r2.failure_action_taken == "emergency_halt")
    t("T10.4 Procedure state = HALTED",
      proc_halt.state == ProcedureState.HALTED)

    # All failure actions exist
    t("T10.5 All 5 failure actions",
      len(FailureAction) == 5)

    # ================================================================
    # T11: Trigger scheduler
    # ================================================================
    print("T11: Trigger Scheduler")
    scheduler = TriggerScheduler()
    scheduler.register(proc_emergency)
    scheduler.register(proc_recharge)
    scheduler.register(proc_temporal)

    # Event triggers
    triggered = scheduler.check_event("security_breach_detected")
    t("T11.1 Emergency triggered by event", "PROC-EMERGENCY" in triggered)
    t("T11.2 Recharge not triggered by event",
      "PROC-ATP-RECHARGE" not in triggered)

    triggered2 = scheduler.check_event("network_state_change")
    t("T11.3 Temporal auth triggered", "PROC-TEMPORAL-AUTH" in triggered2)

    # Time triggers
    midnight = datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone.utc)
    triggered3 = scheduler.check_time(midnight)
    t("T11.4 Recharge at midnight", "PROC-ATP-RECHARGE" in triggered3)

    noon = datetime(2026, 2, 23, 12, 0, 0, tzinfo=timezone.utc)
    triggered4 = scheduler.check_time(noon)
    t("T11.5 No triggers at noon", "PROC-ATP-RECHARGE" not in triggered4)

    # ================================================================
    # T12: R6 action grammar
    # ================================================================
    print("T12: R6 Binding")
    t("T12.1 Execute selector",
      R6Binding.execute_selector("PROC-WIT-3") == "r6.procedure.PROC-WIT-3.execute")
    t("T12.2 Trigger selector",
      R6Binding.trigger_selector("PROC-WIT-3") == "r6.procedure.PROC-WIT-3.trigger")
    t("T12.3 Validate selector",
      R6Binding.validate_selector("PROC-WIT-3") == "r6.procedure.PROC-WIT-3.validate")

    # Parse selector
    parsed = R6Binding.parse_selector("r6.procedure.PROC-EMERGENCY.execute")
    t("T12.4 Parsed procedure ID", parsed[0] == "PROC-EMERGENCY")
    t("T12.5 Parsed action", parsed[1] == "execute")

    invalid = R6Binding.parse_selector("not.a.valid.selector")
    t("T12.6 Invalid returns None", invalid is None)

    # ================================================================
    # T13: Law dataset builder
    # ================================================================
    print("T13: Law Dataset")
    builder = LawDatasetBuilder("law-oracle-society4", version="1.0.0")
    builder.add_procedure(proc_wit)
    builder.add_procedure(proc_emergency)
    builder.add_procedure(proc_recharge)
    builder.add_procedure(proc_temporal)
    builder.add_procedure(proc_hw)
    builder.add_procedure(proc_consensus)

    dataset = builder.build()
    t("T13.1 Has @context", "@context" in dataset)
    t("T13.2 Type is Web4LawDataset", dataset["type"] == "Web4LawDataset")
    t("T13.3 Has 6 procedures", len(dataset["procedures"]) == 6)
    t("T13.4 Has extensions", "law-oracle-procedures-v1" in dataset.get("extensions", []))
    t("T13.5 Compliance level set", dataset["complianceLevel"] == "web4-core-v1.0")

    # Check specific procedure serialization
    emergency_json = next(p for p in dataset["procedures"]
                          if p["id"] == "PROC-EMERGENCY")
    t("T13.6 Emergency has immediate", emergency_json.get("immediate") is True)
    t("T13.7 Emergency has authority", "authority" in emergency_json)

    temporal_json = next(p for p in dataset["procedures"]
                         if p["id"] == "PROC-TEMPORAL-AUTH")
    t("T13.8 Temporal has thresholds", "thresholds" in temporal_json)
    t("T13.9 Temporal has actions", "actions" in temporal_json)
    t("T13.10 Temporal has RFC ref", temporal_json.get("rfc") == "RFC-TEMP-AUTH-001")

    # ================================================================
    # T14: Audit trail hash chain
    # ================================================================
    print("T14: Audit Trail")
    executor4 = ProcedureExecutor()
    hashes = []
    for i in range(5):
        simple = Procedure(id=f"AUDIT-{i}", name=f"Audit Test {i}")
        r = executor4.execute(simple, "test", now=now + timedelta(seconds=i))
        hashes.append(r.audit_hash)

    t("T14.1 All hashes unique", len(set(hashes)) == 5)
    t("T14.2 All hashes non-empty", all(len(h) > 0 for h in hashes))
    t("T14.3 Log has 5 entries", len(executor4.execution_log) == 5)

    # ================================================================
    # T15: Timing attack detection
    # ================================================================
    print("T15: Timing Attack Detection")
    detector = TimingAttackDetector(max_clock_skew_seconds=5.0)

    expected = datetime(2026, 2, 22, 0, 0, 0, tzinfo=timezone.utc)
    actual_ok = datetime(2026, 2, 22, 0, 0, 3, tzinfo=timezone.utc)
    actual_bad = datetime(2026, 2, 22, 0, 0, 10, tzinfo=timezone.utc)

    t("T15.1 Within skew OK", detector.validate_trigger_time(expected, actual_ok))
    t("T15.2 Beyond skew fails",
      not detector.validate_trigger_time(expected, actual_bad))

    # Suspicious timing pattern (perfect regularity)
    perfect_times = [now + timedelta(seconds=i * 60) for i in range(5)]
    t("T15.3 Perfect timing → suspicious",
      detector.detect_manipulation(perfect_times, 60.0))

    # Normal variation
    normal_times = [now + timedelta(seconds=i * 60 + (i % 3) * 2) for i in range(5)]
    t("T15.4 Normal timing → not suspicious",
      not detector.detect_manipulation(normal_times, 60.0))

    # ================================================================
    # T16: Threshold gaming detection
    # ================================================================
    print("T16: Threshold Gaming")
    gaming_detector = ThresholdGamingDetector(window_size=10)
    thresholds_for_gaming = ThresholdSpec(
        levels={"low": 0.3, "high": 0.8},
        actions={"low": "continue", "high": "escalate"})

    # Values clustering just below threshold
    for _ in range(8):
        gaming_detector.record_value("PROC-1", 0.28)  # Just below 0.3
    gaming_detector.record_value("PROC-1", 0.15)
    gaming_detector.record_value("PROC-1", 0.20)

    t("T16.1 Gaming detected (cluster below threshold)",
      gaming_detector.detect_gaming("PROC-1", thresholds_for_gaming))

    # Normal distribution
    gaming_detector2 = ThresholdGamingDetector(window_size=10)
    for v in [0.1, 0.2, 0.5, 0.7, 0.3, 0.4, 0.6, 0.8, 0.15, 0.9]:
        gaming_detector2.record_value("PROC-2", v)

    t("T16.2 Normal distribution → no gaming",
      not gaming_detector2.detect_gaming("PROC-2", thresholds_for_gaming))

    # Unknown procedure
    t("T16.3 Unknown proc → no gaming",
      not gaming_detector2.detect_gaming("PROC-UNKNOWN", thresholds_for_gaming))

    # ================================================================
    # T17: Backward compatibility
    # ================================================================
    print("T17: Backward Compatibility")
    # Minimal procedure (no extensions)
    minimal = Procedure(id="PROC-WIT-3", name="Minimum Witness Requirement",
                        requires_witnesses=3)
    errors = ProcedureValidator.validate(minimal)
    t("T17.1 Minimal valid", len(errors) == 0)
    t("T17.2 No trigger", minimal.trigger is None)
    t("T17.3 Not immediate", not minimal.immediate)
    t("T17.4 No thresholds", minimal.thresholds is None)

    # Minimal in dataset
    min_builder = LawDatasetBuilder("minimal-dataset")
    min_builder.add_procedure(minimal)
    min_dataset = min_builder.build()
    t("T17.5 Dataset valid without extensions",
      "extensions" not in min_dataset)

    # ================================================================
    # T18: E2E — Security breach scenario
    # ================================================================
    print("T18: E2E Security Breach")
    e2e_executor = ProcedureExecutor()
    e2e_scheduler = TriggerScheduler()

    # Register procedures
    emergency = Procedure(
        id="PROC-EMERGENCY", name="Emergency Halt",
        trigger=TriggerSpec.parse("event:security_breach_detected"),
        authority=["security_queen"],
        immediate=True, requires_witnesses=False)
    e2e_scheduler.register(emergency)

    # 1. Detect breach
    triggered = e2e_scheduler.check_event("security_breach_detected")
    t("T18.1 Emergency triggered", "PROC-EMERGENCY" in triggered)

    # 2. Execute with authority
    record = e2e_executor.execute(
        emergency, "security_breach_detected",
        authority="security_queen", now=now)
    t("T18.2 Immediate execution", record.immediate)
    t("T18.3 Success", record.result == "success")
    t("T18.4 Authority logged", record.authority_used == "security_queen")
    t("T18.5 Audit hash", len(record.audit_hash) > 0)

    # ================================================================
    # T19: E2E — ATP recharge scenario
    # ================================================================
    print("T19: E2E ATP Recharge")
    recharge_exec = ProcedureExecutor()
    recharge_proc = Procedure(
        id="PROC-ATP-RECHARGE", name="Daily ATP Regeneration",
        trigger=TriggerSpec.parse("daily_00:00_utc"),
        amount=20, targets=["all_queens"], cap="initial_allocation")

    sched2 = TriggerScheduler()
    sched2.register(recharge_proc)

    # Check at midnight
    midnight = datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone.utc)
    triggered = sched2.check_time(midnight)
    t("T19.1 Recharge triggered at midnight",
      "PROC-ATP-RECHARGE" in triggered)

    # Execute
    r = recharge_exec.execute(recharge_proc, "daily_trigger", now=midnight)
    t("T19.2 Recharge succeeds", r.result == "success")
    t("T19.3 Execution recorded", recharge_proc.execution_count == 1)
    t("T19.4 Last execution set", recharge_proc.last_execution == midnight)

    # ================================================================
    # T20: E2E — Graduated temporal auth
    # ================================================================
    print("T20: E2E Temporal Auth")
    auth_exec = ProcedureExecutor()
    auth_exec.register_method("compute_surprise_factor",
                               lambda ctx: ctx.get("surprise", 0.0))

    auth_proc = Procedure(
        id="PROC-TEMPORAL-AUTH", name="Temporal Auth",
        trigger=TriggerSpec.parse("event:network_state_change"),
        method="compute_surprise_factor",
        thresholds=ThresholdSpec(
            levels={"low": 0.3, "medium": 0.6, "high": 0.8},
            actions={"low": "continue_normal", "medium": "additional_validation",
                     "high": "witness_request"}))

    # Normal scenario
    r1 = auth_exec.execute(auth_proc, "network_state_change",
                            context={"surprise": 0.1}, now=now)
    t("T20.1 Normal → below threshold", r1.matched_level == "below_threshold")

    # Medium surprise
    r2 = auth_exec.execute(auth_proc, "network_state_change",
                            context={"surprise": 0.65}, now=now)
    t("T20.2 Medium → validation", r2.matched_action == "additional_validation")

    # High surprise
    r3 = auth_exec.execute(auth_proc, "network_state_change",
                            context={"surprise": 0.9}, now=now)
    t("T20.3 High → witness request", r3.matched_action == "witness_request")
    t("T20.4 Computed value logged", r3.computed_value == 0.9)

    # ================================================================
    # T21: Interval trigger execution
    # ================================================================
    print("T21: Interval Triggers")
    interval_proc = Procedure(
        id="PROC-REVIEW", name="Quarterly Review",
        trigger=TriggerSpec.parse("interval_90_days"))

    sched3 = TriggerScheduler()
    sched3.register(interval_proc)

    # First time → should trigger (never executed)
    triggered = sched3.check_intervals(now)
    t("T21.1 First trigger fires", "PROC-REVIEW" in triggered)

    # Mark as executed
    interval_proc.last_execution = now

    # Check again → too soon
    triggered2 = sched3.check_intervals(now + timedelta(days=30))
    t("T21.2 Too soon → no trigger", "PROC-REVIEW" not in triggered2)

    # After 90 days → fires
    triggered3 = sched3.check_intervals(now + timedelta(days=91))
    t("T21.3 After interval → fires", "PROC-REVIEW" in triggered3)

    # ================================================================
    # T22: All failure actions
    # ================================================================
    print("T22: All Failure Actions")
    for fa in FailureAction:
        proc = Procedure(id=f"FA-{fa.value}", name=f"Test {fa.value}",
                         failure_action=fa)
        errors = ProcedureValidator.validate(proc)
        t(f"T22.{fa.value} Valid failure action",
          not any(e.field == "failureAction" for e in errors))

    # ================================================================
    # T23: Procedure state transitions
    # ================================================================
    print("T23: State Transitions")
    state_proc = Procedure(id="STATE-1", name="State Test")
    t("T23.1 Initial state = IDLE", state_proc.state == ProcedureState.IDLE)

    exec5 = ProcedureExecutor()
    exec5.execute(state_proc, "test", now=now)
    t("T23.2 After success = COMPLETED",
      state_proc.state == ProcedureState.COMPLETED)

    # Reset and fail
    state_proc2 = Procedure(id="STATE-2", name="State Test 2",
                            failure_action=FailureAction.REJECT_TRANSACTION)
    exec5.execute(state_proc2, "test",
                   context={"simulate_failure": True}, now=now)
    t("T23.3 After failure = FAILED",
      state_proc2.state == ProcedureState.FAILED)

    # Emergency halt
    state_proc3 = Procedure(id="STATE-3", name="State Test 3",
                            failure_action=FailureAction.EMERGENCY_HALT)
    exec5.execute(state_proc3, "test",
                   context={"simulate_failure": True}, now=now)
    t("T23.4 After halt = HALTED",
      state_proc3.state == ProcedureState.HALTED)

    # ================================================================
    # T24: Edge cases
    # ================================================================
    print("T24: Edge Cases")
    # No method registered → no computation
    exec6 = ProcedureExecutor()
    proc_no_method = Procedure(
        id="EDGE-1", name="No Method",
        method="nonexistent_method",
        thresholds=ThresholdSpec(
            levels={"low": 0.3},
            actions={"low": "do_something"}))
    r = exec6.execute(proc_no_method, "test", now=now)
    t("T24.1 Missing method → no value", r.computed_value is None)
    t("T24.2 Still succeeds", r.result == "success")

    # Trigger with unusual format
    t6 = TriggerSpec.parse("some_unknown_trigger")
    t("T24.3 Unknown format → event type", t6.trigger_type == TriggerType.EVENT)

    # Empty thresholds
    empty_thresh = ThresholdSpec(levels={}, actions={})
    level, action = empty_thresh.evaluate(0.5)
    t("T24.4 Empty thresholds → below", level == "below_threshold")

    # ================================================================
    # T25: Serialization round-trip
    # ================================================================
    print("T25: JSON Serialization")
    builder2 = LawDatasetBuilder("test-dataset", "2.0.0")
    all_procs = [proc_wit, proc_emergency, proc_recharge, proc_temporal,
                 proc_hw, proc_consensus]
    for p in all_procs:
        builder2.add_procedure(p)

    dataset = builder2.build()
    json_str = json.dumps(dataset, indent=2)

    t("T25.1 Serializes to JSON", len(json_str) > 0)
    parsed = json.loads(json_str)
    t("T25.2 Round-trips to dict", isinstance(parsed, dict))
    t("T25.3 Procedures preserved", len(parsed["procedures"]) == 6)
    t("T25.4 Context preserved", parsed["@context"][0].startswith("https://"))

    # ================================================================
    # SUMMARY
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Law Oracle Procedures: {passed}/{total} checks passed")
    if passed == total:
        print("  All checks passed!")
    else:
        print(f"  {total - passed} checks FAILED")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
