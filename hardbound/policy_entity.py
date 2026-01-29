# SPDX-License-Identifier: PROPRIETARY
# Copyright (c) 2025 Hardbound Contributors
#
# Hardbound - Policy Entity for Enterprise Governance
# https://github.com/dp-web4/hardbound
#
# DERIVATION NOTICE:
# This module is derived from the open-source Web4 Lightweight Governance
# PolicyEntity (https://github.com/dp-web4/web4/claude-code-plugin/governance/policy_entity.py)
# Adapted for enterprise use with:
# - Team-scoped policies
# - Integration with Hardbound Ledger
# - Member role-based enforcement
# - Enterprise audit requirements
"""
Policy Entity - Policy as a first-class participant in the enterprise trust network.

Policy isn't just configuration - it's organizational law. It has identity,
can be witnessed by teams and members, and is hash-tracked in the audit chain.

Key concepts:
- Policy is immutable once registered (changing = new entity)
- Teams witness operating under a policy
- Policy witnesses member actions (allow/deny)
- R6 records reference the policy_hash in effect
- Team admins can register and modify which policy is active

Usage:
    from policy_entity import PolicyEntity, PolicyRegistry

    # Register a policy (creates hash-identified entity)
    registry = PolicyRegistry(ledger)
    entity = registry.register_policy("enterprise-safety", config)

    # Evaluate a member action
    decision = entity.evaluate(action_type, role, member_trust)

    # Team witnesses adoption of policy
    registry.witness_team(entity.entity_id, team_id)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, TYPE_CHECKING
import re
import fnmatch

if TYPE_CHECKING:
    from .ledger import Ledger


# ============================================================================
# Policy Types (self-contained, derived from Web4 presets.py)
# ============================================================================

PolicyDecision = Literal["allow", "deny", "warn"]


@dataclass
class RateLimit:
    """Rate limiting configuration for a rule."""
    max_count: int
    window_ms: int


@dataclass
class PolicyMatch:
    """Criteria for when a policy rule applies."""
    # Action/tool matching
    tools: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    action_types: Optional[List[str]] = None  # Enterprise: action_type matching

    # Target matching
    target_patterns: Optional[List[str]] = None
    target_patterns_are_regex: bool = False

    # Trust-based matching (enterprise)
    min_trust: Optional[float] = None  # Minimum trust threshold
    max_trust: Optional[float] = None  # Maximum trust threshold

    # Role-based matching (enterprise)
    roles: Optional[List[str]] = None  # Only these roles can trigger

    # Rate limiting
    rate_limit: Optional[RateLimit] = None


@dataclass
class PolicyRule:
    """A single rule in the policy."""
    id: str
    name: str
    priority: int  # Lower = evaluated first
    decision: PolicyDecision
    match: PolicyMatch
    reason: Optional[str] = None

    # Enterprise extensions
    requires_approval: bool = False  # Requires admin/peer approval
    atp_cost: int = 1  # ATP cost when rule fires


@dataclass
class PolicyConfig:
    """Complete policy configuration."""
    default_policy: PolicyDecision
    enforce: bool  # False = dry-run mode (log but don't block)
    rules: List[PolicyRule]
    preset: Optional[str] = None  # Source preset name if any

    # Enterprise extensions
    team_scope: Optional[str] = None  # Restrict to specific team
    admin_override: bool = True  # Admins can bypass denials


# ============================================================================
# Policy Evaluation
# ============================================================================

@dataclass
class PolicyEvaluation:
    """Result of evaluating an action against policy."""
    decision: PolicyDecision
    rule_id: Optional[str]
    rule_name: Optional[str]
    reason: str
    enforced: bool
    constraints: List[str]

    # Enterprise extensions
    requires_approval: bool = False
    atp_cost: int = 0


# ============================================================================
# Enterprise Presets
# ============================================================================

def get_enterprise_preset(name: str) -> PolicyConfig:
    """
    Get an enterprise policy preset.

    Enterprise presets differ from open-source presets:
    - Include role-based access controls
    - ATP cost management
    - Approval workflows
    - Trust threshold requirements
    """
    presets = {
        "permissive": PolicyConfig(
            default_policy="allow",
            enforce=False,
            rules=[],
            preset="permissive",
        ),

        "audit-only": PolicyConfig(
            default_policy="allow",
            enforce=False,
            rules=[
                PolicyRule(
                    id="audit-all",
                    name="Audit all actions",
                    priority=100,
                    decision="allow",
                    match=PolicyMatch(),
                    reason="Audit trail only, no enforcement",
                ),
            ],
            preset="audit-only",
        ),

        "enterprise-safety": PolicyConfig(
            default_policy="allow",
            enforce=True,
            rules=[
                # High-risk actions require elevated trust
                PolicyRule(
                    id="high-risk-trust",
                    name="High-risk actions need elevated trust",
                    priority=10,
                    decision="deny",
                    match=PolicyMatch(
                        action_types=["admin_action", "financial", "delete"],
                        max_trust=0.7,  # Deny if trust below 0.7
                    ),
                    reason="Insufficient trust for high-risk action",
                    atp_cost=5,
                ),
                # Destructive actions need approval
                PolicyRule(
                    id="destructive-approval",
                    name="Destructive actions need approval",
                    priority=20,
                    decision="warn",
                    match=PolicyMatch(
                        action_types=["delete", "revoke", "terminate"],
                    ),
                    reason="Destructive action flagged for review",
                    requires_approval=True,
                    atp_cost=3,
                ),
                # Rate limit external API calls
                PolicyRule(
                    id="external-rate-limit",
                    name="Rate limit external calls",
                    priority=30,
                    decision="deny",
                    match=PolicyMatch(
                        categories=["network", "external_api"],
                        rate_limit=RateLimit(max_count=100, window_ms=60000),
                    ),
                    reason="External API rate limit exceeded",
                    atp_cost=1,
                ),
                # Warn on sensitive data access
                PolicyRule(
                    id="sensitive-data-warn",
                    name="Warn on sensitive data",
                    priority=40,
                    decision="warn",
                    match=PolicyMatch(
                        target_patterns=["*credentials*", "*secrets*", "*.env", "*password*"],
                    ),
                    reason="Accessing potentially sensitive data",
                    atp_cost=2,
                ),
            ],
            preset="enterprise-safety",
            admin_override=True,
        ),

        "strict": PolicyConfig(
            default_policy="deny",
            enforce=True,
            rules=[
                # Only allow read-only operations by default
                PolicyRule(
                    id="allow-read",
                    name="Allow read operations",
                    priority=10,
                    decision="allow",
                    match=PolicyMatch(
                        categories=["read", "query", "view"],
                    ),
                    reason="Read operations allowed",
                    atp_cost=0,
                ),
                # Allow approved roles to write
                PolicyRule(
                    id="allow-write-roles",
                    name="Allow write for authorized roles",
                    priority=20,
                    decision="allow",
                    match=PolicyMatch(
                        categories=["write", "create", "update"],
                        roles=["admin", "developer", "operator"],
                        min_trust=0.5,
                    ),
                    reason="Authorized role with sufficient trust",
                    atp_cost=1,
                ),
            ],
            preset="strict",
            admin_override=True,
        ),
    }

    if name not in presets:
        raise ValueError(f"Unknown preset: {name}. Available: {list(presets.keys())}")

    return presets[name]


# ============================================================================
# Policy Entity
# ============================================================================

@dataclass
class PolicyEntity:
    """
    A policy as a first-class entity in the enterprise trust network.

    Properties:
    - entity_id: Unique identifier (policy:<name>:<version>:<hash>)
    - content_hash: SHA-256 of the policy document (first 16 chars)
    - config: The actual policy configuration
    - created_at: When this version was created
    """
    name: str
    version: str
    config: PolicyConfig
    content_hash: str
    entity_id: str
    created_at: str
    source: str = "preset"  # "preset", "custom", "file"

    # Sorted rules for evaluation (lower priority = evaluated first)
    _sorted_rules: List[PolicyRule] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Sort rules by priority after initialization."""
        self._sorted_rules = sorted(self.config.rules, key=lambda r: r.priority)

    def evaluate(
        self,
        tool_name: str,
        category: str,
        target: Optional[str] = None,
        role: Optional[str] = None,
        trust_score: Optional[float] = None,
        rate_limiter: Optional[Any] = None,
        is_admin: bool = False,
    ) -> PolicyEvaluation:
        """
        Evaluate an action against this policy.

        Args:
            tool_name: Name of the tool/action
            category: Action category
            target: Target of the operation
            role: Member's role (enterprise)
            trust_score: Member's trust score (enterprise)
            rate_limiter: Optional RateLimiter for rate-based rules
            is_admin: Whether the member is an admin (enterprise)

        Returns:
            PolicyEvaluation with decision and context
        """
        for rule in self._sorted_rules:
            if self._matches_rule(tool_name, category, target, role, trust_score, rule.match):
                # Check rate limit if specified
                if rule.match.rate_limit and rate_limiter:
                    key = self._rate_limit_key(rule, tool_name, category)
                    result = rate_limiter.check(
                        key,
                        rule.match.rate_limit.max_count,
                        rule.match.rate_limit.window_ms,
                    )
                    if result.allowed:
                        continue  # Under limit, rule doesn't fire

                # Admin override (enterprise)
                if rule.decision == "deny" and is_admin and self.config.admin_override:
                    return PolicyEvaluation(
                        decision="allow",
                        rule_id=rule.id,
                        rule_name=rule.name,
                        reason=f"Admin override: {rule.reason}",
                        enforced=True,
                        constraints=[
                            f"policy:{self.entity_id}",
                            "decision:allow",
                            f"rule:{rule.id}",
                            "override:admin",
                        ],
                        requires_approval=False,
                        atp_cost=rule.atp_cost,
                    )

                enforced = rule.decision != "deny" or self.config.enforce
                return PolicyEvaluation(
                    decision=rule.decision,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    reason=rule.reason or f"Matched rule: {rule.name}",
                    enforced=enforced,
                    constraints=[
                        f"policy:{self.entity_id}",
                        f"decision:{rule.decision}",
                        f"rule:{rule.id}",
                    ],
                    requires_approval=rule.requires_approval,
                    atp_cost=rule.atp_cost,
                )

        # No rule matched - default policy
        return PolicyEvaluation(
            decision=self.config.default_policy,
            rule_id=None,
            rule_name=None,
            reason=f"Default policy: {self.config.default_policy}",
            enforced=True,
            constraints=[
                f"policy:{self.entity_id}",
                f"decision:{self.config.default_policy}",
                "rule:default",
            ],
            requires_approval=False,
            atp_cost=1,
        )

    def _matches_rule(
        self,
        tool_name: str,
        category: str,
        target: Optional[str],
        role: Optional[str],
        trust_score: Optional[float],
        match: PolicyMatch,
    ) -> bool:
        """Check if an action matches a rule's criteria (AND logic)."""
        # Tool match
        if match.tools and tool_name not in match.tools:
            return False

        # Category match
        if match.categories and category not in match.categories:
            return False

        # Action type match (enterprise)
        if match.action_types and category not in match.action_types:
            return False

        # Role match (enterprise)
        if match.roles and role not in match.roles:
            return False

        # Trust threshold match (enterprise)
        if match.min_trust is not None and trust_score is not None:
            if trust_score < match.min_trust:
                return False
        if match.max_trust is not None and trust_score is not None:
            if trust_score > match.max_trust:
                # This is for "deny if trust below X" - inverted logic
                return False

        # Target pattern match
        if match.target_patterns:
            if target is None:
                return False
            matched = False
            for pattern in match.target_patterns:
                if match.target_patterns_are_regex:
                    if re.search(pattern, target):
                        matched = True
                        break
                else:
                    # Glob pattern
                    if fnmatch.fnmatch(target, pattern):
                        matched = True
                        break
            if not matched:
                return False

        return True

    def _rate_limit_key(self, rule: PolicyRule, tool_name: str, category: str) -> str:
        """Build rate limit key from rule context."""
        if rule.match.tools:
            return f"ratelimit:{rule.id}:tool:{tool_name}"
        if rule.match.categories:
            return f"ratelimit:{rule.id}:category:{category}"
        return f"ratelimit:{rule.id}:global"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "version": self.version,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "source": self.source,
            "config": _policy_config_to_dict(self.config),
        }


# ============================================================================
# Policy Registry
# ============================================================================

class PolicyRegistry:
    """
    Registry of policy entities with hash-tracking and witnessing.

    Enterprise features:
    - Persistent storage in Hardbound Ledger
    - Team-scoped policies
    - Member witnessing
    """

    def __init__(self, ledger: Optional["Ledger"] = None, storage_path: Optional[Path] = None):
        """
        Initialize registry.

        Args:
            ledger: Hardbound Ledger for persistence (preferred)
            storage_path: Fallback file-based storage path
        """
        self._ledger = ledger

        if storage_path is None:
            storage_path = Path.home() / ".hardbound"
        self.storage_path = Path(storage_path)
        self.policies_path = self.storage_path / "policies"
        self.policies_path.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._cache: Dict[str, PolicyEntity] = {}

        # Witnessing records (in-memory, persisted to ledger)
        self._witnessed_by: Dict[str, set] = {}  # entity -> set of witnesses
        self._has_witnessed: Dict[str, set] = {}  # entity -> set of entities witnessed

    def register_policy(
        self,
        name: str,
        config: Optional[PolicyConfig] = None,
        preset: Optional[str] = None,
        version: Optional[str] = None,
    ) -> PolicyEntity:
        """
        Register a policy and create its entity.

        Args:
            name: Policy name
            config: PolicyConfig (mutually exclusive with preset)
            preset: Enterprise preset name (mutually exclusive with config)
            version: Version string (auto-generated if not provided)

        Returns:
            PolicyEntity with hash-identified entity_id
        """
        if config is None and preset is None:
            raise ValueError("Must provide either config or preset")
        if config is not None and preset is not None:
            raise ValueError("Cannot provide both config and preset")

        # Resolve config
        if preset:
            config = get_enterprise_preset(preset)
            source = "preset"
        else:
            source = "custom"

        # Generate version if not provided
        if version is None:
            version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        # Compute content hash
        config_dict = _policy_config_to_dict(config)
        content_str = json.dumps(config_dict, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        # Build entity ID
        entity_id = f"policy:{name}:{version}:{content_hash}"

        # Check cache
        if entity_id in self._cache:
            return self._cache[entity_id]

        # Create entity
        now = datetime.now(timezone.utc).isoformat() + "Z"
        entity = PolicyEntity(
            name=name,
            version=version,
            config=config,
            content_hash=content_hash,
            entity_id=entity_id,
            created_at=now,
            source=source,
        )

        # Persist to ledger if available
        if self._ledger:
            self._ledger.save_policy_entity(
                entity_id=entity_id,
                name=name,
                version=version,
                content_hash=content_hash,
                source=source,
                config=config_dict,
            )
        else:
            # Fallback: persist to file
            policy_file = self.policies_path / f"{content_hash}.json"
            if not policy_file.exists():
                policy_file.write_text(json.dumps(entity.to_dict(), indent=2))

        # Cache
        self._cache[entity_id] = entity

        return entity

    def get_policy(self, entity_id: str) -> Optional[PolicyEntity]:
        """Get a policy by entity ID."""
        if entity_id in self._cache:
            return self._cache[entity_id]

        # Try ledger first
        if self._ledger:
            data = self._ledger.get_policy_entity(entity_id)
            if data:
                entity = self._entity_from_dict(data)
                self._cache[entity_id] = entity
                return entity

        # Try file fallback
        parts = entity_id.split(":")
        if len(parts) >= 4:
            content_hash = parts[3]
            policy_file = self.policies_path / f"{content_hash}.json"
            if policy_file.exists():
                data = json.loads(policy_file.read_text())
                entity = self._entity_from_dict(data)
                self._cache[entity_id] = entity
                return entity

        return None

    def _entity_from_dict(self, data: Dict[str, Any]) -> PolicyEntity:
        """Reconstruct PolicyEntity from dict."""
        config_data = data["config"]
        rules = []
        for r in config_data.get("rules", []):
            match_data = r.get("match", {})
            rate_limit = None
            if match_data.get("rate_limit"):
                rl = match_data["rate_limit"]
                rate_limit = RateLimit(max_count=rl["max_count"], window_ms=rl["window_ms"])

            rules.append(PolicyRule(
                id=r["id"],
                name=r["name"],
                priority=r["priority"],
                decision=r["decision"],
                reason=r.get("reason"),
                requires_approval=r.get("requires_approval", False),
                atp_cost=r.get("atp_cost", 1),
                match=PolicyMatch(
                    tools=match_data.get("tools"),
                    categories=match_data.get("categories"),
                    action_types=match_data.get("action_types"),
                    target_patterns=match_data.get("target_patterns"),
                    target_patterns_are_regex=match_data.get("target_patterns_are_regex", False),
                    min_trust=match_data.get("min_trust"),
                    max_trust=match_data.get("max_trust"),
                    roles=match_data.get("roles"),
                    rate_limit=rate_limit,
                ),
            ))

        config = PolicyConfig(
            default_policy=config_data["default_policy"],
            enforce=config_data["enforce"],
            rules=rules,
            preset=config_data.get("preset"),
            team_scope=config_data.get("team_scope"),
            admin_override=config_data.get("admin_override", True),
        )

        return PolicyEntity(
            name=data["name"],
            version=data["version"],
            config=config,
            content_hash=data["content_hash"],
            entity_id=data["entity_id"],
            created_at=data["created_at"],
            source=data.get("source", "custom"),
        )

    def witness_team(self, policy_entity_id: str, team_id: str) -> None:
        """
        Record that a team is operating under this policy.

        Creates bidirectional witnessing:
        - Team witnesses the policy (we operate under these rules)
        - Policy witnesses the team (this team uses me)
        """
        team_entity = f"team:{team_id}"

        if policy_entity_id not in self._witnessed_by:
            self._witnessed_by[policy_entity_id] = set()
        self._witnessed_by[policy_entity_id].add(team_entity)

        if team_entity not in self._has_witnessed:
            self._has_witnessed[team_entity] = set()
        self._has_witnessed[team_entity].add(policy_entity_id)

        # Persist to ledger
        if self._ledger:
            self._ledger.record_policy_witness(policy_entity_id, team_entity, "team_adoption")

    def witness_member(self, policy_entity_id: str, member_id: str) -> None:
        """Record that a member has been evaluated against this policy."""
        member_entity = f"member:{member_id}"

        if policy_entity_id not in self._has_witnessed:
            self._has_witnessed[policy_entity_id] = set()
        self._has_witnessed[policy_entity_id].add(member_entity)

        # Persist to ledger
        if self._ledger:
            self._ledger.record_policy_witness(policy_entity_id, member_entity, "member_evaluation")

    def witness_decision(
        self,
        policy_entity_id: str,
        member_id: str,
        action_type: str,
        decision: PolicyDecision,
        success: bool,
    ) -> None:
        """
        Record a policy decision in the witnessing chain.

        The policy witnesses the member's action attempt.
        """
        member_entity = f"member:{member_id}"

        if policy_entity_id not in self._has_witnessed:
            self._has_witnessed[policy_entity_id] = set()
        self._has_witnessed[policy_entity_id].add(member_entity)

        # Persist to ledger
        if self._ledger:
            witness_type = f"decision:{decision}:{'success' if success else 'failure'}"
            self._ledger.record_policy_witness(policy_entity_id, member_entity, witness_type)

    def get_witnessed_by(self, entity_id: str) -> List[str]:
        """Get entities that have witnessed a policy."""
        return list(self._witnessed_by.get(entity_id, set()))

    def get_has_witnessed(self, entity_id: str) -> List[str]:
        """Get entities that a policy has witnessed."""
        return list(self._has_witnessed.get(entity_id, set()))

    def list_policies(self) -> List[PolicyEntity]:
        """List all registered policies."""
        policies = []

        # Load from file storage
        for policy_file in self.policies_path.glob("*.json"):
            try:
                data = json.loads(policy_file.read_text())
                entity = self._entity_from_dict(data)
                if entity.entity_id not in self._cache:
                    self._cache[entity.entity_id] = entity
                policies.append(entity)
            except (json.JSONDecodeError, KeyError):
                pass

        return policies


# ============================================================================
# Utility Functions
# ============================================================================

def _policy_config_to_dict(config: PolicyConfig) -> Dict[str, Any]:
    """Convert PolicyConfig to JSON-serializable dict."""
    rules = []
    for r in config.rules:
        match_dict: Dict[str, Any] = {}
        if r.match.tools:
            match_dict["tools"] = r.match.tools
        if r.match.categories:
            match_dict["categories"] = r.match.categories
        if r.match.action_types:
            match_dict["action_types"] = r.match.action_types
        if r.match.target_patterns:
            match_dict["target_patterns"] = r.match.target_patterns
            match_dict["target_patterns_are_regex"] = r.match.target_patterns_are_regex
        if r.match.min_trust is not None:
            match_dict["min_trust"] = r.match.min_trust
        if r.match.max_trust is not None:
            match_dict["max_trust"] = r.match.max_trust
        if r.match.roles:
            match_dict["roles"] = r.match.roles
        if r.match.rate_limit:
            match_dict["rate_limit"] = {
                "max_count": r.match.rate_limit.max_count,
                "window_ms": r.match.rate_limit.window_ms,
            }

        rules.append({
            "id": r.id,
            "name": r.name,
            "priority": r.priority,
            "decision": r.decision,
            "reason": r.reason,
            "requires_approval": r.requires_approval,
            "atp_cost": r.atp_cost,
            "match": match_dict,
        })

    result: Dict[str, Any] = {
        "default_policy": config.default_policy,
        "enforce": config.enforce,
        "rules": rules,
    }
    if config.preset:
        result["preset"] = config.preset
    if config.team_scope:
        result["team_scope"] = config.team_scope
    if config.admin_override is not None:
        result["admin_override"] = config.admin_override

    return result


def compute_policy_hash(config: PolicyConfig) -> str:
    """Compute a policy content hash."""
    config_dict = _policy_config_to_dict(config)
    content_str = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()[:16]
