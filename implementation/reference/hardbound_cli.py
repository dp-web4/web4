#!/usr/bin/env python3
"""
Hardbound CLI — Enterprise Team Management with Hardware-Backed Identity
=========================================================================

Command-line tool for creating and managing Web4 teams (societies)
with TPM2-backed identity. Wraps HardwareWeb4Entity and the
simulations/team infrastructure.

Commands:
    team create <name>         — Create a new team with hardware-bound root
    team info [name]           — Show team status and member list
    team list                  — List all teams
    team add-member <team> <name> <type> — Add a member to the team
    team sign <team> <actor> <action>    — Sign an R6 action
    entity create <name> <type> — Create a standalone hardware entity
    entity sign <name> <action> — Sign an R6 action with hardware key
    avp prove <name>           — Run AVP aliveness proof
    avp attest                 — Get TPM2 attestation
    ek info                    — Show EK certificate chain info
    ek verify                  — Verify EK certificate chain
    status                     — Show full system status

State is persisted to .hardbound/teams/<name>/ directory.

Enterprise Terminology Bridge:
    Society    → Team
    Citizen    → Member
    Law Oracle → Admin
    Blockchain → Ledger
    Birth Cert → Onboarding Record

Date: 2026-02-19 (persistent state: 2026-02-20, governance: 2026-02-20)
"""

import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web4_entity import (
    Web4Entity, EntityType, R6Request, R6Result, R6Decision,
    T3Tensor, V3Tensor, ATPBudget
)
from hardware_entity import HardwareWeb4Entity

# Default state directory
HARDBOUND_DIR = Path.cwd() / ".hardbound"

# ═══════════════════════════════════════════════════════════════
# Team Roles — Enterprise governance structure
# ═══════════════════════════════════════════════════════════════

class TeamRole:
    """Role definitions for team governance."""
    ADMIN = "admin"       # Hardware-bound, can approve/deny, manage members
    OPERATOR = "operator" # Can execute approved actions, modify resources
    AGENT = "agent"       # AI agent, self-approving for permitted actions
    VIEWER = "viewer"     # Read-only, can witness but not act

    # Default actions that require admin approval (used for initial policy)
    DEFAULT_ADMIN_ONLY = {
        "approve_deployment", "set_resource_limit", "rotate_credentials",
        "add_member", "remove_member", "update_policy", "grant_role",
        "revoke_role", "set_atp_limit", "emergency_shutdown",
    }

    # Default actions that require operator or higher (used for initial policy)
    DEFAULT_OPERATOR_MIN = {
        "deploy_staging", "run_migration", "scale_service",
        "update_config", "restart_service",
    }

    # Keep backward compat aliases
    ADMIN_ONLY = DEFAULT_ADMIN_ONLY
    OPERATOR_MIN = DEFAULT_OPERATOR_MIN


class TeamHeartbeat:
    """
    Heartbeat-driven ledger timing.

    The ledger doesn't write every action immediately — it aggregates
    actions into blocks based on the team's metabolic state:

      FOCUS:  15s heartbeat — intensive work, frequent commits
      WAKE:   60s heartbeat — normal operation
      REST:  300s heartbeat — reduced activity, batched updates
      DREAM: 1800s heartbeat — consolidation, minimal writes
      CRISIS:  5s heartbeat — emergency mode, near-real-time

    Between heartbeats, actions accumulate in a pending buffer.
    On each heartbeat tick, the buffer is flushed to a ledger block.

    This is bio-inspired: metabolic rate controls information flow.
    """

    # Heartbeat intervals per metabolic state (seconds)
    INTERVALS = {
        "focus": 15,
        "wake": 60,
        "rest": 300,
        "dream": 1800,
        "crisis": 5,
    }

    # ATP recharge rates per heartbeat tick (per metabolic state)
    # Higher recharge in restful states; minimal during intense work
    # NOTE: crisis has a small trickle to prevent death spirals
    # (stress test 2026-02-20: 0.0 crisis rate → unrecoverable depletion)
    RECHARGE_RATES = {
        "dream": 20.0,   # Max recharge — consolidation/recovery mode
        "rest": 10.0,    # High recharge — reduced activity
        "wake": 5.0,     # Moderate — normal operation
        "focus": 2.0,    # Low — most energy goes to work
        "crisis": 3.0,   # Trickle — prevents death spiral, allows slow recovery
    }

    def __init__(self, state: str = "wake"):
        self.state = state
        self.last_heartbeat = datetime.now(timezone.utc)
        self.pending_actions: list = []
        self.blocks_written = 0
        self.total_recharged = 0.0  # Cumulative ATP recharged

    @property
    def interval(self) -> int:
        """Current heartbeat interval in seconds."""
        return self.INTERVALS.get(self.state, 60)

    @property
    def recharge_rate(self) -> float:
        """ATP recharge per heartbeat tick in current state."""
        return self.RECHARGE_RATES.get(self.state, 5.0)

    def seconds_since_last(self) -> float:
        """Seconds since last heartbeat."""
        now = datetime.now(timezone.utc)
        return (now - self.last_heartbeat).total_seconds()

    def should_flush(self) -> bool:
        """Check if enough time has elapsed for a heartbeat flush."""
        return self.seconds_since_last() >= self.interval

    def queue_action(self, action: dict):
        """Queue an action for the next heartbeat flush."""
        self.pending_actions.append(action)

    def flush(self) -> list:
        """Flush pending actions and reset heartbeat timer."""
        actions = list(self.pending_actions)
        self.pending_actions = []
        self.last_heartbeat = datetime.now(timezone.utc)
        self.blocks_written += 1
        return actions

    def compute_recharge(self, elapsed_seconds: float) -> float:
        """
        Compute ATP recharge based on elapsed time and metabolic state.

        Recharge is proportional to elapsed heartbeat intervals:
        - 1 full heartbeat interval = 1x recharge_rate
        - Partial intervals = proportional recharge
        - Capped at 3x recharge_rate per call (prevent time-skip abuse)
        """
        if self.recharge_rate <= 0:
            return 0.0
        intervals_elapsed = elapsed_seconds / self.interval if self.interval > 0 else 0
        raw_recharge = intervals_elapsed * self.recharge_rate
        # Cap at 3x to prevent gaming via long idle periods
        max_recharge = self.recharge_rate * 3.0
        recharge = min(raw_recharge, max_recharge)
        return round(recharge, 2)

    def transition(self, new_state: str):
        """Transition to a new metabolic state."""
        if new_state != self.state:
            old = self.state
            self.state = new_state
            return {"from": old, "to": new_state,
                    "interval_change": f"{self.INTERVALS.get(old, 60)}s → {self.interval}s",
                    "recharge_change": f"{self.RECHARGE_RATES.get(old, 5.0)} → {self.recharge_rate} ATP/tick"}
        return None

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "interval_seconds": self.interval,
            "recharge_rate": self.recharge_rate,
            "pending_actions": len(self.pending_actions),
            "blocks_written": self.blocks_written,
            "total_recharged": round(self.total_recharged, 2),
            "seconds_since_last": round(self.seconds_since_last(), 1),
        }


class TeamPolicy:
    """
    Versioned policy for team governance.

    Policies are stored as entries in the hash-chained ledger, so:
    - "What policy was active when action X occurred?" is answerable from the chain
    - Policy changes are themselves governed actions (admin-only)
    - The full policy history is tamper-evident
    """

    # Default action costs (ATP) — higher for more impactful actions
    DEFAULT_ACTION_COSTS = {
        # Admin actions (high cost — they change system state)
        "approve_deployment": 25.0,
        "emergency_shutdown": 50.0,
        "rotate_credentials": 20.0,
        "set_resource_limit": 15.0,
        "add_member": 10.0,
        "remove_member": 10.0,
        "update_policy": 30.0,
        "grant_role": 15.0,
        "revoke_role": 15.0,
        "set_atp_limit": 20.0,
        # Operator actions (medium cost)
        "deploy_staging": 20.0,
        "run_migration": 25.0,
        "scale_service": 15.0,
        "update_config": 10.0,
        "restart_service": 10.0,
        # Agent actions (low cost — routine work)
        "run_analysis": 5.0,
        "review_pr": 5.0,
        "execute_review": 3.0,
        "run_diagnostics": 5.0,
        "validate_schema": 3.0,
        "analyze_dataset": 8.0,
    }
    DEFAULT_COST = 10.0  # Fallback for unknown actions

    # Default multi-sig requirements for critical actions
    DEFAULT_MULTI_SIG = {
        "emergency_shutdown": {"required": 2, "eligible_roles": ["admin", "operator"]},
        "rotate_credentials": {"required": 2, "eligible_roles": ["admin"]},
    }

    def __init__(self, version: int = 1, admin_only: set = None,
                 operator_min: set = None, custom_rules: dict = None,
                 action_costs: dict = None, multi_sig: dict = None):
        self.version = version
        self.admin_only = admin_only if admin_only is not None else set(TeamRole.DEFAULT_ADMIN_ONLY)
        self.operator_min = operator_min if operator_min is not None else set(TeamRole.DEFAULT_OPERATOR_MIN)
        self.custom_rules = custom_rules or {}
        self.action_costs = action_costs if action_costs is not None else dict(self.DEFAULT_ACTION_COSTS)
        self.multi_sig = multi_sig if multi_sig is not None else dict(self.DEFAULT_MULTI_SIG)
        # Seal the integrity hash after construction
        self._integrity_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute integrity hash over all policy fields."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Check if policy state matches its sealed hash (detects cache tampering)."""
        return self._integrity_hash == self._compute_hash()

    def get_cost(self, action: str) -> float:
        """Get the ATP cost for an action from policy."""
        return self.action_costs.get(action, self.DEFAULT_COST)

    def requires_multi_sig(self, action: str) -> dict:
        """Check if an action requires multi-sig. Returns requirement or None."""
        return self.multi_sig.get(action)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "admin_only": sorted(list(self.admin_only)),
            "operator_min": sorted(list(self.operator_min)),
            "custom_rules": self.custom_rules,
            "action_costs": self.action_costs,
            "multi_sig": self.multi_sig,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeamPolicy":
        return cls(
            version=data.get("version", 1),
            admin_only=set(data.get("admin_only", [])),
            operator_min=set(data.get("operator_min", [])),
            custom_rules=data.get("custom_rules", {}),
            action_costs=data.get("action_costs"),
            multi_sig=data.get("multi_sig"),
        )

    @classmethod
    def default(cls) -> "TeamPolicy":
        """Create the default policy (matches TeamRole defaults)."""
        return cls(
            version=1,
            admin_only=set(TeamRole.DEFAULT_ADMIN_ONLY),
            operator_min=set(TeamRole.DEFAULT_OPERATOR_MIN),
            custom_rules={},
            action_costs=dict(cls.DEFAULT_ACTION_COSTS),
            multi_sig=dict(cls.DEFAULT_MULTI_SIG),
        )


# ═══════════════════════════════════════════════════════════════
# SAL Birth Certificate — Genesis identity record
# ═══════════════════════════════════════════════════════════════

# Role → initial rights mapping (from SAL spec §2.2)
ROLE_INITIAL_RIGHTS = {
    TeamRole.ADMIN: [
        "exist", "interact", "accumulate_reputation",
        "manage_members", "update_policy", "approve_actions",
        "delegate_authority", "emergency_powers",
    ],
    TeamRole.OPERATOR: [
        "exist", "interact", "accumulate_reputation",
        "execute_approved", "modify_resources", "deploy",
    ],
    TeamRole.AGENT: [
        "exist", "interact", "accumulate_reputation",
        "self_approve_permitted", "execute_tasks",
    ],
    TeamRole.VIEWER: [
        "exist", "interact", "accumulate_reputation",
        "witness", "read_state",
    ],
}

# Role → initial responsibilities mapping
ROLE_INITIAL_RESPONSIBILITIES = {
    TeamRole.ADMIN: [
        "abide_law", "respect_quorum", "maintain_integrity",
        "respond_to_crisis", "audit_compliance",
    ],
    TeamRole.OPERATOR: [
        "abide_law", "respect_quorum", "report_anomalies",
        "follow_procedures",
    ],
    TeamRole.AGENT: [
        "abide_law", "respect_quorum", "minimize_resource_use",
        "report_failures",
    ],
    TeamRole.VIEWER: [
        "abide_law", "respect_quorum",
    ],
}


class BirthCertificate:
    """
    SAL Birth Certificate — genesis identity record for team members.

    Created when an entity joins a society (team). Immutable after creation.
    Follows the canonical JSON-LD structure from SAL spec §2.2.

    Enterprise Terminology:
        Society    → Team
        Citizen    → Member
        Law Oracle → Admin (the team's policy authority)
        Birth Cert → Onboarding Record
    """

    def __init__(self, entity_lct: str, citizen_role: str,
                 society_lct: str, law_oracle_lct: str,
                 law_version: int, witnesses: list,
                 genesis_block: str, initial_rights: list,
                 initial_responsibilities: list,
                 binding_type: str = "software",
                 entity_name: str = "",
                 society_name: str = ""):
        self.entity_lct = entity_lct
        self.citizen_role = citizen_role
        self.society_lct = society_lct
        self.law_oracle_lct = law_oracle_lct
        self.law_version = f"v{law_version}"
        self.birth_timestamp = datetime.now(timezone.utc).isoformat()
        self.witnesses = witnesses
        self.genesis_block = genesis_block
        self.initial_rights = initial_rights
        self.initial_responsibilities = initial_responsibilities
        self.binding_type = binding_type
        self.entity_name = entity_name
        self.society_name = society_name

        # Compute certificate hash for tamper detection
        self.cert_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of the canonical certificate content."""
        canonical = json.dumps(self.to_dict(include_hash=False),
                               sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify certificate integrity."""
        return self.cert_hash == self._compute_hash()

    def to_dict(self, include_hash: bool = True) -> dict:
        """Serialize to canonical JSON-LD form."""
        d = {
            "@context": ["https://web4.io/contexts/sal.jsonld"],
            "type": "Web4BirthCertificate",
            "entity": self.entity_lct,
            "entityName": self.entity_name,
            "citizenRole": self.citizen_role,
            "society": self.society_lct,
            "societyName": self.society_name,
            "lawOracle": self.law_oracle_lct,
            "lawVersion": self.law_version,
            "birthTimestamp": self.birth_timestamp,
            "witnesses": self.witnesses,
            "genesisBlock": self.genesis_block,
            "initialRights": self.initial_rights,
            "initialResponsibilities": self.initial_responsibilities,
            "bindingType": self.binding_type,
        }
        if include_hash:
            d["certHash"] = self.cert_hash
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "BirthCertificate":
        """Reconstruct from persisted dict."""
        law_version_str = data.get("lawVersion", "v1")
        # Parse "v1" → 1
        law_version_int = int(law_version_str.lstrip("v")) if law_version_str.startswith("v") else 1

        cert = cls(
            entity_lct=data["entity"],
            citizen_role=data["citizenRole"],
            society_lct=data["society"],
            law_oracle_lct=data["lawOracle"],
            law_version=law_version_int,
            witnesses=data.get("witnesses", []),
            genesis_block=data.get("genesisBlock", ""),
            initial_rights=data.get("initialRights", []),
            initial_responsibilities=data.get("initialResponsibilities", []),
            binding_type=data.get("bindingType", "software"),
            entity_name=data.get("entityName", ""),
            society_name=data.get("societyName", ""),
        )
        # Restore original timestamp
        cert.birth_timestamp = data.get("birthTimestamp", cert.birth_timestamp)
        # Recompute hash (should match if untampered)
        cert.cert_hash = cert._compute_hash()
        stored_hash = data.get("certHash")
        if stored_hash and stored_hash != cert.cert_hash:
            cert._tampered = True
        else:
            cert._tampered = False
        return cert


# ═══════════════════════════════════════════════════════════════
# Team Ledger — Hash-chained append-only action log
# ═══════════════════════════════════════════════════════════════

class TeamLedger:
    """
    Hash-chained append-only ledger for team governance actions.

    Each entry contains:
    - sequence: Monotonically increasing integer
    - action: The action record
    - prev_hash: SHA-256 of the previous entry (tamper detection)
    - entry_hash: SHA-256 of this entry's canonical form
    - signer_lct: Who signed this entry
    - signature: Hardware or software signature of entry_hash

    The genesis entry (sequence=0) has prev_hash="genesis".
    """

    GENESIS_HASH = "0" * 64  # All zeros for genesis

    def __init__(self, ledger_path: Path):
        self.path = ledger_path
        self._head_hash: str = self.GENESIS_HASH
        self._sequence: int = 0

        # Load existing chain head
        if self.path.exists():
            self._load_head()

    def _load_head(self):
        """Load the chain head from the existing ledger file."""
        last_line = None
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if last_line:
            try:
                entry = json.loads(last_line)
                self._head_hash = entry.get("entry_hash", self.GENESIS_HASH)
                self._sequence = entry.get("sequence", 0)
            except json.JSONDecodeError:
                pass  # Corrupt last line, will append from current head

    @staticmethod
    def _canonical(data: dict) -> str:
        """Canonical JSON for hashing (sorted keys, no whitespace)."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _hash(data: str) -> str:
        """SHA-256 hex hash."""
        return hashlib.sha256(data.encode()).hexdigest()

    def append(self, action: dict, signer_lct: str = "",
               signer_entity=None) -> dict:
        """
        Append an action to the ledger with hash-chain linkage.

        If signer_entity is a HardwareWeb4Entity, the entry is
        hardware-signed. Otherwise, a software hash is used.
        """
        self._sequence += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build the entry (without entry_hash — that's computed)
        entry = {
            "sequence": self._sequence,
            "timestamp": timestamp,
            "prev_hash": self._head_hash,
            "action": action,
            "signer_lct": signer_lct,
        }

        # Compute entry hash from canonical form
        canonical = self._canonical(entry)
        entry_hash = self._hash(canonical)
        entry["entry_hash"] = entry_hash

        # Sign the entry hash
        signature = ""
        hw_signed = False
        if signer_entity and isinstance(signer_entity, HardwareWeb4Entity):
            sig_record = signer_entity.sign_action(
                R6Request(request=f"ledger:{self._sequence}", role=signer_lct)
            )
            signature = sig_record.get("signature", "")[:64]
            hw_signed = True
        else:
            # Software signature: hash of entry_hash + signer_lct
            signature = self._hash(f"{entry_hash}:{signer_lct}")

        entry["signature"] = signature
        entry["hw_signed"] = hw_signed

        # Append to file
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Update chain head
        self._head_hash = entry_hash
        return entry

    def append_genesis(self, team_name: str, root_lct: str,
                       admin_lct: str, signer_entity=None) -> dict:
        """Write the genesis entry when a team is created."""
        return self.append(
            action={
                "type": "genesis",
                "team": team_name,
                "root_lct": root_lct,
                "admin_lct": admin_lct,
            },
            signer_lct=root_lct,
            signer_entity=signer_entity,
        )

    def verify(self) -> dict:
        """
        Verify the entire ledger chain.

        Returns verification result with:
        - valid: bool (all hashes match)
        - entries: total entry count
        - breaks: list of sequence numbers where chain breaks
        - hw_signed: count of hardware-signed entries
        """
        if not self.path.exists():
            return {"valid": True, "entries": 0, "breaks": [], "hw_signed": 0}

        entries = 0
        breaks = []
        hw_signed = 0
        expected_prev = self.GENESIS_HASH

        with open(self.path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    breaks.append(line_num)
                    continue

                entries += 1

                # Check prev_hash linkage
                if entry.get("prev_hash") != expected_prev:
                    breaks.append(entry.get("sequence", line_num))

                # Count hw_signed before stripping
                if entry.get("hw_signed"):
                    hw_signed += 1

                # Verify entry_hash (strip fields not in canonical form)
                entry_hash = entry.pop("entry_hash", "")
                entry.pop("signature", "")
                entry.pop("hw_signed", False)
                canonical = self._canonical(entry)
                computed_hash = self._hash(canonical)

                if computed_hash != entry_hash:
                    breaks.append(entry.get("sequence", line_num))

                expected_prev = entry_hash

        return {
            "valid": len(breaks) == 0,
            "entries": entries,
            "breaks": breaks,
            "hw_signed": hw_signed,
            "head_hash": expected_prev,
        }

    def active_policy(self) -> dict:
        """
        Find the most recent policy_update entry in the ledger.

        Returns the policy dict, or None if no policy has been written.
        This is O(n) — walks the entire chain. For hot paths, the
        HardboundTeam caches the result.
        """
        if not self.path.exists():
            return None
        last_policy = None
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        action = entry.get("action", {})
                        if action.get("type") == "policy_update":
                            last_policy = action.get("policy")
                    except json.JSONDecodeError:
                        continue
        return last_policy

    def policy_at_sequence(self, seq: int) -> dict:
        """
        Find the policy that was active at a given sequence number.

        Returns the most recent policy_update entry with sequence <= seq,
        or None if no policy existed at that point.
        """
        if not self.path.exists():
            return None
        last_policy = None
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get("sequence", 0) > seq:
                            break
                        action = entry.get("action", {})
                        if action.get("type") == "policy_update":
                            last_policy = action.get("policy")
                    except json.JSONDecodeError:
                        continue
        return last_policy

    def count(self) -> int:
        """Count entries in the ledger."""
        if not self.path.exists():
            return 0
        return sum(1 for line in open(self.path) if line.strip())

    def tail(self, n: int = 10) -> list:
        """Get the last N entries."""
        if not self.path.exists():
            return []
        entries = []
        for line in open(self.path):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries[-n:]

    def _all_entries(self) -> list:
        """Load all entries (cached internally for analytics)."""
        if not self.path.exists():
            return []
        entries = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def query(self, actor: str = None, action_type: str = None,
              decision: str = None, hw_only: bool = False,
              since_seq: int = None, limit: int = None) -> list:
        """
        Query ledger entries with filters.

        Args:
            actor: Filter by actor name (in action dict)
            action_type: Filter by action type (genesis, action, policy_update, add_member)
            decision: Filter by decision (approved, denied)
            hw_only: Only hardware-signed entries
            since_seq: Only entries with sequence >= this
            limit: Maximum entries to return

        Returns:
            List of matching entries (most recent first)
        """
        entries = self._all_entries()
        results = []

        for entry in entries:
            action = entry.get("action", {})

            if since_seq is not None and entry.get("sequence", 0) < since_seq:
                continue
            if actor and action.get("actor") != actor:
                continue
            if action_type and action.get("type") != action_type:
                continue
            if decision and action.get("decision") != decision:
                continue
            if hw_only and not entry.get("hw_signed"):
                continue

            results.append(entry)

        # Most recent first
        results.reverse()

        if limit:
            results = results[:limit]

        return results

    def analytics(self) -> dict:
        """
        Compute analytics over the entire ledger.

        Returns:
            {
                "total_entries": int,
                "actions": {"total": int, "approved": int, "denied": int, "approval_rate": float},
                "by_actor": {"name": {"actions": int, "approved": int, "denied": int, "atp_spent": float}},
                "by_action_type": {"type": {"count": int, "total_atp": float}},
                "policy_versions": int,
                "hw_signed_pct": float,
                "timeline": {"first": str, "last": str, "duration_hours": float},
            }
        """
        entries = self._all_entries()
        if not entries:
            return {"total_entries": 0}

        total = len(entries)
        actions = 0
        approved = 0
        denied = 0
        hw_signed = 0
        by_actor = {}
        by_type = {}
        policy_versions = 0

        for entry in entries:
            if entry.get("hw_signed"):
                hw_signed += 1

            action = entry.get("action", {})
            atype = action.get("type", "unknown")

            # Count by type
            if atype not in by_type:
                by_type[atype] = {"count": 0, "total_atp": 0.0}
            by_type[atype]["count"] += 1

            if atype == "policy_update":
                policy_versions += 1
                continue

            if atype == "action":
                actions += 1
                actor_name = action.get("actor", "unknown")
                adecision = action.get("decision", "unknown")
                atp_cost = action.get("atp_cost", 0.0)

                by_type[atype]["total_atp"] += atp_cost

                if actor_name not in by_actor:
                    by_actor[actor_name] = {"actions": 0, "approved": 0,
                                            "denied": 0, "atp_spent": 0.0}
                by_actor[actor_name]["actions"] += 1

                if adecision == "approved":
                    approved += 1
                    by_actor[actor_name]["approved"] += 1
                    by_actor[actor_name]["atp_spent"] += atp_cost
                elif adecision == "denied":
                    denied += 1
                    by_actor[actor_name]["denied"] += 1

        # Timeline
        first_ts = entries[0].get("timestamp", "")
        last_ts = entries[-1].get("timestamp", "")
        try:
            from datetime import datetime as dt
            t1 = dt.fromisoformat(first_ts.replace("Z", "+00:00"))
            t2 = dt.fromisoformat(last_ts.replace("Z", "+00:00"))
            duration_hours = (t2 - t1).total_seconds() / 3600
        except Exception:
            duration_hours = 0.0

        return {
            "total_entries": total,
            "actions": {
                "total": actions,
                "approved": approved,
                "denied": denied,
                "approval_rate": round(approved / actions * 100, 1) if actions > 0 else 0.0,
            },
            "by_actor": by_actor,
            "by_action_type": by_type,
            "policy_versions": policy_versions,
            "hw_signed_pct": round(hw_signed / total * 100, 1) if total > 0 else 0.0,
            "timeline": {
                "first": first_ts,
                "last": last_ts,
                "duration_hours": round(duration_hours, 2),
            },
        }


class MultiSigRequest:
    """
    A pending multi-signature request.

    Critical actions requiring M-of-N approval accumulate signatures
    in this buffer. Once the quorum is met, the action executes.
    Expired requests are pruned on access.
    """

    def __init__(self, request_id: str, actor: str, action: str,
                 required: int, eligible_roles: list,
                 ttl_seconds: int = 3600):
        self.request_id = request_id
        self.actor = actor          # Who requested the action
        self.action = action        # What action
        self.required = required    # How many approvals needed
        self.eligible_roles = eligible_roles
        self.approvals: list = []   # List of {"approver": name, "role": role, "timestamp": ts}
        self.created_at = datetime.now(timezone.utc)
        self.ttl_seconds = ttl_seconds
        self.executed = False
        self.denied = False

    @property
    def is_expired(self) -> bool:
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

    @property
    def approval_count(self) -> int:
        return len(self.approvals)

    @property
    def is_quorum_met(self) -> bool:
        return self.approval_count >= self.required

    def add_approval(self, approver: str, role: str) -> dict:
        """Add an approval. Returns status."""
        # Check for duplicate
        for a in self.approvals:
            if a["approver"] == approver:
                return {"error": f"{approver} already approved this request",
                        "duplicate": True}

        # Check role eligibility
        if role not in self.eligible_roles:
            return {"error": f"role '{role}' not eligible (need: {self.eligible_roles})",
                    "ineligible": True}

        self.approvals.append({
            "approver": approver,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "approved_by": approver,
            "approvals": self.approval_count,
            "required": self.required,
            "quorum_met": self.is_quorum_met,
        }

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "actor": self.actor,
            "action": self.action,
            "required": self.required,
            "approvals": self.approvals,
            "approval_count": self.approval_count,
            "quorum_met": self.is_quorum_met,
            "eligible_roles": self.eligible_roles,
            "created_at": self.created_at.isoformat(),
            "expired": self.is_expired,
            "executed": self.executed,
        }


class MultiSigBuffer:
    """Buffer for pending multi-sig requests."""

    def __init__(self):
        self.pending: dict = {}  # request_id → MultiSigRequest

    def create_request(self, actor: str, action: str,
                       required: int, eligible_roles: list) -> MultiSigRequest:
        """Create a new multi-sig request."""
        request_id = hashlib.sha256(
            f"{actor}:{action}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        req = MultiSigRequest(request_id, actor, action, required, eligible_roles)
        self.pending[request_id] = req
        return req

    def find_pending(self, action: str) -> MultiSigRequest:
        """Find a pending (non-expired, non-executed) request for an action."""
        self._prune_expired()
        for req in self.pending.values():
            if req.action == action and not req.executed and not req.is_expired:
                return req
        return None

    def _prune_expired(self):
        """Remove expired requests."""
        expired = [rid for rid, req in self.pending.items() if req.is_expired]
        for rid in expired:
            del self.pending[rid]

    def to_dict(self) -> dict:
        self._prune_expired()
        return {
            "pending_count": len(self.pending),
            "requests": {rid: req.to_dict() for rid, req in self.pending.items()},
        }

    def save(self, path: "Path"):
        """Persist pending requests to disk."""
        self._prune_expired()
        data = []
        for req in self.pending.values():
            if not req.executed and not req.is_expired:
                data.append({
                    "request_id": req.request_id,
                    "actor": req.actor,
                    "action": req.action,
                    "required": req.required,
                    "eligible_roles": req.eligible_roles,
                    "approvals": req.approvals,
                    "created_at": req.created_at.isoformat(),
                    "ttl_seconds": req.ttl_seconds,
                })
        if data:
            path.write_text(json.dumps(data, indent=2))
        elif path.exists():
            path.unlink()  # Clean up empty file

    @classmethod
    def load(cls, path: "Path") -> "MultiSigBuffer":
        """Restore pending requests from disk."""
        buf = cls()
        if not path.exists():
            return buf
        try:
            data = json.loads(path.read_text())
            for item in data:
                req = MultiSigRequest(
                    request_id=item["request_id"],
                    actor=item["actor"],
                    action=item["action"],
                    required=item["required"],
                    eligible_roles=item["eligible_roles"],
                    ttl_seconds=item.get("ttl_seconds", 3600),
                )
                # Restore creation time
                req.created_at = datetime.fromisoformat(item["created_at"])
                # Restore approvals
                req.approvals = item.get("approvals", [])
                # Only add if not expired
                if not req.is_expired:
                    buf.pending[req.request_id] = req
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupt file, start fresh
        return buf


def detect_tpm2() -> bool:
    """Check if TPM2 is available."""
    try:
        from core.lct_binding.tpm2_provider import TPM2Provider
        provider = TPM2Provider()
        info = provider.get_platform_info()
        return info.has_tpm2
    except Exception:
        return False


def create_entity(name: str, entity_type: str, use_tpm: bool = True) -> HardwareWeb4Entity:
    """Create a hardware-backed entity."""
    etype = EntityType(entity_type)
    if use_tpm and detect_tpm2():
        return HardwareWeb4Entity.create_with_tpm2(etype, name)
    else:
        return HardwareWeb4Entity.create_simulated(etype, name)


class HardboundTeam:
    """
    A Hardbound team: enterprise wrapper around Web4Entity hierarchy.

    The team root is a SOCIETY-type HardwareWeb4Entity.
    Members are child entities (HUMAN, AI, ORGANIZATION, etc.).
    Admin is a HUMAN-type hardware-bound entity with elevated privileges.

    State is persisted to .hardbound/teams/<name>/ as JSON files:
        team.json          — Team metadata and root entity state
        members/<name>.json — Per-member entity state
        actions.jsonl       — Append-only action log (ledger)
    """

    def __init__(self, name: str, use_tpm: bool = True, state_dir: Path = None,
                 team_atp: float = 1000.0):
        self.name = name
        self.use_tpm = use_tpm and detect_tpm2()
        self.root: HardwareWeb4Entity = None
        self.admin: HardwareWeb4Entity = None
        self.members: dict = {}  # name → HardwareWeb4Entity
        self.roles: dict = {}    # member_name → TeamRole constant
        self.action_log: list = []
        self.created_at = datetime.now(timezone.utc).isoformat()

        # Team-level ATP pool (aggregate budget)
        self.team_atp = team_atp
        self.team_atp_max = team_atp
        self.team_adp_discharged = 0.0  # Total ATP consumed by team

        # State directory
        self.state_dir = state_dir or (HARDBOUND_DIR / "teams" / name)

        # Hash-chained ledger
        self.ledger = TeamLedger(self.state_dir / "ledger.jsonl")

        # Policy cache (resolved from ledger, avoids re-scanning)
        self._cached_policy: TeamPolicy = None

        # Heartbeat-driven ledger timing
        self.heartbeat = TeamHeartbeat()

        # Multi-sig approval buffer
        self.multi_sig_buffer = MultiSigBuffer()

        # SAL Birth Certificates (member_name → BirthCertificate)
        self.birth_certificates: dict = {}

    # ─── Persistence ────────────────────────────────────────────

    def _entity_to_state(self, entity) -> dict:
        """Serialize entity state for persistence."""
        state = {
            "entity_type": entity.entity_type.value,
            "name": entity.name,
            "lct_id": entity.lct_id,
            "coherence": round(entity.coherence, 4),
            "t3": {
                "talent": entity.t3.talent,
                "training": entity.t3.training,
                "temperament": entity.t3.temperament,
            },
            "v3": {
                "valuation": entity.v3.valuation,
                "veracity": entity.v3.veracity,
                "validity": entity.v3.validity,
            },
            "atp_balance": round(entity.atp.atp_balance, 2),
            "adp_discharged": round(entity.atp.adp_discharged, 2),
        }

        if isinstance(entity, HardwareWeb4Entity):
            state.update({
                "key_id": entity.key_id,
                "public_key": entity.public_key,
                "tpm_handle": entity.tpm_handle,
                "hardware_type": entity.hardware_type,
                "capability_level": entity.capability_level,
                "trust_ceiling": entity.trust_ceiling,
                "binding_proof": entity.binding_proof,
                "signed_action_count": len(entity.signed_actions),
            })
        else:
            state["capability_level"] = getattr(entity, 'capability_level', 4)

        return state

    def _entity_from_state(self, state: dict) -> HardwareWeb4Entity:
        """
        Reconstruct entity from persisted state.

        For hardware entities, attempts to reconnect to the TPM2
        persistent handle so hardware signing works after reload.
        """
        if "key_id" in state:
            # Hardware entity
            entity = HardwareWeb4Entity(
                entity_type=EntityType(state["entity_type"]),
                name=state["name"],
                lct_id=state["lct_id"],
                key_id=state["key_id"],
                public_key=state["public_key"],
                tpm_handle=state.get("tpm_handle", ""),
                hardware_type=state.get("hardware_type", "tpm2"),
                atp_allocation=state.get("atp_balance", 100.0),
            )
            entity.binding_proof = state.get("binding_proof")

            # Reconnect to TPM2 persistent handle if available
            if self.use_tpm and state.get("tpm_handle"):
                try:
                    from core.lct_binding.tpm2_provider import TPM2Provider
                    provider = TPM2Provider()
                    # Verify the persistent handle still exists
                    handle = state["tpm_handle"]
                    result = provider._run_tpm2_command(
                        ["tpm2_readpublic", "-c", handle],
                        check=False
                    )
                    if result.returncode == 0:
                        entity._tpm2_reconnected = True
                    else:
                        entity._tpm2_reconnected = False
                except Exception:
                    entity._tpm2_reconnected = False
        else:
            # Software entity (reconstruct as Web4Entity)
            entity = Web4Entity(
                EntityType(state["entity_type"]),
                state["name"],
                atp_allocation=state.get("atp_balance", 100.0),
            )
            entity.lct_id = state["lct_id"]

        # Restore trust state
        if "t3" in state:
            entity.t3 = T3Tensor(**state["t3"])
        if "v3" in state:
            entity.v3 = V3Tensor(**state["v3"])

        return entity

    def save(self):
        """Save team state to disk."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        members_dir = self.state_dir / "members"
        members_dir.mkdir(exist_ok=True)

        # Save team metadata
        team_state = {
            "name": self.name,
            "created_at": self.created_at,
            "use_tpm": self.use_tpm,
            "member_names": list(self.members.keys()),
            "roles": self.roles,
            "team_atp": round(self.team_atp, 2),
            "team_atp_max": round(self.team_atp_max, 2),
            "team_adp_discharged": round(self.team_adp_discharged, 2),
            "total_recharged": round(self.heartbeat.total_recharged, 2),
        }
        if self.root:
            team_state["root"] = self._entity_to_state(self.root)
        if self.admin:
            team_state["admin_name"] = f"{self.name}-admin"

        (self.state_dir / "team.json").write_text(
            json.dumps(team_state, indent=2)
        )

        # Save each member
        for name, member in self.members.items():
            member_state = self._entity_to_state(member)
            safe_name = name.replace("/", "_").replace(" ", "_")
            (members_dir / f"{safe_name}.json").write_text(
                json.dumps(member_state, indent=2)
            )

        # Persist multi-sig pending requests
        self.multi_sig_buffer.save(self.state_dir / "multi_sig_pending.json")

        # Flush pending actions to hash-chained ledger
        if self.action_log:
            for action in self.action_log:
                actor_name = action.get("actor", "")
                signer = self.members.get(actor_name)
                self.ledger.append(
                    action=action,
                    signer_lct=signer.lct_id if signer and hasattr(signer, 'lct_id') else "",
                    signer_entity=signer if isinstance(signer, HardwareWeb4Entity) else None,
                )
            self.action_log = []  # Clear after saving

    @classmethod
    def load(cls, name: str, state_dir: Path = None) -> "HardboundTeam":
        """Load team state from disk."""
        base = state_dir or (HARDBOUND_DIR / "teams" / name)
        team_file = base / "team.json"
        if not team_file.exists():
            raise FileNotFoundError(f"Team '{name}' not found at {base}")

        team_state = json.loads(team_file.read_text())
        team = cls(team_state["name"], use_tpm=team_state.get("use_tpm", True),
                   team_atp=team_state.get("team_atp", 1000.0))
        team.created_at = team_state.get("created_at", "unknown")
        team.team_atp_max = team_state.get("team_atp_max", team.team_atp)
        team.team_adp_discharged = team_state.get("team_adp_discharged", 0.0)
        team.heartbeat.total_recharged = team_state.get("total_recharged", 0.0)
        team.state_dir = base

        # Reinitialize ledger pointing to correct file
        team.ledger = TeamLedger(base / "ledger.jsonl")

        # Restore root
        if "root" in team_state:
            team.root = team._entity_from_state(team_state["root"])

        # Restore members (skip birth certificate files)
        members_dir = base / "members"
        if members_dir.exists():
            for member_file in sorted(members_dir.glob("*.json")):
                if member_file.name.endswith("_birth_cert.json"):
                    continue
                member_state = json.loads(member_file.read_text())
                member = team._entity_from_state(member_state)
                team.members[member_state["name"]] = member

        # Restore admin reference
        admin_name = team_state.get("admin_name")
        if admin_name and admin_name in team.members:
            team.admin = team.members[admin_name]

        # Restore roles
        team.roles = team_state.get("roles", {})

        # Assign default roles if not persisted
        if not team.roles and admin_name:
            team.roles[admin_name] = TeamRole.ADMIN
            for mname in team.members:
                if mname not in team.roles:
                    member = team.members[mname]
                    if member.entity_type in (EntityType.AI, EntityType.SERVICE, EntityType.TASK):
                        team.roles[mname] = TeamRole.AGENT
                    else:
                        team.roles[mname] = TeamRole.OPERATOR

        # Warm up policy cache from ledger
        team._resolve_policy()

        # Restore multi-sig pending requests
        team.multi_sig_buffer = MultiSigBuffer.load(base / "multi_sig_pending.json")

        # Restore birth certificates from disk
        members_dir = base / "members"
        if members_dir.exists():
            for cert_file in members_dir.glob("*_birth_cert.json"):
                try:
                    data = json.loads(cert_file.read_text())
                    cert = BirthCertificate.from_dict(data)
                    member_name = data.get("entityName", "")
                    if member_name:
                        team.birth_certificates[member_name] = cert
                except (json.JSONDecodeError, KeyError):
                    pass  # Skip corrupt cert files

        return team

    @staticmethod
    def list_teams(state_dir: Path = None) -> list:
        """List all persisted teams."""
        base = state_dir or (HARDBOUND_DIR / "teams")
        if not base.exists():
            return []
        teams = []
        for team_dir in sorted(base.iterdir()):
            if team_dir.is_dir() and (team_dir / "team.json").exists():
                try:
                    state = json.loads((team_dir / "team.json").read_text())
                    teams.append({
                        "name": state["name"],
                        "created": state.get("created_at", "unknown"),
                        "members": len(state.get("member_names", [])),
                        "use_tpm": state.get("use_tpm", False),
                    })
                except Exception:
                    teams.append({"name": team_dir.name, "error": "corrupt state"})
        return teams

    # ─── Team Operations ────────────────────────────────────────

    def create(self) -> dict:
        """Create the team with hardware-bound root and admin."""
        # Create team root (SOCIETY type)
        if self.use_tpm:
            self.root = HardwareWeb4Entity.create_with_tpm2(
                EntityType.SOCIETY, self.name, atp_allocation=500.0
            )
        else:
            self.root = HardwareWeb4Entity.create_simulated(
                EntityType.SOCIETY, self.name, atp_allocation=500.0
            )

        # Create admin (HUMAN type, hardware-bound)
        if self.use_tpm:
            self.admin = HardwareWeb4Entity.create_with_tpm2(
                EntityType.HUMAN, f"{self.name}-admin", atp_allocation=200.0
            )
        else:
            self.admin = HardwareWeb4Entity.create_simulated(
                EntityType.HUMAN, f"{self.name}-admin", atp_allocation=200.0
            )

        # Root witnesses admin (binding ceremony)
        self.root.witness(self.admin, "admin_binding")
        self.members[f"{self.name}-admin"] = self.admin

        # Assign roles
        self.roles[f"{self.name}-admin"] = TeamRole.ADMIN

        # Persist state first (creates state_dir)
        self.save()

        # Write genesis entry to hash-chained ledger
        self.ledger.append_genesis(
            team_name=self.name,
            root_lct=self.root.lct_id,
            admin_lct=self.admin.lct_id,
            signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
        )

        # Write initial policy to ledger (versioned from day one)
        initial_policy = TeamPolicy.default()
        self._cached_policy = initial_policy
        self.ledger.append(
            action={"type": "policy_update", "policy": initial_policy.to_dict()},
            signer_lct=self.root.lct_id,
            signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
        )

        # SAL Birth Certificate for the founding admin (first citizen)
        admin_name = f"{self.name}-admin"
        binding_type = "hardware" if isinstance(self.admin, HardwareWeb4Entity) and getattr(self.admin, 'tpm_handle', None) else "software"
        self._generate_birth_certificate(admin_name, self.admin,
                                          TeamRole.ADMIN, binding_type)

        return self.info()

    def add_member(self, name: str, entity_type: str,
                   role: str = None) -> dict:
        """Add a member to the team with a role."""
        etype = EntityType(entity_type)

        # Determine role
        if role is None:
            if etype in (EntityType.AI, EntityType.SERVICE, EntityType.TASK):
                role = TeamRole.AGENT
            elif entity_type == "human":
                role = TeamRole.OPERATOR
            else:
                role = TeamRole.VIEWER

        # Software entities can be spawned as children of the root
        # Hardware entities need their own TPM key
        if entity_type in ("human",) and self.use_tpm:
            member = HardwareWeb4Entity.create_with_tpm2(
                etype, name, atp_allocation=100.0
            )
        elif etype in (EntityType.AI, EntityType.TASK, EntityType.SERVICE):
            # AI/Task/Service entities are software spawns from root
            member = self.root.spawn(etype, name, atp_share=50.0)
            self.members[name] = member
            self.roles[name] = role

            # Log to ledger
            self.ledger.append(
                action={"type": "add_member", "name": name,
                        "entity_type": entity_type, "role": role,
                        "binding": "software"},
                signer_lct=self.root.lct_id,
                signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
            )

            self.save()

            # Generate SAL birth certificate for software spawn
            cert = self._generate_birth_certificate(name, member, role, "software")

            return {
                "name": name, "type": entity_type, "role": role,
                "lct_id": member.lct_id, "level": 4,
                "binding": "software (spawned child)",
                "parent": self.root.lct_id,
                "birth_cert_hash": cert.cert_hash[:16] + "...",
            }
        else:
            member = HardwareWeb4Entity.create_simulated(
                etype, name, atp_allocation=100.0
            )

        # Root witnesses the new member
        self.root.witness(member, "member_binding")
        self.members[name] = member
        self.roles[name] = role

        # Log to ledger
        self.ledger.append(
            action={"type": "add_member", "name": name,
                    "entity_type": entity_type, "role": role,
                    "binding": "hardware" if isinstance(member, HardwareWeb4Entity) else "software"},
            signer_lct=self.root.lct_id,
            signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
        )

        # Persist
        self.save()

        # Generate SAL birth certificate
        binding_type = "hardware" if isinstance(member, HardwareWeb4Entity) and hasattr(member, 'tpm_handle') else "software"
        cert = self._generate_birth_certificate(name, member, role, binding_type)

        return {
            "name": name, "type": entity_type, "role": role,
            "lct_id": member.lct_id if hasattr(member, 'lct_id') else "unknown",
            "level": getattr(member, 'capability_level', 4),
            "binding": binding_type,
            "birth_cert_hash": cert.cert_hash[:16] + "...",
        }

    def _generate_birth_certificate(self, member_name: str, member,
                                     role: str, binding_type: str) -> BirthCertificate:
        """
        Generate a SAL birth certificate for a new team member.

        The birth certificate is the immutable genesis record for a member's
        identity within this team (society). It captures:
        - Who they are (entity LCT)
        - What society they belong to (team root LCT)
        - What role they were born into (citizen role)
        - What law governs them (current policy version)
        - Who witnessed the birth (root entity)
        - What rights and responsibilities they start with
        """
        policy = self._resolve_policy()

        # Get the genesis block reference (current ledger head)
        verify = self.ledger.verify()
        genesis_block = f"block:{verify['entries']}"

        cert = BirthCertificate(
            entity_lct=member.lct_id if hasattr(member, 'lct_id') else f"lct:web4:entity:{member_name}",
            citizen_role=f"lct:web4:role:citizen:{member_name}@{self.name}",
            society_lct=self.root.lct_id if self.root else f"lct:web4:society:{self.name}",
            law_oracle_lct=self.admin.lct_id if self.admin else "",
            law_version=policy.version,
            witnesses=[self.root.lct_id] if self.root else [],
            genesis_block=genesis_block,
            initial_rights=ROLE_INITIAL_RIGHTS.get(role, ["exist", "interact"]),
            initial_responsibilities=ROLE_INITIAL_RESPONSIBILITIES.get(role, ["abide_law"]),
            binding_type=binding_type,
            entity_name=member_name,
            society_name=self.name,
        )

        # Store in memory
        self.birth_certificates[member_name] = cert

        # Persist to disk
        certs_dir = self.state_dir / "members"
        certs_dir.mkdir(parents=True, exist_ok=True)
        safe_name = member_name.replace("/", "_").replace(" ", "_")
        cert_path = certs_dir / f"{safe_name}_birth_cert.json"
        cert_path.write_text(json.dumps(cert.to_dict(), indent=2))

        # Record birth certificate hash in ledger
        self.ledger.append(
            action={
                "type": "sal_birth_certificate",
                "member": member_name,
                "role": role,
                "cert_hash": cert.cert_hash,
                "law_version": cert.law_version,
                "binding": binding_type,
                "rights_count": len(cert.initial_rights),
                "responsibilities_count": len(cert.initial_responsibilities),
            },
            signer_lct=self.root.lct_id if self.root else "",
            signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
        )

        return cert

    def get_birth_certificate(self, member_name: str) -> dict:
        """Get a member's birth certificate."""
        # Check in-memory first
        if member_name in self.birth_certificates:
            cert = self.birth_certificates[member_name]
            return {
                "found": True,
                "valid": cert.verify(),
                "certificate": cert.to_dict(),
            }

        # Try loading from disk
        safe_name = member_name.replace("/", "_").replace(" ", "_")
        cert_path = self.state_dir / "members" / f"{safe_name}_birth_cert.json"
        if cert_path.exists():
            try:
                data = json.loads(cert_path.read_text())
                cert = BirthCertificate.from_dict(data)
                self.birth_certificates[member_name] = cert
                return {
                    "found": True,
                    "valid": cert.verify() and not getattr(cert, '_tampered', False),
                    "certificate": cert.to_dict(),
                }
            except (json.JSONDecodeError, KeyError):
                return {"found": False, "error": "corrupt certificate file"}

        return {"found": False, "error": f"no birth certificate for '{member_name}'"}

    def info(self) -> dict:
        """Get team status."""
        result = {
            "team": self.name,
            "created": self.created_at,
            "hardware_binding": "tpm2" if self.use_tpm else "simulated",
            "state_dir": str(self.state_dir),
        }

        if self.root:
            result["root"] = {
                "lct_id": self.root.lct_id,
                "level": self.root.capability_level,
                "trust_ceiling": self.root.trust_ceiling,
                "coherence": round(self.root.coherence, 4),
                "atp": round(self.root.atp.atp_balance, 1),
                "handle": getattr(self.root, 'tpm_handle', None),
            }

        if self.admin:
            result["admin"] = {
                "lct_id": self.admin.lct_id,
                "level": getattr(self.admin, 'capability_level', 4),
                "coherence": round(self.admin.coherence, 4),
            }

        result["members"] = []
        for name, member in self.members.items():
            m_info = {
                "name": name,
                "type": member.entity_type.value if hasattr(member, 'entity_type') else "unknown",
                "role": self.roles.get(name, "unknown"),
                "level": getattr(member, 'capability_level', 4),
                "coherence": round(member.coherence, 4),
            }
            if hasattr(member, 't3'):
                m_info["t3"] = member.t3.to_dict()
            if hasattr(member, 'v3'):
                m_info["v3"] = member.v3.to_dict()
            result["members"].append(m_info)

        # Heartbeat info
        result["heartbeat"] = self.heartbeat.to_dict()

        # Team ATP pool
        result["team_atp"] = {
            "balance": round(self.team_atp, 2),
            "max": round(self.team_atp_max, 2),
            "discharged": round(self.team_adp_discharged, 2),
            "recharged": round(self.heartbeat.total_recharged, 2),
            "net_flow": round(self.heartbeat.total_recharged - self.team_adp_discharged, 2),
            "utilization": round(self.team_adp_discharged / self.team_atp_max * 100, 1)
                           if self.team_atp_max > 0 else 0.0,
        }

        # Birth certificates
        result["birth_certificates"] = len(self.birth_certificates)

        # Ledger info
        result["ledger"] = {
            "entries": self.ledger.count(),
            "pending": len(self.action_log),
        }

        # Policy info (from ledger)
        policy = self._resolve_policy()
        result["policy"] = {
            "version": policy.version,
            "admin_only_actions": len(policy.admin_only),
            "operator_min_actions": len(policy.operator_min),
            "multi_sig_actions": len(policy.multi_sig),
            "custom_rules": len(policy.custom_rules),
            "source": "ledger" if self.ledger.active_policy() else "default",
        }

        # Multi-sig pending requests
        msig = self.multi_sig_buffer.to_dict()
        if msig["pending_count"] > 0:
            result["pending_multi_sig"] = msig

        return result

    def _resolve_policy(self) -> TeamPolicy:
        """
        Resolve the active policy from the ledger (with caching).

        If no policy exists in the ledger, returns the default policy.
        Cache is invalidated when a policy_update is appended.
        Integrity hash detects direct cache tampering (attack vector 3.3).
        """
        if self._cached_policy is not None:
            if self._cached_policy.verify_integrity():
                return self._cached_policy
            # Cache was tampered with — re-derive from ledger
            self._cached_policy = None

        policy_data = self.ledger.active_policy()
        if policy_data:
            self._cached_policy = TeamPolicy.from_dict(policy_data)
        else:
            self._cached_policy = TeamPolicy.default()
        return self._cached_policy

    def update_policy(self, admin_name: str, changes: dict) -> dict:
        """
        Update the team policy (admin-only meta-governance action).

        Args:
            admin_name: Name of the admin making the change
            changes: Dict with optional keys:
                - add_admin_only: list of actions to add to admin_only
                - remove_admin_only: list of actions to remove from admin_only
                - add_operator_min: list of actions to add to operator_min
                - remove_operator_min: list of actions to remove from operator_min
                - set_custom_rule: {"name": "...", "value": "..."}

        Returns:
            Result dict with new policy version
        """
        # Only admin can update policy
        role = self.roles.get(admin_name, TeamRole.VIEWER)
        if role != TeamRole.ADMIN:
            return {"error": f"policy update requires admin role (actor has '{role}')",
                    "denied": True}

        # Resolve current policy
        current = self._resolve_policy()

        # Apply changes
        new_admin_only = set(current.admin_only)
        new_operator_min = set(current.operator_min)
        new_custom = dict(current.custom_rules)

        for action in changes.get("add_admin_only", []):
            new_admin_only.add(action)
        for action in changes.get("remove_admin_only", []):
            new_admin_only.discard(action)
        for action in changes.get("add_operator_min", []):
            new_operator_min.add(action)
        for action in changes.get("remove_operator_min", []):
            new_operator_min.discard(action)
        if "set_custom_rule" in changes:
            rule = changes["set_custom_rule"]
            new_custom[rule["name"]] = rule["value"]

        # Action cost changes
        new_action_costs = dict(current.action_costs)
        for action, cost in changes.get("set_action_costs", {}).items():
            new_action_costs[action] = float(cost)

        # Multi-sig requirement changes
        new_multi_sig = dict(current.multi_sig)
        for action, req in changes.get("set_multi_sig", {}).items():
            if req is None:
                new_multi_sig.pop(action, None)  # Remove requirement
            else:
                new_multi_sig[action] = req
        for action in changes.get("remove_multi_sig", []):
            new_multi_sig.pop(action, None)

        new_policy = TeamPolicy(
            version=current.version + 1,
            admin_only=new_admin_only,
            operator_min=new_operator_min,
            custom_rules=new_custom,
            action_costs=new_action_costs,
            multi_sig=new_multi_sig,
        )

        # Write to ledger
        admin_entity = self.members.get(admin_name)
        self.ledger.append(
            action={"type": "policy_update", "policy": new_policy.to_dict()},
            signer_lct=admin_entity.lct_id if admin_entity else "",
            signer_entity=admin_entity if isinstance(admin_entity, HardwareWeb4Entity) else None,
        )

        # Invalidate cache
        self._cached_policy = new_policy

        return {
            "policy_version": new_policy.version,
            "admin_only_count": len(new_policy.admin_only),
            "operator_min_count": len(new_policy.operator_min),
            "custom_rules": len(new_policy.custom_rules),
            "changes_applied": changes,
        }

    def check_authorization(self, actor_name: str, action: str) -> dict:
        """
        Check if an actor is authorized for an action based on their role
        and the active policy from the ledger.

        Returns:
            {"authorized": bool, "reason": str, "requires_approval": bool,
             "approver_role": str or None, "policy_version": int}
        """
        role = self.roles.get(actor_name, TeamRole.VIEWER)
        policy = self._resolve_policy()

        # Admin can do anything
        if role == TeamRole.ADMIN:
            return {"authorized": True, "reason": "admin privilege",
                    "requires_approval": False, "approver_role": None,
                    "policy_version": policy.version}

        # Check admin-only actions (from ledger policy)
        if action in policy.admin_only:
            if role != TeamRole.ADMIN:
                return {"authorized": False,
                        "reason": f"'{action}' requires admin role (actor has '{role}')",
                        "requires_approval": True, "approver_role": TeamRole.ADMIN,
                        "policy_version": policy.version}

        # Check operator-min actions (from ledger policy)
        if action in policy.operator_min:
            if role not in (TeamRole.ADMIN, TeamRole.OPERATOR):
                return {"authorized": False,
                        "reason": f"'{action}' requires operator role (actor has '{role}')",
                        "requires_approval": True, "approver_role": TeamRole.OPERATOR,
                        "policy_version": policy.version}

        # Viewer can't act
        if role == TeamRole.VIEWER:
            return {"authorized": False,
                    "reason": "viewer role cannot execute actions",
                    "requires_approval": True, "approver_role": TeamRole.OPERATOR,
                    "policy_version": policy.version}

        # Agent and operator can execute non-restricted actions
        return {"authorized": True, "reason": f"permitted for role '{role}'",
                "requires_approval": False, "approver_role": None,
                "policy_version": policy.version}

    def _handle_multi_sig(self, actor_name: str, action: str,
                          record: dict, requirement: dict,
                          approved_by: str = None) -> dict:
        """
        Handle multi-sig approval flow.

        If no pending request exists, create one with the actor as first approver.
        If a pending request exists, add the actor (or approved_by) as approver.
        If quorum is met, execute the action.
        """
        required = requirement.get("required", 2)
        eligible_roles = requirement.get("eligible_roles", ["admin"])

        # Find existing pending request for this action
        pending = self.multi_sig_buffer.find_pending(action)

        if pending is None:
            # Create new multi-sig request — actor is first approver
            pending = self.multi_sig_buffer.create_request(
                actor_name, action, required, eligible_roles
            )
            # Actor approves their own request
            actor_role = self.roles.get(actor_name, "viewer")
            result = pending.add_approval(actor_name, actor_role)

            if result.get("ineligible"):
                record["decision"] = "denied"
                record["reason"] = f"multi-sig: {result['error']}"
                self.action_log.append(record)
                self.save()
                return record

            # Also add approved_by if provided
            if approved_by and approved_by != actor_name:
                approver_role = self.roles.get(approved_by, "viewer")
                pending.add_approval(approved_by, approver_role)

            if pending.is_quorum_met:
                # Quorum met immediately (enough approvers provided)
                return self._execute_multi_sig(pending, record)

            # Still need more approvals
            record["decision"] = "pending_multi_sig"
            record["multi_sig"] = {
                "request_id": pending.request_id,
                "approvals": pending.approval_count,
                "required": required,
                "remaining": required - pending.approval_count,
                "eligible_roles": eligible_roles,
            }
            # Log the pending request to ledger
            self.ledger.append(
                action={
                    "type": "multi_sig_request",
                    "request_id": pending.request_id,
                    "actor": actor_name,
                    "action": action,
                    "required": required,
                    "approvals": [a["approver"] for a in pending.approvals],
                },
                signer_lct=self.members[actor_name].lct_id if actor_name in self.members else "",
                signer_entity=self.members.get(actor_name),
            )
            return record

        else:
            # Existing pending request — add approval
            approver = approved_by or actor_name
            approver_role = self.roles.get(approver, "viewer")
            result = pending.add_approval(approver, approver_role)

            if result.get("duplicate"):
                record["decision"] = "denied"
                record["reason"] = f"multi-sig: {result['error']}"
                return record

            if result.get("ineligible"):
                record["decision"] = "denied"
                record["reason"] = f"multi-sig: {result['error']}"
                return record

            if pending.is_quorum_met:
                return self._execute_multi_sig(pending, record)

            # Still need more
            record["decision"] = "pending_multi_sig"
            record["multi_sig"] = {
                "request_id": pending.request_id,
                "approvals": pending.approval_count,
                "required": pending.required,
                "remaining": pending.required - pending.approval_count,
                "new_approver": approver,
            }
            # Log the approval to ledger
            self.ledger.append(
                action={
                    "type": "multi_sig_approval",
                    "request_id": pending.request_id,
                    "approver": approver,
                    "approvals_so_far": pending.approval_count,
                    "required": pending.required,
                },
                signer_lct=self.members[approver].lct_id if approver in self.members else "",
                signer_entity=self.members.get(approver),
            )
            return record

    def _execute_multi_sig(self, pending: MultiSigRequest, record: dict) -> dict:
        """Execute an action that has met its multi-sig quorum."""
        pending.executed = True
        actor_name = pending.actor
        action = pending.action
        member = self.members.get(actor_name)

        policy = self._resolve_policy()
        action_cost = policy.get_cost(action)
        record["action_cost_policy"] = action_cost
        record["multi_sig_quorum_met"] = True
        record["multi_sig_approvals"] = [a["approver"] for a in pending.approvals]

        # Check team ATP pool
        if self.team_atp < action_cost:
            record["decision"] = "denied"
            record["reason"] = f"team ATP pool exhausted ({self.team_atp:.1f} remaining, need {action_cost:.1f})"
            self.action_log.append(record)
            self.save()
            return record

        # Execute
        request = R6Request(
            rules="team-policy-v1",
            role=member.lct_id if member and hasattr(member, 'lct_id') else "unknown",
            request=action,
            resource_estimate=action_cost,
        )

        result = member.act(request) if member else None
        if result:
            record["decision"] = result.decision.value
            record["atp_cost"] = result.atp_consumed

            if result.decision == R6Decision.APPROVED and result.atp_consumed > 0:
                self.team_atp -= result.atp_consumed
                self.team_adp_discharged += result.atp_consumed
                record["team_atp_remaining"] = round(self.team_atp, 2)

                atp_ratio = self.team_atp / self.team_atp_max if self.team_atp_max > 0 else 0
                if atp_ratio < 0.1:
                    new_state = "crisis"
                elif atp_ratio < 0.3:
                    new_state = "rest"
                elif atp_ratio > 0.8:
                    new_state = "focus"
                else:
                    new_state = "wake"
                transition = self.heartbeat.transition(new_state)
                if transition:
                    record["metabolic_transition"] = transition

            if isinstance(member, HardwareWeb4Entity) and result.decision == R6Decision.APPROVED:
                record["hw_signed"] = True
        else:
            record["decision"] = "approved"
            record["atp_cost"] = action_cost

        # Log execution to ledger
        self.action_log.append(record)
        self.save()

        # Log the multi-sig execution
        self.ledger.append(
            action={
                "type": "multi_sig_executed",
                "request_id": pending.request_id,
                "action": action,
                "actor": actor_name,
                "approvers": [a["approver"] for a in pending.approvals],
                "decision": record.get("decision", "unknown"),
            },
            signer_lct=member.lct_id if member and hasattr(member, 'lct_id') else "",
            signer_entity=member if isinstance(member, HardwareWeb4Entity) else None,
        )

        return record

    def approve_multi_sig(self, approver_name: str, request_id: str = None,
                          action: str = None) -> dict:
        """
        Approve a pending multi-sig request.

        Find by request_id or by action name.
        """
        pending = None
        if request_id:
            pending = self.multi_sig_buffer.pending.get(request_id)
        elif action:
            pending = self.multi_sig_buffer.find_pending(action)

        if not pending:
            return {"error": "no pending multi-sig request found",
                    "request_id": request_id, "action": action}

        if pending.is_expired:
            return {"error": "multi-sig request expired",
                    "request_id": pending.request_id}

        approver_role = self.roles.get(approver_name, "viewer")
        result = pending.add_approval(approver_name, approver_role)

        if result.get("error"):
            return result

        if pending.is_quorum_met:
            record = {
                "type": "action",
                "actor": pending.actor,
                "action": pending.action,
                "role": self.roles.get(pending.actor, "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return self._execute_multi_sig(pending, record)

        return {
            "approved_by": approver_name,
            "request_id": pending.request_id,
            "approvals": pending.approval_count,
            "required": pending.required,
            "remaining": pending.required - pending.approval_count,
            "status": "pending",
        }

    # ─── Reputation Engine ──────────────────────────────────────

    # Quality map: action type → base quality score
    # Higher for more impactful/difficult actions
    ACTION_QUALITY = {
        "approve_deployment": 0.8,
        "emergency_shutdown": 0.9,
        "rotate_credentials": 0.7,
        "set_resource_limit": 0.6,
        "deploy_staging": 0.7,
        "run_migration": 0.8,
        "scale_service": 0.6,
        "update_config": 0.5,
        "restart_service": 0.5,
        "run_analysis": 0.5,
        "review_pr": 0.6,
        "execute_review": 0.4,
        "run_diagnostics": 0.4,
        "validate_schema": 0.4,
        "analyze_dataset": 0.6,
    }
    DEFAULT_QUALITY = 0.5

    def _compute_reputation_delta(self, member, action: str,
                                   decision: R6Decision,
                                   action_cost: float) -> dict:
        """
        Compute T3/V3 reputation delta from action outcome.

        Uses EMA (Exponential Moving Average) approach from web4_entity.py:
        - Success → trust increases toward quality target
        - Denial → slight decrease (behavioral signal)
        - Higher-cost actions have stronger signal

        Returns delta dict for ledger recording, or None if no change.
        """
        success = (decision == R6Decision.APPROVED)
        quality = self.ACTION_QUALITY.get(action, self.DEFAULT_QUALITY)

        # Scale quality by action cost (expensive actions matter more)
        # Normalize: 10 ATP = 1.0x, 50 ATP = 1.5x, 3 ATP = 0.7x
        cost_multiplier = min(1.5, max(0.5, action_cost / 20.0))
        effective_quality = min(1.0, quality * cost_multiplier)

        # Snapshot before
        t3_before = {
            "talent": round(member.t3.talent, 4),
            "training": round(member.t3.training, 4),
            "temperament": round(member.t3.temperament, 4),
        }
        v3_before = {
            "valuation": round(member.v3.valuation, 4),
            "veracity": round(member.v3.veracity, 4),
            "validity": round(member.v3.validity, 4),
        }
        coherence_before = round(member.coherence, 4)

        # Apply T3 update
        member.t3.update_from_outcome(success, effective_quality)

        # Apply V3 update
        # value_created: proportional to quality on success, 0 on denial
        value_created = effective_quality * 0.8 if success else 0.0
        # accurate: successful actions are considered accurate
        member.v3.update_from_outcome(value_created, accurate=success)

        # Snapshot after
        t3_after = {
            "talent": round(member.t3.talent, 4),
            "training": round(member.t3.training, 4),
            "temperament": round(member.t3.temperament, 4),
        }
        v3_after = {
            "valuation": round(member.v3.valuation, 4),
            "veracity": round(member.v3.veracity, 4),
            "validity": round(member.v3.validity, 4),
        }
        coherence_after = round(member.coherence, 4)

        # Compute deltas
        t3_delta = {
            k: round(t3_after[k] - t3_before[k], 4)
            for k in t3_before
        }
        v3_delta = {
            k: round(v3_after[k] - v3_before[k], 4)
            for k in v3_before
        }

        return {
            "success": success,
            "quality": round(effective_quality, 3),
            "t3_delta": t3_delta,
            "v3_delta": v3_delta,
            "t3_composite": round(member.t3.composite(), 4),
            "v3_composite": round(member.v3.composite(), 4),
            "coherence_before": coherence_before,
            "coherence_after": coherence_after,
            "coherence_delta": round(coherence_after - coherence_before, 4),
        }

    def recharge(self, force: bool = False) -> dict:
        """
        Apply metabolic ATP recharge based on elapsed time and heartbeat state.

        Recharge happens automatically on each heartbeat tick. Call this
        to manually trigger a recharge check (e.g., before an action).

        Returns recharge record or None if no recharge occurred.
        """
        elapsed = self.heartbeat.seconds_since_last()
        recharge_amount = self.heartbeat.compute_recharge(elapsed)

        if recharge_amount <= 0 and not force:
            return None

        # Apply recharge up to max
        headroom = self.team_atp_max - self.team_atp
        actual = min(recharge_amount, headroom)

        if actual <= 0:
            return None

        self.team_atp += actual
        self.heartbeat.total_recharged += actual

        return {
            "recharged": round(actual, 2),
            "elapsed_seconds": round(elapsed, 1),
            "metabolic_state": self.heartbeat.state,
            "recharge_rate": self.heartbeat.recharge_rate,
            "team_atp_after": round(self.team_atp, 2),
        }

    def _save_state_only(self):
        """Save entity and team state without flushing actions to ledger."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        members_dir = self.state_dir / "members"
        members_dir.mkdir(exist_ok=True)

        team_state = {
            "name": self.name,
            "created_at": self.created_at,
            "use_tpm": self.use_tpm,
            "member_names": list(self.members.keys()),
            "roles": self.roles,
            "team_atp": round(self.team_atp, 2),
            "team_atp_max": round(self.team_atp_max, 2),
            "team_adp_discharged": round(self.team_adp_discharged, 2),
            "total_recharged": round(self.heartbeat.total_recharged, 2),
        }
        if self.root:
            team_state["root"] = self._entity_to_state(self.root)
        if self.admin:
            team_state["admin_name"] = f"{self.name}-admin"

        (self.state_dir / "team.json").write_text(
            json.dumps(team_state, indent=2)
        )

        for name, member in self.members.items():
            member_state = self._entity_to_state(member)
            safe_name = name.replace("/", "_").replace(" ", "_")
            (members_dir / f"{safe_name}.json").write_text(
                json.dumps(member_state, indent=2)
            )

        # Persist multi-sig pending requests
        self.multi_sig_buffer.save(self.state_dir / "multi_sig_pending.json")

    def _flush_heartbeat_block(self):
        """
        Flush pending heartbeat actions as a ledger block.

        All queued actions are written as a single "block" entry, then
        the heartbeat timer resets. Individual actions within the block
        are preserved in the block's action list.
        """
        actions = self.heartbeat.flush()

        if not actions:
            return

        # Apply recharge on heartbeat tick
        recharge_record = self.recharge()

        # Write individual actions to ledger (preserves per-action granularity)
        for action_record in actions:
            actor_name = action_record.get("actor", "")
            signer = self.members.get(actor_name)
            self.ledger.append(
                action=action_record,
                signer_lct=signer.lct_id if signer and hasattr(signer, 'lct_id') else "",
                signer_entity=signer if isinstance(signer, HardwareWeb4Entity) else None,
            )

        # Write block metadata entry
        self.ledger.append(
            action={
                "type": "heartbeat_block",
                "block_number": self.heartbeat.blocks_written,
                "actions_count": len(actions),
                "metabolic_state": self.heartbeat.state,
                "heartbeat_interval": self.heartbeat.interval,
                "recharge": recharge_record,
            },
            signer_lct=self.root.lct_id if self.root else "",
            signer_entity=self.root if isinstance(self.root, HardwareWeb4Entity) else None,
        )

        # Clear action_log (already flushed)
        self.action_log = [a for a in self.action_log if a not in actions]

        # Save state
        self._save_state_only()

    def flush(self):
        """Force-flush any pending actions (e.g., before shutdown)."""
        if self.heartbeat.pending_actions:
            self._flush_heartbeat_block()
        # Also flush any remaining action_log entries via save()
        self.save()

    def sign_action(self, actor_name: str, action: str,
                    approved_by: str = None) -> dict:
        """
        Sign an R6 action with role-based authorization.

        If the action requires higher privileges, `approved_by` must be
        the name of an authorized approver (e.g., the admin).
        """
        member = self.members.get(actor_name)
        if not member:
            return {"error": f"Member '{actor_name}' not found"}

        # Apply metabolic recharge before action (time-based recovery)
        recharge_record = self.recharge()

        # Check authorization
        auth = self.check_authorization(actor_name, action)
        record = {
            "type": "action",
            "actor": actor_name,
            "action": action,
            "role": self.roles.get(actor_name, "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Record recharge if it happened
        if recharge_record:
            record["pre_action_recharge"] = recharge_record

        if not auth["authorized"]:
            # Check if an approver was provided
            if approved_by:
                approver_auth = self.check_authorization(approved_by, action)
                if approver_auth["authorized"]:
                    record["approved_by"] = approved_by
                    record["approval_reason"] = "delegated by " + approved_by
                else:
                    record["decision"] = "denied"
                    record["reason"] = auth["reason"]
                    record["denied_approver"] = approved_by
                    self.action_log.append(record)
                    self.save()
                    return record
            else:
                record["decision"] = "denied"
                record["reason"] = auth["reason"]
                record["required_approver"] = auth["approver_role"]
                self.action_log.append(record)
                self.save()
                return record

        # Check multi-sig requirements
        policy = self._resolve_policy()
        multi_sig_req = policy.requires_multi_sig(action)
        if multi_sig_req:
            return self._handle_multi_sig(
                actor_name, action, record, multi_sig_req,
                approved_by=approved_by
            )

        # Get action cost from policy (not hardcoded)
        action_cost = policy.get_cost(action)
        record["action_cost_policy"] = action_cost

        # Check team ATP pool before executing
        if self.team_atp < action_cost:
            record["decision"] = "denied"
            record["reason"] = f"team ATP pool exhausted ({self.team_atp:.1f} remaining, need {action_cost:.1f})"
            self.action_log.append(record)
            self.save()
            return record

        # Execute the action
        request = R6Request(
            rules="team-policy-v1",
            role=member.lct_id if hasattr(member, 'lct_id') else "unknown",
            request=action,
            resource_estimate=action_cost,
        )

        result = member.act(request)
        record["decision"] = result.decision.value
        record["atp_cost"] = result.atp_consumed

        # Debit team pool on successful actions
        if result.decision == R6Decision.APPROVED and result.atp_consumed > 0:
            self.team_atp -= result.atp_consumed
            self.team_adp_discharged += result.atp_consumed
            record["team_atp_remaining"] = round(self.team_atp, 2)

            # Update team metabolic state based on ATP ratio
            atp_ratio = self.team_atp / self.team_atp_max if self.team_atp_max > 0 else 0
            if atp_ratio < 0.1:
                new_state = "crisis"
            elif atp_ratio < 0.3:
                new_state = "rest"
            elif atp_ratio > 0.8:
                new_state = "focus"
            else:
                new_state = "wake"
            transition = self.heartbeat.transition(new_state)
            if transition:
                record["metabolic_transition"] = transition

        if isinstance(member, HardwareWeb4Entity) and result.decision == R6Decision.APPROVED:
            record["hw_signed"] = True
            record["signed_actions"] = len(member.signed_actions)

        # ─── Reputation Delta: Update T3/V3 from action outcome ───
        reputation_delta = self._compute_reputation_delta(
            member, action, result.decision, action_cost
        )
        if reputation_delta:
            record["reputation_delta"] = reputation_delta

        self.action_log.append(record)

        # Heartbeat-driven block aggregation:
        # Queue action in heartbeat buffer; flush when heartbeat fires
        self.heartbeat.queue_action(record)

        if self.heartbeat.should_flush() or self.heartbeat.state == "crisis":
            # Heartbeat tick: flush all pending actions as a block
            self._flush_heartbeat_block()
        else:
            # Still save entity state (ATP balances etc) but don't flush to ledger
            self._save_state_only()

        return record


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_team_create(args):
    """Create a new team."""
    team = HardboundTeam(args.name, use_tpm=not args.no_tpm)
    result = team.create()
    print(json.dumps(result, indent=2))
    return team


def cmd_team_info(args):
    """Show team info (loads from disk)."""
    try:
        team = HardboundTeam.load(args.name)
        print(json.dumps(team.info(), indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_list(args):
    """List all teams."""
    teams = HardboundTeam.list_teams()
    print(json.dumps({"teams": teams}, indent=2))


def cmd_team_add_member(args):
    """Add a member to an existing team."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.add_member(args.name, args.type)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_sign(args):
    """Sign an action within a team."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.sign_action(args.actor, args.action)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_actions(args):
    """Show action log from the hash-chained ledger."""
    team_dir = HARDBOUND_DIR / "teams" / args.team
    ledger = TeamLedger(team_dir / "ledger.jsonl")

    limit = args.limit if hasattr(args, 'limit') else 20
    entries = ledger.tail(limit)

    print(json.dumps({
        "team": args.team,
        "total_entries": ledger.count(),
        "showing_last": len(entries),
        "entries": entries,
    }, indent=2))


def cmd_team_verify(args):
    """Verify the team's hash-chained ledger."""
    team_dir = HARDBOUND_DIR / "teams" / args.team
    ledger = TeamLedger(team_dir / "ledger.jsonl")

    result = ledger.verify()
    result["team"] = args.team
    print(json.dumps(result, indent=2))


def cmd_team_analytics(args):
    """Show team ledger analytics."""
    team_dir = HARDBOUND_DIR / "teams" / args.team
    ledger = TeamLedger(team_dir / "ledger.jsonl")

    result = ledger.analytics()
    result["team"] = args.team
    print(json.dumps(result, indent=2))


def cmd_team_approve(args):
    """Approve a pending multi-sig request."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.approve_multi_sig(
            args.approver,
            request_id=getattr(args, 'request_id', None),
            action=getattr(args, 'action', None),
        )
        print(json.dumps(result, indent=2, default=str))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_recharge(args):
    """Manually trigger ATP recharge for a team."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.recharge(force=True)
        if result:
            team.save()
            result["team"] = args.team
        else:
            result = {
                "team": args.team,
                "recharged": 0,
                "reason": "pool at max or zero recharge rate",
                "team_atp": round(team.team_atp, 2),
                "team_atp_max": round(team.team_atp_max, 2),
                "metabolic_state": team.heartbeat.state,
            }
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_birth_cert(args):
    """Show a member's SAL birth certificate."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.get_birth_certificate(args.member)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_query(args):
    """Query team ledger entries."""
    team_dir = HARDBOUND_DIR / "teams" / args.team
    ledger = TeamLedger(team_dir / "ledger.jsonl")

    results = ledger.query(
        actor=getattr(args, 'actor', None),
        action_type=getattr(args, 'type', None),
        decision=getattr(args, 'decision', None),
        hw_only=getattr(args, 'hw_only', False),
        limit=getattr(args, 'limit', 20),
    )

    print(json.dumps({
        "team": args.team,
        "matches": len(results),
        "entries": results,
    }, indent=2))


def cmd_entity_create(args):
    """Create a standalone entity."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type, use_tpm=use_tpm)
    status = entity.status()
    print(json.dumps(status, indent=2, default=str))


def cmd_entity_sign(args):
    """Sign an action with an entity's hardware key."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type or "ai", use_tpm=use_tpm)

    request = R6Request(
        rules="cli-policy-v1",
        role=entity.lct_id,
        request=args.action,
        resource_estimate=5.0,
    )
    result = entity.act(request)
    print(json.dumps({
        "entity": args.name,
        "action": args.action,
        "decision": result.decision.value,
        "hw_signed": len(entity.signed_actions) > 0,
        "signed_actions": len(entity.signed_actions),
        "atp_remaining": round(entity.atp.atp_balance, 1),
    }, indent=2))


def cmd_avp_prove(args):
    """Run AVP aliveness proof."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type or "ai", use_tpm=use_tpm)

    proof = entity.prove_aliveness("cli-verifier", "cli-check")
    print(json.dumps(proof, indent=2, default=str))


def cmd_avp_attest(args):
    """Get TPM2 attestation."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name or "attest-check", args.type or "ai", use_tpm=use_tpm)

    attestation = entity.get_attestation()
    print(json.dumps(attestation, indent=2, default=str))


def cmd_ek_info(args):
    """Show EK certificate info."""
    try:
        from core.lct_binding.ek_attestation import EKAttestationProvider
        provider = EKAttestationProvider()
        identity = provider.get_platform_identity()
        print(json.dumps(identity.to_dict(), indent=2))
        provider.cleanup()
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_ek_verify(args):
    """Verify EK certificate chain."""
    try:
        from core.lct_binding.ek_attestation import EKAttestationProvider
        provider = EKAttestationProvider()
        bundle = provider.create_attestation_bundle()
        print(json.dumps(bundle, indent=2))
        provider.cleanup()
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_status(args):
    """Show full system status."""
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tpm2_available": detect_tpm2(),
        "teams": HardboundTeam.list_teams(),
    }

    if status["tpm2_available"]:
        try:
            from core.lct_binding.tpm2_provider import TPM2Provider
            provider = TPM2Provider()
            info = provider.get_platform_info()
            status["platform"] = info.to_dict()
        except Exception as e:
            status["platform_error"] = str(e)

        try:
            from core.lct_binding.ek_attestation import EKAttestationProvider
            ek = EKAttestationProvider()
            identity = ek.get_platform_identity()
            status["ek_identity"] = identity.to_dict()
            ek.cleanup()
        except Exception as e:
            status["ek_error"] = str(e)

    print(json.dumps(status, indent=2))


# ═══════════════════════════════════════════════════════════════
# Interactive Demo
# ═══════════════════════════════════════════════════════════════

def demo():
    """Interactive demo showing Hardbound CLI with hash-chained ledger and role-based governance."""
    import shutil

    print("=" * 65)
    print("  HARDBOUND CLI — Enterprise Team Governance")
    print("  Hash-chained ledger + Role-based authorization + TPM2")
    print("=" * 65)

    tpm_available = detect_tpm2()
    print(f"\n  TPM2: {'available (real hardware)' if tpm_available else 'not available (simulation mode)'}")
    print(f"  State dir: {HARDBOUND_DIR}/teams/")

    # Clean up previous demo
    demo_dir = HARDBOUND_DIR / "teams" / "acme-ai-ops"
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    # ─── Create team ───
    print("\n--- Creating Team ---")
    team = HardboundTeam("acme-ai-ops", use_tpm=tpm_available)
    result = team.create()
    print(f"  Team: {result['team']}")
    print(f"  Hardware: {result['hardware_binding']}")
    print(f"  Root LCT: {result['root']['lct_id'][:40]}...")
    level = result['root']['level']
    print(f"  Root level: {level} ({'HARDWARE' if level == 5 else 'SOFTWARE'})")
    print(f"  Genesis ledger entry written")
    print(f"  Ledger entries: {team.ledger.count()}")

    # ─── Add members with roles ───
    print("\n--- Adding Team Members (with roles) ---")

    members_to_add = [
        ("data-analyst-agent", "ai", TeamRole.AGENT),
        ("code-review-agent", "ai", TeamRole.AGENT),
        ("deploy-service", "service", TeamRole.OPERATOR),
        ("qa-engineer", "human", TeamRole.OPERATOR),
    ]

    for name, mtype, role in members_to_add:
        info = team.add_member(name, mtype, role=role)
        cert_hash = info.get('birth_cert_hash', 'n/a')
        print(f"  Added: {name:25s} ({mtype:7s}) role={info.get('role'):10s} cert={cert_hash}")

    # ─── SAL Birth Certificates ───
    print("\n--- SAL Birth Certificates ---")
    print(f"  Certificates issued: {len(team.birth_certificates)}")
    for member_name, cert in team.birth_certificates.items():
        print(f"\n  [{member_name}]")
        print(f"    Citizen role: {cert.citizen_role}")
        print(f"    Society: {cert.society_name}")
        print(f"    Law version: {cert.law_version}")
        print(f"    Binding: {cert.binding_type}")
        print(f"    Rights: {', '.join(cert.initial_rights[:4])}{'...' if len(cert.initial_rights) > 4 else ''}")
        print(f"    Responsibilities: {', '.join(cert.initial_responsibilities[:3])}{'...' if len(cert.initial_responsibilities) > 3 else ''}")
        print(f"    Witnesses: {len(cert.witnesses)}")
        print(f"    Cert hash: {cert.cert_hash[:24]}...")
        print(f"    Integrity: {'VALID' if cert.verify() else 'TAMPERED'}")

    # ─── Team status with roles ───
    print("\n--- Team Status ---")
    info = team.info()
    print(f"  Members: {len(info['members'])}")
    for m in info['members']:
        print(f"    {m['name']:25s} | {m['type']:12s} | role={m['role']:10s} | level={m['level']}")
    print(f"  Ledger entries: {info['ledger']['entries']}")

    # ─── Authorized actions ───
    print("\n--- Role-Based Actions ---")

    # Admin actions (should succeed)
    admin = f"{team.name}-admin"
    for action in ["approve_deployment", "set_resource_limit"]:
        record = team.sign_action(admin, action)
        hw = "HW" if record.get("hw_signed") else "SW"
        print(f"  [{hw}] {admin:25s} → {action:22s} : {record['decision']}")

    # Agent actions (permitted non-restricted)
    for actor, action in [("data-analyst-agent", "run_analysis"),
                          ("code-review-agent", "review_pr")]:
        record = team.sign_action(actor, action)
        print(f"  [SW] {actor:25s} → {action:22s} : {record['decision']}")

    # Operator action (permitted)
    record = team.sign_action("deploy-service", "deploy_staging")
    print(f"  [SW] {'deploy-service':25s} → {'deploy_staging':22s} : {record['decision']}")

    # ─── Authorization denial ───
    print("\n--- Role-Based Denial ---")

    # Agent tries admin-only action (should be denied)
    record = team.sign_action("data-analyst-agent", "approve_deployment")
    print(f"  Agent → approve_deployment: {record['decision']}")
    print(f"    Reason: {record.get('reason', 'n/a')}")

    # Agent tries with admin approval (should succeed)
    record = team.sign_action("data-analyst-agent", "approve_deployment",
                              approved_by=admin)
    print(f"  Agent → approve_deployment (approved by admin): {record['decision']}")

    # ─── Policy-from-Ledger ───
    print("\n--- Policy-from-Ledger ---")
    policy = team._resolve_policy()
    print(f"  Active policy version: {policy.version}")
    print(f"  Admin-only actions: {len(policy.admin_only)}")
    print(f"  Source: {'ledger' if team.ledger.active_policy() else 'default'}")

    # Agent tries 'restart_service' — currently requires operator
    record = team.sign_action("data-analyst-agent", "restart_service")
    print(f"\n  Agent → restart_service (before policy change): {record['decision']}")
    print(f"    Reason: {record.get('reason', 'authorized')}")

    # Admin updates policy: move 'restart_service' to agent-accessible
    result = team.update_policy(admin, {
        "remove_operator_min": ["restart_service"],
    })
    print(f"\n  Policy updated to v{result['policy_version']}")
    print(f"  Removed 'restart_service' from operator-min")

    # Same agent tries again — now allowed
    record = team.sign_action("data-analyst-agent", "restart_service")
    print(f"  Agent → restart_service (after policy change): {record['decision']}")

    # Also add a custom admin-only action
    result = team.update_policy(admin, {
        "add_admin_only": ["delete_team_data"],
        "set_custom_rule": {"name": "max_delegation_depth", "value": "3"},
    })
    print(f"\n  Policy updated to v{result['policy_version']}")
    print(f"  Added 'delete_team_data' to admin-only")

    # Historical policy query
    policy_at_genesis = team.ledger.policy_at_sequence(2)
    policy_at_latest = team.ledger.active_policy()
    print(f"\n  Policy at seq 2: v{policy_at_genesis['version']} ({len(policy_at_genesis['admin_only'])} admin-only)")
    print(f"  Current policy:  v{policy_at_latest['version']} ({len(policy_at_latest['admin_only'])} admin-only)")

    # ─── Ledger verification ───
    # Force-flush any buffered actions before verifying
    team.flush()
    print("\n--- Ledger Verification ---")
    verification = team.ledger.verify()
    print(f"  Chain valid: {verification['valid']}")
    print(f"  Total entries: {verification['entries']}")
    print(f"  HW-signed entries: {verification['hw_signed']}")
    print(f"  Chain breaks: {verification['breaks']}")
    print(f"  Head hash: {verification['head_hash'][:16]}...")

    # Show last few ledger entries
    print("\n--- Last 3 Ledger Entries ---")
    for entry in team.ledger.tail(3):
        action = entry.get("action", {})
        hw = "HW" if entry.get("hw_signed") else "SW"
        print(f"  #{entry['sequence']:3d} [{hw}] {action.get('type', action.get('action', '?')):20s} "
              f"prev={entry['prev_hash'][:8]}... hash={entry['entry_hash'][:8]}...")

    # ─── Persistence + reload test ───
    # Flush pending actions before testing persistence
    team.flush()
    print("\n--- Persistence Test ---")
    loaded = HardboundTeam.load("acme-ai-ops")
    loaded_info = loaded.info()
    print(f"  Members restored: {len(loaded_info['members'])}")
    print(f"  Ledger entries: {loaded_info['ledger']['entries']}")
    print(f"  Birth certs restored: {loaded_info['birth_certificates']}")
    for m in loaded_info['members']:
        print(f"    {m['name']:25s} role={m['role']:10s}")

    # Verify birth certificates survived reload
    certs_valid = all(
        cert.verify() for cert in loaded.birth_certificates.values()
    )
    print(f"  Birth cert integrity: {'ALL VALID' if certs_valid else 'SOME TAMPERED'}")

    # Sign on loaded team (use non-multi-sig action to test basic reload)
    record = loaded.sign_action(f"{loaded.name}-admin", "set_resource_limit")
    print(f"\n  Sign after reload: set_resource_limit → {record['decision']}")

    # Flush and re-verify after new action
    loaded.flush()
    reload_verify = loaded.ledger.verify()
    print(f"  Ledger still valid: {reload_verify['valid']}")
    print(f"  Total entries: {reload_verify['entries']}")

    # ─── State files ───
    print("\n--- Persisted State Files ---")
    state_dir = team.state_dir
    for f in sorted(state_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(state_dir)
            print(f"  {str(rel):30s} ({f.stat().st_size:,} bytes)")

    # ─── Ledger Analytics ───
    print("\n--- Ledger Analytics ---")
    analytics = team.ledger.analytics()
    acts = analytics["actions"]
    print(f"  Total entries: {analytics['total_entries']}")
    print(f"  Actions: {acts['total']} ({acts['approved']} approved, {acts['denied']} denied)")
    print(f"  Approval rate: {acts['approval_rate']}%")
    print(f"  HW-signed: {analytics['hw_signed_pct']}%")
    print(f"  Policy versions: {analytics['policy_versions']}")

    # Per-actor breakdown
    print("\n  Per-actor:")
    for actor, stats in analytics.get("by_actor", {}).items():
        print(f"    {actor:25s} acts={stats['actions']:2d}  ok={stats['approved']:2d}  "
              f"denied={stats['denied']:2d}  ATP={stats['atp_spent']:.1f}")

    # Query example: denied actions
    denied = team.ledger.query(decision="denied", limit=3)
    print(f"\n  Recent denied actions ({len(denied)}):")
    for entry in denied:
        action = entry.get("action", {})
        print(f"    #{entry['sequence']} {action.get('actor', '?')} → "
              f"{action.get('action', '?')}: {action.get('reason', '?')[:50]}")

    # ─── Heartbeat + Metabolic State ───
    print("\n--- Heartbeat-Driven Ledger ---")
    hb = team.heartbeat
    print(f"  Metabolic state: {hb.state}")
    print(f"  Heartbeat interval: {hb.interval}s")
    print(f"  Team ATP: {team.team_atp:.1f}/{team.team_atp_max:.1f} "
          f"(ratio={team.team_atp / team.team_atp_max:.2f})")

    # Show member ATP for comparison
    for name, member in team.members.items():
        m_atp = member.atp.atp_balance if hasattr(member, 'atp') else 0
        print(f"    {name:25s} ATP: {m_atp:.1f}")

    # ─── Reputation Evolution ───
    print("\n--- Reputation Evolution (T3/V3 Deltas) ---")
    print("  Trust evolves from every action:")
    for name, member in team.members.items():
        t3 = member.t3
        v3 = member.v3
        c = member.coherence
        print(f"    {name:25s} T3=[{t3.talent:.3f},{t3.training:.3f},{t3.temperament:.3f}] "
              f"V3=[{v3.valuation:.3f},{v3.veracity:.3f},{v3.validity:.3f}] C={c:.3f}")

    # Show recent deltas from action records
    recent_with_deltas = [
        r for r in team.action_log[-10:]
        if "reputation_delta" in r
    ]
    # If action_log was flushed, check the ledger
    if not recent_with_deltas:
        for entry in team.ledger.tail(10):
            action = entry.get("action", {})
            if "reputation_delta" in action:
                recent_with_deltas.append(action)

    if recent_with_deltas:
        print(f"\n  Recent reputation deltas ({len(recent_with_deltas)}):")
        for r in recent_with_deltas[-5:]:
            delta = r.get("reputation_delta", {})
            t3d = delta.get("t3_delta", {})
            actor = r.get("actor", "?")
            action_name = r.get("action", "?")
            cd = delta.get("coherence_delta", 0)
            sign = "+" if cd >= 0 else ""
            print(f"    {actor:20s} → {action_name:20s} "
                  f"C{sign}{cd:.4f} "
                  f"(talent{'+' if t3d.get('talent', 0) >= 0 else ''}{t3d.get('talent', 0):.4f})")

    # ─── Multi-Sig Approval ───
    print("\n--- Multi-Sig Approval (M-of-N) ---")

    # Use the loaded team to avoid stale chain head from persistence test
    team = loaded
    admin = f"{team.name}-admin"

    policy = team._resolve_policy()
    print(f"  Multi-sig actions defined: {len(policy.multi_sig)}")
    for action, req in policy.multi_sig.items():
        print(f"    {action}: {req['required']}-of-{req['eligible_roles']}")

    # Admin tries emergency_shutdown — requires 2-of-[admin,operator]
    record = team.sign_action(admin, "emergency_shutdown")
    print(f"\n  Admin → emergency_shutdown: {record.get('decision', 'unknown')}")
    if "multi_sig" in record:
        msig = record["multi_sig"]
        print(f"    Request ID: {msig.get('request_id', 'n/a')}")
        print(f"    Approvals: {msig['approvals']}/{msig['required']}")
        print(f"    Remaining: {msig['remaining']}")
        request_id = msig.get("request_id")

        # Second approver (operator) completes the quorum
        result = team.approve_multi_sig("qa-engineer", action="emergency_shutdown")
        if result.get("decision") == "approved" or result.get("multi_sig_quorum_met"):
            print(f"\n  Operator (qa-engineer) approves → quorum met!")
            print(f"    Decision: {result.get('decision', 'unknown')}")
            print(f"    ATP cost: {result.get('atp_cost', 'n/a')}")
            print(f"    Approvers: {result.get('multi_sig_approvals', [])}")
        elif result.get("status") == "pending":
            print(f"\n  Operator approves → still pending ({result['approvals']}/{result['required']})")
        else:
            print(f"\n  Approval result: {result}")
    else:
        print(f"    (executed without multi-sig — check policy)")

    # Also try rotate_credentials (requires 2 admins)
    print(f"\n  Admin → rotate_credentials (needs 2 admins):")
    record = team.sign_action(admin, "rotate_credentials")
    if record.get("decision") == "pending_multi_sig":
        print(f"    Status: pending (only 1 admin available)")
        print(f"    Would need a second admin to approve")
    else:
        print(f"    Decision: {record.get('decision', 'unknown')}")

    # ─── Summary ───
    # Flush any remaining buffered actions
    team.flush()
    print("\n--- Summary ---")
    hw_members = sum(1 for m in team.members.values()
                    if isinstance(m, HardwareWeb4Entity))
    sw_members = len(team.members) - hw_members
    policy = team._resolve_policy()
    print(f"  Team: {team.name}")
    print(f"  Members: {len(team.members)} ({hw_members} HW, {sw_members} SW)")
    print(f"  Roles: admin={sum(1 for r in team.roles.values() if r == TeamRole.ADMIN)}, "
          f"operator={sum(1 for r in team.roles.values() if r == TeamRole.OPERATOR)}, "
          f"agent={sum(1 for r in team.roles.values() if r == TeamRole.AGENT)}")
    print(f"  Ledger: {team.ledger.count()} entries (hash-chained)")
    final_verify = team.ledger.verify()
    print(f"  Chain integrity: {'VERIFIED' if final_verify['valid'] else 'BROKEN'}")
    print(f"  Policy: v{policy.version} ({len(policy.admin_only)} admin-only, "
          f"{len(policy.operator_min)} operator-min)")
    print(f"  Team ATP: {team.team_atp:.1f}/{team.team_atp_max:.1f} "
          f"({team.team_adp_discharged:.1f} discharged)")
    print(f"  Birth certificates: {len(team.birth_certificates)}")

    print("\n" + "=" * 65)
    print("  Hardbound: Real enterprise AI governance.")
    print("  Hash-chained ledger. Role-based authorization.")
    print("  Policy-from-ledger. SAL birth certificates.")
    print("  State survives sessions. The chain remembers.")
    print("=" * 65)


def main():
    """Parse CLI arguments and dispatch commands."""
    parser = argparse.ArgumentParser(
        description="Hardbound CLI — Enterprise Team Management with Hardware-Backed Identity",
        prog="hardbound"
    )
    parser.add_argument("--no-tpm", action="store_true", help="Force simulation mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # team create
    team_create = subparsers.add_parser("team-create", help="Create a new team")
    team_create.add_argument("name", help="Team name")

    # team info
    team_info = subparsers.add_parser("team-info", help="Show team info")
    team_info.add_argument("name", help="Team name")

    # team list
    subparsers.add_parser("team-list", help="List all teams")

    # team add-member
    team_add = subparsers.add_parser("team-add-member", help="Add member to team")
    team_add.add_argument("team", help="Team name")
    team_add.add_argument("name", help="Member name")
    team_add.add_argument("type", help="Member type (ai, human, service, etc.)")

    # team sign
    team_sign = subparsers.add_parser("team-sign", help="Sign action in team context")
    team_sign.add_argument("team", help="Team name")
    team_sign.add_argument("actor", help="Actor name")
    team_sign.add_argument("action", help="Action to sign")

    # team actions
    team_actions = subparsers.add_parser("team-actions", help="Show team action log")
    team_actions.add_argument("team", help="Team name")
    team_actions.add_argument("--limit", type=int, default=20, help="Max actions to show")

    # team verify
    team_verify = subparsers.add_parser("team-verify", help="Verify team ledger chain")
    team_verify.add_argument("team", help="Team name")

    # team analytics
    team_analytics = subparsers.add_parser("team-analytics", help="Show team ledger analytics")
    team_analytics.add_argument("team", help="Team name")

    # team approve
    team_approve = subparsers.add_parser("team-approve", help="Approve a pending multi-sig request")
    team_approve.add_argument("team", help="Team name")
    team_approve.add_argument("approver", help="Name of the approver")
    team_approve.add_argument("--request-id", help="Multi-sig request ID")
    team_approve.add_argument("--action", help="Action name to find pending request")

    # team recharge
    team_recharge = subparsers.add_parser("team-recharge", help="Manually trigger ATP recharge")
    team_recharge.add_argument("team", help="Team name")

    # team query
    team_query = subparsers.add_parser("team-query", help="Query team ledger entries")
    team_query.add_argument("team", help="Team name")
    team_query.add_argument("--actor", help="Filter by actor name")
    team_query.add_argument("--type", help="Filter by action type")
    team_query.add_argument("--decision", help="Filter by decision (approved/denied)")
    team_query.add_argument("--hw-only", action="store_true", help="Only hardware-signed entries")
    team_query.add_argument("--limit", type=int, default=20, help="Max entries to show")

    # team birth-cert
    team_birth_cert = subparsers.add_parser("team-birth-cert", help="Show a member's SAL birth certificate")
    team_birth_cert.add_argument("team", help="Team name")
    team_birth_cert.add_argument("member", help="Member name")

    # demo
    subparsers.add_parser("demo", help="Run interactive demo")

    # entity create
    entity_create = subparsers.add_parser("entity-create", help="Create an entity")
    entity_create.add_argument("name", help="Entity name")
    entity_create.add_argument("type", help="Entity type (ai, human, service, etc.)")

    # entity sign
    entity_sign = subparsers.add_parser("entity-sign", help="Sign an R6 action")
    entity_sign.add_argument("name", help="Entity name")
    entity_sign.add_argument("action", help="Action to sign")
    entity_sign.add_argument("--type", default="ai", help="Entity type")

    # avp prove
    avp_prove = subparsers.add_parser("avp-prove", help="Run AVP aliveness proof")
    avp_prove.add_argument("name", help="Entity name")
    avp_prove.add_argument("--type", default="ai", help="Entity type")

    # avp attest
    avp_attest = subparsers.add_parser("avp-attest", help="Get TPM2 attestation")
    avp_attest.add_argument("--name", default=None, help="Entity name")
    avp_attest.add_argument("--type", default="ai", help="Entity type")

    # ek info
    subparsers.add_parser("ek-info", help="Show EK certificate info")

    # ek verify
    subparsers.add_parser("ek-verify", help="Verify EK certificate chain")

    # status
    subparsers.add_parser("status", help="Show system status")

    args = parser.parse_args()

    dispatch = {
        "team-create": cmd_team_create,
        "team-info": cmd_team_info,
        "team-list": cmd_team_list,
        "team-add-member": cmd_team_add_member,
        "team-sign": cmd_team_sign,
        "team-actions": cmd_team_actions,
        "team-verify": cmd_team_verify,
        "team-analytics": cmd_team_analytics,
        "team-approve": cmd_team_approve,
        "team-recharge": cmd_team_recharge,
        "team-query": cmd_team_query,
        "team-birth-cert": cmd_team_birth_cert,
        "demo": lambda a: demo(),
        "entity-create": cmd_entity_create,
        "entity-sign": cmd_entity_sign,
        "avp-prove": cmd_avp_prove,
        "avp-attest": cmd_avp_attest,
        "ek-info": cmd_ek_info,
        "ek-verify": cmd_ek_verify,
        "status": cmd_status,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        demo()


if __name__ == "__main__":
    main()
