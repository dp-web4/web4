"""
Federation Binding: LCT Chain + Federation Integration

Track BP: Connects LCT binding chains with the federation system.

Key concepts:
1. Federations have LCTs that root their binding chains
2. Teams within federations are bound as children of the federation LCT
3. Cross-federation witnessing creates inter-federation trust links
4. Presence scores influence witness eligibility and trust

This enables:
- Verifiable federation identity through binding chains
- Cross-federation witnessing with presence requirements
- Trust that flows from strong binding roots
- Sybil resistance through binding chain validation
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .lct_binding_chain import (
    LCTBindingChain,
    LCTNode,
    WitnessRelationship,
    BindingType,
)
from .multi_federation import (
    MultiFederationRegistry,
    FederationProfile,
    InterFederationTrust,
    FederationRelationship,
)


@dataclass
class FederationBindingStatus:
    """Status of a federation's LCT binding chain."""
    federation_id: str
    root_lct: str
    chain_valid: bool
    chain_depth: int
    team_count: int
    presence_score: float
    witness_eligible: bool
    issues: List[str] = field(default_factory=list)


class FederationBindingRegistry:
    """
    Manages LCT binding chains for federations.

    Track BP: Every federation has an LCT root that binds its teams.

    A federation's binding chain:
    - Root: Federation LCT (highest trust, bound to federation identity)
    - Children: Team LCTs (derived trust from federation)
    - Cross-federation: Witnessing relationships create trust links
    """

    # Minimum presence score to be an eligible witness
    MIN_WITNESS_PRESENCE = 0.4

    # Minimum chain validity percentage for witness eligibility
    MIN_CHAIN_VALIDITY = 0.8

    def __init__(
        self,
        db_path: Optional[str] = None,
        federation_db_path: Optional[str] = None,
        federation_registry: MultiFederationRegistry = None,
    ):
        """
        Initialize the federation binding registry.

        Args:
            db_path: Path for LCT binding chain database
            federation_db_path: Path for federation registry database
            federation_registry: Existing federation registry (creates new if None)
        """
        self.binding_chain = LCTBindingChain(db_path=db_path)
        self.federation_registry = federation_registry or MultiFederationRegistry(
            db_path=federation_db_path
        )

        # Map federation IDs to their root LCTs
        self._federation_lcts: Dict[str, str] = {}

    def register_federation_with_binding(
        self,
        federation_id: str,
        name: str,
        initial_trust: float = 0.9,
        binding_type: BindingType = BindingType.SOFTWARE,
        **kwargs,
    ) -> Tuple[FederationProfile, LCTNode]:
        """
        Register a federation with its root LCT.

        Creates:
        1. Federation profile in the registry
        2. Root LCT node for the federation

        Args:
            federation_id: Unique federation identifier
            name: Human-readable name
            initial_trust: Initial trust level for the root LCT
            binding_type: How the federation is bound

        Returns:
            (FederationProfile, root LCTNode)
        """
        # Create federation profile
        profile = self.federation_registry.register_federation(
            federation_id=federation_id,
            name=name,
            **kwargs,
        )

        # Create root LCT for federation
        root_lct = f"lct:federation:{federation_id}"
        root_node = self.binding_chain.create_root_node(
            lct_id=root_lct,
            entity_type="federation",
            binding_type=binding_type,
            initial_trust=initial_trust,
            metadata={"federation_id": federation_id, "name": name},
        )

        # Track mapping
        self._federation_lcts[federation_id] = root_lct

        return profile, root_node

    def bind_team_to_federation(
        self,
        federation_id: str,
        team_id: str,
        team_name: str = "",
    ) -> LCTNode:
        """
        Bind a team as a child of the federation's LCT.

        Team's trust is derived from federation (slightly lower).
        Federation automatically witnesses the team.

        Args:
            federation_id: Parent federation
            team_id: Team identifier
            team_name: Optional team name

        Returns:
            Team's LCTNode
        """
        if federation_id not in self._federation_lcts:
            raise ValueError(f"Federation not registered: {federation_id}")

        parent_lct = self._federation_lcts[federation_id]
        team_lct = f"lct:team:{federation_id}:{team_id}"

        team_node = self.binding_chain.bind_child(
            parent_lct=parent_lct,
            child_lct=team_lct,
            entity_type="team",
            binding_type=BindingType.DERIVED,
            metadata={"team_id": team_id, "federation_id": federation_id, "name": team_name},
        )

        return team_node

    def get_federation_root(self, federation_id: str) -> Optional[LCTNode]:
        """Get the root LCT node for a federation."""
        if federation_id not in self._federation_lcts:
            return None
        return self.binding_chain.get_node(self._federation_lcts[federation_id])

    def get_federation_teams(self, federation_id: str) -> List[LCTNode]:
        """Get all team LCT nodes bound to a federation."""
        if federation_id not in self._federation_lcts:
            return []

        root_lct = self._federation_lcts[federation_id]
        descendants = self.binding_chain.get_descendants(root_lct)

        return [d for d in descendants if d.entity_type == "team"]

    def cross_federation_witness(
        self,
        witness_federation_id: str,
        subject_federation_id: str,
    ) -> Optional[WitnessRelationship]:
        """
        Create a witnessing relationship between federations.

        The witness federation's root LCT witnesses the subject federation's
        root LCT, creating an inter-federation trust link.

        Args:
            witness_federation_id: Federation doing the witnessing
            subject_federation_id: Federation being witnessed

        Returns:
            WitnessRelationship if successful, None if not eligible
        """
        if witness_federation_id not in self._federation_lcts:
            raise ValueError(f"Witness federation not registered: {witness_federation_id}")
        if subject_federation_id not in self._federation_lcts:
            raise ValueError(f"Subject federation not registered: {subject_federation_id}")

        witness_lct = self._federation_lcts[witness_federation_id]
        subject_lct = self._federation_lcts[subject_federation_id]

        # Check witness eligibility
        witness_status = self.get_federation_binding_status(witness_federation_id)
        if not witness_status.witness_eligible:
            return None

        # Create witness relationship
        try:
            relationship = self.binding_chain.witness(witness_lct, subject_lct)
            return relationship
        except ValueError:
            return None

    def get_federation_binding_status(
        self,
        federation_id: str,
    ) -> FederationBindingStatus:
        """
        Get the complete binding status for a federation.

        Includes:
        - Chain validation status
        - Presence score
        - Witness eligibility
        """
        if federation_id not in self._federation_lcts:
            return FederationBindingStatus(
                federation_id=federation_id,
                root_lct="",
                chain_valid=False,
                chain_depth=0,
                team_count=0,
                presence_score=0.0,
                witness_eligible=False,
                issues=["Federation not registered with binding chain"],
            )

        root_lct = self._federation_lcts[federation_id]
        root_node = self.binding_chain.get_node(root_lct)

        if not root_node:
            return FederationBindingStatus(
                federation_id=federation_id,
                root_lct=root_lct,
                chain_valid=False,
                chain_depth=0,
                team_count=0,
                presence_score=0.0,
                witness_eligible=False,
                issues=["Root LCT node not found"],
            )

        # Validate chain
        validation = self.binding_chain.validate_chain(root_lct)

        # Get presence proof
        presence = self.binding_chain.get_presence_proof(root_lct)

        # Count teams
        teams = self.get_federation_teams(federation_id)

        # Check witness eligibility
        issues = validation.get("issues", [])
        witness_eligible = (
            validation["valid"] and
            presence.get("presence_score", 0) >= self.MIN_WITNESS_PRESENCE
        )

        return FederationBindingStatus(
            federation_id=federation_id,
            root_lct=root_lct,
            chain_valid=validation["valid"],
            chain_depth=validation.get("chain_depth", 0),
            team_count=len(teams),
            presence_score=presence.get("presence_score", 0),
            witness_eligible=witness_eligible,
            issues=issues,
        )

    def get_eligible_federation_witnesses(
        self,
        requesting_federation_id: str,
        exclude: List[str] = None,
    ) -> List[Tuple[str, float]]:
        """
        Find federations eligible to witness for the requester.

        Eligibility requires:
        1. Valid binding chain
        2. Sufficient presence score
        3. Not the requesting federation
        4. Not in exclude list

        Returns:
            List of (federation_id, presence_score) tuples, sorted by presence
        """
        exclude = set(exclude or [])
        exclude.add(requesting_federation_id)

        eligible = []

        for fed_id in self._federation_lcts:
            if fed_id in exclude:
                continue

            status = self.get_federation_binding_status(fed_id)
            if status.witness_eligible:
                eligible.append((fed_id, status.presence_score))

        # Sort by presence score (highest first)
        eligible.sort(key=lambda x: x[1], reverse=True)

        return eligible

    def validate_cross_federation_witness(
        self,
        witness_federation_id: str,
        subject_federation_id: str,
    ) -> Dict:
        """
        Validate whether a cross-federation witness is valid.

        Checks:
        1. Both federations have valid binding chains
        2. Witness has sufficient presence
        3. Witnessing relationship exists
        """
        witness_status = self.get_federation_binding_status(witness_federation_id)
        subject_status = self.get_federation_binding_status(subject_federation_id)

        issues = []

        if not witness_status.chain_valid:
            issues.append(f"Witness chain invalid: {witness_status.issues}")

        if not witness_status.witness_eligible:
            issues.append(f"Witness not eligible: presence={witness_status.presence_score}")

        if not subject_status.chain_valid:
            issues.append(f"Subject chain invalid: {subject_status.issues}")

        # Check if witnessing relationship exists
        witness_lct = self._federation_lcts.get(witness_federation_id)
        subject_lct = self._federation_lcts.get(subject_federation_id)

        relationship_exists = False
        if witness_lct and subject_lct:
            # Check in binding chain's witness relationships
            conn = self.binding_chain._get_conn()
            try:
                row = conn.execute("""
                    SELECT * FROM witness_relationships
                    WHERE witness_lct = ? AND subject_lct = ?
                """, (witness_lct, subject_lct)).fetchone()
                relationship_exists = row is not None
            finally:
                if not self.binding_chain._in_memory:
                    conn.close()

        return {
            "valid": len(issues) == 0 and relationship_exists,
            "witness_federation": witness_federation_id,
            "subject_federation": subject_federation_id,
            "relationship_exists": relationship_exists,
            "witness_presence": witness_status.presence_score,
            "issues": issues,
        }

    def get_federation_trust_from_binding(
        self,
        federation_id: str,
    ) -> Dict:
        """
        Calculate federation trust based on its binding chain.

        Trust factors:
        - Root LCT trust level
        - Chain validity
        - Presence score
        - Number of witnesses
        """
        status = self.get_federation_binding_status(federation_id)
        root = self.get_federation_root(federation_id)

        if not root or not status.chain_valid:
            return {
                "federation_id": federation_id,
                "binding_trust": 0.0,
                "components": {},
                "valid": False,
            }

        presence = self.binding_chain.get_presence_proof(status.root_lct)

        # Calculate binding-based trust
        # Base: root trust level (max 0.4 contribution)
        base_trust = root.trust_level * 0.4

        # Presence: presence score (max 0.3 contribution)
        presence_trust = presence.get("presence_score", 0) * 0.3

        # Teams: more teams = more distributed (max 0.2 contribution)
        team_factor = min(1.0, status.team_count / 10)  # Cap at 10 teams
        team_trust = team_factor * 0.2

        # Validity: full marks if chain is valid (0.1 contribution)
        validity_trust = 0.1 if status.chain_valid else 0.0

        total_binding_trust = base_trust + presence_trust + team_trust + validity_trust

        return {
            "federation_id": federation_id,
            "binding_trust": total_binding_trust,
            "components": {
                "base_trust": base_trust,
                "presence_trust": presence_trust,
                "team_trust": team_trust,
                "validity_trust": validity_trust,
            },
            "root_trust": root.trust_level,
            "presence_score": presence.get("presence_score", 0),
            "team_count": status.team_count,
            "chain_valid": status.chain_valid,
            "valid": True,
        }

    # === Track BR: Presence Accumulation ===

    def build_internal_presence(
        self,
        federation_id: str,
    ) -> Dict:
        """
        Build presence through internal witnessing within the federation.

        Track BR: Internal activity contributes to presence score.

        Teams witness each other and the root, building presence.

        Returns:
            Dict with presence building results
        """
        if federation_id not in self._federation_lcts:
            return {"error": "Federation not registered", "witnesses_added": 0}

        root_lct = self._federation_lcts[federation_id]
        teams = self.get_federation_teams(federation_id)

        if len(teams) < 2:
            return {
                "error": "Need at least 2 teams for internal witnessing",
                "witnesses_added": 0,
            }

        witnesses_added = 0

        # Have each team witness the root
        for team in teams:
            try:
                self.binding_chain.witness(team.lct_id, root_lct)
                witnesses_added += 1
            except ValueError:
                pass  # May fail if trust too low

        # Have teams witness each other (sequential)
        for i, team in enumerate(teams):
            if i > 0:
                try:
                    self.binding_chain.witness(teams[i-1].lct_id, team.lct_id)
                    witnesses_added += 1
                except ValueError:
                    pass

        # Get updated status
        status = self.get_federation_binding_status(federation_id)

        return {
            "federation_id": federation_id,
            "witnesses_added": witnesses_added,
            "new_presence": status.presence_score,
            "witness_eligible": status.witness_eligible,
        }

    def get_presence_ranking(self) -> List[Dict]:
        """
        Get all federations ranked by presence score.

        Track BR: Presence determines influence and eligibility.

        Returns:
            List of federation info dicts, sorted by presence (highest first)
        """
        rankings = []

        for fed_id in self._federation_lcts:
            status = self.get_federation_binding_status(fed_id)
            trust_info = self.get_federation_trust_from_binding(fed_id)

            rankings.append({
                "federation_id": fed_id,
                "presence_score": status.presence_score,
                "binding_trust": trust_info.get("binding_trust", 0),
                "team_count": status.team_count,
                "chain_valid": status.chain_valid,
                "witness_eligible": status.witness_eligible,
            })

        rankings.sort(key=lambda x: x["presence_score"], reverse=True)
        return rankings

    def calculate_presence_weighted_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        base_trust: float,
    ) -> Dict:
        """
        Calculate trust weighted by target's presence score.

        Track BR: Higher presence = more trustworthy.

        The presence multiplier adjusts base trust:
        - Low presence (< 0.4): Trust reduced
        - Medium presence (0.4-0.6): Trust unchanged
        - High presence (> 0.6): Trust boosted

        Args:
            source_federation_id: Federation establishing trust
            target_federation_id: Federation being trusted
            base_trust: Initial trust level (before presence weighting)

        Returns:
            Dict with weighted trust and breakdown
        """
        target_status = self.get_federation_binding_status(target_federation_id)
        presence = target_status.presence_score

        # Calculate presence multiplier
        if presence < 0.4:
            # Low presence: reduce trust (0.8x at 0.3)
            multiplier = 0.5 + (presence * 1.25)  # 0.875 at 0.3, 1.0 at 0.4
        elif presence < 0.6:
            # Medium presence: neutral zone
            multiplier = 1.0
        else:
            # High presence: boost trust (up to 1.2x at 1.0)
            multiplier = 1.0 + (presence - 0.6) * 0.5  # 1.0 at 0.6, 1.2 at 1.0

        weighted_trust = min(1.0, base_trust * multiplier)

        return {
            "source_federation": source_federation_id,
            "target_federation": target_federation_id,
            "base_trust": base_trust,
            "target_presence": presence,
            "presence_multiplier": multiplier,
            "weighted_trust": weighted_trust,
            "trust_adjustment": weighted_trust - base_trust,
        }

    def get_presence_requirements(
        self,
        action_type: str,
    ) -> Dict:
        """
        Get presence requirements for different actions.

        Track BR: Presence gates certain capabilities.

        Args:
            action_type: Type of action (witness, propose, vote, etc.)

        Returns:
            Dict with presence thresholds
        """
        requirements = {
            "witness": {
                "min_presence": self.MIN_WITNESS_PRESENCE,
                "description": "Provide external witness for proposals",
            },
            "propose_cross_fed": {
                "min_presence": 0.35,
                "description": "Create cross-federation proposals",
            },
            "vote_critical": {
                "min_presence": 0.5,
                "description": "Vote on critical multi-federation actions",
            },
            "lead_federation": {
                "min_presence": 0.6,
                "description": "Lead or coordinate multi-federation efforts",
            },
        }

        if action_type in requirements:
            return requirements[action_type]
        else:
            return {
                "error": f"Unknown action type: {action_type}",
                "available_types": list(requirements.keys()),
            }

    def check_presence_permission(
        self,
        federation_id: str,
        action_type: str,
    ) -> Dict:
        """
        Check if a federation has sufficient presence for an action.

        Track BR: Presence as permission system.

        Args:
            federation_id: Federation to check
            action_type: Action requiring presence

        Returns:
            Dict with permission status and gap analysis
        """
        requirements = self.get_presence_requirements(action_type)

        if "error" in requirements:
            return requirements

        status = self.get_federation_binding_status(federation_id)
        min_required = requirements["min_presence"]

        has_permission = status.presence_score >= min_required
        gap = max(0, min_required - status.presence_score)

        return {
            "federation_id": federation_id,
            "action_type": action_type,
            "has_permission": has_permission,
            "current_presence": status.presence_score,
            "required_presence": min_required,
            "gap": gap,
            "description": requirements["description"],
            "suggestion": (
                None if has_permission
                else f"Need {gap:.2f} more presence. Add teams and build internal witnesses."
            ),
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Federation Binding Registry - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "federation_binding_test.db"
    fed_db_path = tmp_dir / "federation_registry_test.db"
    registry = FederationBindingRegistry(db_path=db_path, federation_db_path=fed_db_path)

    # Register federations with binding
    print("\n1. Register federations with LCT binding:")
    fed_a, lct_a = registry.register_federation_with_binding(
        "fed:alpha", "Alpha Federation", initial_trust=0.9
    )
    fed_b, lct_b = registry.register_federation_with_binding(
        "fed:beta", "Beta Federation", initial_trust=0.8
    )
    fed_c, lct_c = registry.register_federation_with_binding(
        "fed:gamma", "Gamma Federation", initial_trust=0.7
    )

    print(f"   Alpha root LCT: {lct_a.lct_id} (trust={lct_a.trust_level})")
    print(f"   Beta root LCT: {lct_b.lct_id} (trust={lct_b.trust_level})")
    print(f"   Gamma root LCT: {lct_c.lct_id} (trust={lct_c.trust_level})")

    # Bind teams
    print("\n2. Bind teams to federations:")
    for i in range(3):
        team = registry.bind_team_to_federation("fed:alpha", f"team:a:{i}")
        if i == 0:
            print(f"   Team A:0 bound: {team.lct_id} (trust={team.trust_level})")

    for i in range(2):
        team = registry.bind_team_to_federation("fed:beta", f"team:b:{i}")

    print(f"   Alpha teams: {len(registry.get_federation_teams('fed:alpha'))}")
    print(f"   Beta teams: {len(registry.get_federation_teams('fed:beta'))}")

    # Build presence through internal witnessing
    print("\n3. Build presence through team witnessing:")
    # Have teams witness each other within Alpha
    alpha_teams = registry.get_federation_teams("fed:alpha")
    for i, team in enumerate(alpha_teams):
        if i > 0:
            # Previous team witnesses this team
            registry.binding_chain.witness(alpha_teams[i-1].lct_id, team.lct_id)
            # This team witnesses root
            registry.binding_chain.witness(team.lct_id, registry._federation_lcts["fed:alpha"])

    # Check new presence
    alpha_status = registry.get_federation_binding_status("fed:alpha")
    print(f"   Alpha presence after team witnessing: {alpha_status.presence_score:.2f}")
    print(f"   Alpha witness eligible: {alpha_status.witness_eligible}")

    # Cross-federation witnessing
    print("\n4. Cross-federation witnessing:")
    rel = registry.cross_federation_witness("fed:alpha", "fed:beta")
    if rel:
        print(f"   Alpha witnessed Beta: {rel.witness_lct} -> {rel.subject_lct}")
    else:
        print("   Alpha could not witness Beta (not eligible)")

    # Get binding status
    print("\n5. Federation binding status:")
    for fed_id in ["fed:alpha", "fed:beta", "fed:gamma"]:
        status = registry.get_federation_binding_status(fed_id)
        print(f"   {fed_id}:")
        print(f"     Chain valid: {status.chain_valid}")
        print(f"     Teams: {status.team_count}")
        print(f"     Presence: {status.presence_score:.2f}")
        print(f"     Witness eligible: {status.witness_eligible}")

    # Get trust from binding
    print("\n6. Binding-based trust calculation:")
    for fed_id in ["fed:alpha", "fed:beta"]:
        trust = registry.get_federation_trust_from_binding(fed_id)
        print(f"   {fed_id}: binding_trust={trust['binding_trust']:.2f}")
        print(f"     Components: {trust['components']}")

    # Find eligible witnesses
    print("\n7. Eligible witnesses for Beta:")
    eligible = registry.get_eligible_federation_witnesses("fed:beta")
    for fed_id, presence in eligible:
        print(f"   {fed_id}: presence={presence:.2f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
