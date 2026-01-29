# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Admin Binding (Hardware Security)
# https://github.com/dp-web4/web4

"""
Admin Binding: Hardware-secured admin identity.

Production admin roles MUST be hardware-bound to prevent impersonation.
This module provides:
- TPM2 binding for admin LCTs
- Binding verification
- Admin attestation
- Fallback to software binding for development

Key insight: Whoever controls the admin key controls the team.
Hardware binding makes this key non-extractable.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import sys

# Import TPM2 provider
_tpm_path = Path(__file__).parent.parent / "core" / "lct_binding"
sys.path.insert(0, str(_tpm_path))
sys.path.insert(0, str(_tpm_path.parent))
try:
    from lct_binding.tpm2_provider import TPM2Provider
    TPM2_AVAILABLE = True
except ImportError:
    try:
        from tpm2_provider import TPM2Provider
        TPM2_AVAILABLE = True
    except ImportError:
        TPM2_AVAILABLE = False
        TPM2Provider = None

# Import governance (self-contained)
from .ledger import Ledger

if TYPE_CHECKING:
    from .team import Team


class AdminBindingType(Enum):
    """Types of admin binding."""
    SOFTWARE = "software"    # Soft LCT - development only
    TPM2 = "tpm2"           # TPM 2.0 hardware binding
    FIDO2 = "fido2"         # FIDO2/WebAuthn - not yet implemented


@dataclass
class AdminBinding:
    """Admin binding record."""
    binding_type: AdminBindingType
    lct_id: str
    public_key: Optional[str] = None
    hardware_anchor: Optional[str] = None
    attestation: Optional[str] = None
    bound_at: Optional[str] = None
    verified: bool = False


class AdminBindingManager:
    """
    Manages admin binding for teams.

    Production requirements:
    - Admin MUST have hardware binding (TPM2 or FIDO2)
    - Software binding allowed for development with explicit flag
    - All binding changes recorded in audit trail
    - Binding can be verified cryptographically
    """

    def __init__(self, ledger: Optional[Ledger] = None):
        """
        Initialize admin binding manager.

        Args:
            ledger: Ledger for audit trail
        """
        self.ledger = ledger or Ledger()
        self._tpm_provider: Optional[TPM2Provider] = None
        self._ensure_table()

    def _ensure_table(self):
        """Create admin bindings table if not exists."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_bindings (
                    team_id TEXT PRIMARY KEY,
                    lct_id TEXT NOT NULL,
                    binding_type TEXT NOT NULL,
                    public_key TEXT,
                    hardware_anchor TEXT,
                    attestation TEXT,
                    bound_at TEXT NOT NULL,
                    verified INTEGER DEFAULT 0
                )
            """)

    @property
    def tpm_provider(self) -> Optional[TPM2Provider]:
        """Get TPM2 provider (lazy init)."""
        if self._tpm_provider is None and TPM2_AVAILABLE:
            try:
                self._tpm_provider = TPM2Provider()
            except Exception:
                pass
        return self._tpm_provider

    def get_tpm_status(self) -> dict:
        """Get TPM availability status."""
        if not TPM2_AVAILABLE:
            return {
                "available": False,
                "reason": "TPM2 provider module not found",
                "recommendation": "Install tpm2-tools and ensure core/lct_binding/tpm2_provider.py exists"
            }

        provider = self.tpm_provider
        if provider is None:
            return {
                "available": False,
                "reason": "TPM2 provider failed to initialize",
                "recommendation": "Check TPM2 tools installation and access permissions"
            }

        if not provider._tpm_available:
            return {
                "available": False,
                "reason": "TPM2 tools not accessible",
                "recommendation": "Run: sudo apt install tpm2-tools && sudo usermod -a -G tss $USER"
            }

        return {
            "available": True,
            "hardware_type": "TPM2",
            "trust_ceiling": provider.trust_ceiling,
            "platform": provider.get_platform_info().name if provider.get_platform_info() else "unknown"
        }

    def bind_admin_tpm2(self, team_id: str, admin_name: str = "admin") -> AdminBinding:
        """
        Bind admin to TPM2 hardware.

        Args:
            team_id: Team ID to bind admin for
            admin_name: Name for the admin entity

        Returns:
            AdminBinding record

        Raises:
            RuntimeError: If TPM2 not available
        """
        if not TPM2_AVAILABLE or self.tpm_provider is None:
            raise RuntimeError(
                "TPM2 not available. For development, use bind_admin_software() "
                "with require_hardware=False"
            )

        if not self.tpm_provider._tpm_available:
            raise RuntimeError(
                "TPM2 tools not accessible. Install tpm2-tools and ensure TPM access."
            )

        # Generate TPM-bound LCT for admin
        from core.lct_binding.lct_capability_levels import EntityType
        lct = self.tpm_provider.create_lct(EntityType.HUMAN, f"admin-{admin_name}")

        # Get attestation
        key_id = lct.lct_id.split(':')[-1]
        attestation_result = self.tpm_provider.get_attestation(key_id)

        now = datetime.now(timezone.utc).isoformat()

        binding = AdminBinding(
            binding_type=AdminBindingType.TPM2,
            lct_id=lct.lct_id,
            public_key=lct.binding.public_key,
            hardware_anchor=lct.binding.hardware_anchor,
            attestation=attestation_result.attestation_token if attestation_result.success else None,
            bound_at=now,
            verified=attestation_result.success
        )

        # Store binding
        self._store_binding(team_id, binding)

        # Audit trail
        self.ledger.record_audit(
            session_id=team_id,
            action_type="admin_bound_tpm2",
            tool_name="hardbound",
            target=lct.lct_id,
            r6_data={
                "binding_type": "tpm2",
                "hardware_anchor": lct.binding.hardware_anchor,
                "verified": binding.verified,
                "trust_ceiling": self.tpm_provider.trust_ceiling
            }
        )

        return binding

    def bind_admin_software(
        self,
        team_id: str,
        lct_id: str,
        require_hardware: bool = True
    ) -> AdminBinding:
        """
        Bind admin with software LCT.

        Args:
            team_id: Team ID
            lct_id: Existing soft LCT ID
            require_hardware: If True, raise error (production mode)

        Returns:
            AdminBinding record

        Raises:
            ValueError: If require_hardware=True (production mode)
        """
        if require_hardware:
            raise ValueError(
                "Software binding not allowed for production. "
                "Use bind_admin_tpm2() for hardware binding, or set "
                "require_hardware=False for development."
            )

        now = datetime.now(timezone.utc).isoformat()

        binding = AdminBinding(
            binding_type=AdminBindingType.SOFTWARE,
            lct_id=lct_id,
            bound_at=now,
            verified=False  # Software bindings are never verified
        )

        # Store binding
        self._store_binding(team_id, binding)

        # Audit trail with warning
        self.ledger.record_audit(
            session_id=team_id,
            action_type="admin_bound_software",
            tool_name="hardbound",
            target=lct_id,
            r6_data={
                "binding_type": "software",
                "warning": "DEVELOPMENT MODE - Software binding provides no hardware security",
                "trust_ceiling": 0.7
            }
        )

        return binding

    def get_binding(self, team_id: str) -> Optional[AdminBinding]:
        """Get admin binding for a team."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM admin_bindings WHERE team_id = ?",
                (team_id,)
            ).fetchone()

            if not row:
                return None

            return AdminBinding(
                binding_type=AdminBindingType(row["binding_type"]),
                lct_id=row["lct_id"],
                public_key=row["public_key"],
                hardware_anchor=row["hardware_anchor"],
                attestation=row["attestation"],
                bound_at=row["bound_at"],
                verified=bool(row["verified"])
            )

    def verify_admin(self, team_id: str, lct_id: str, signature: bytes = None,
                     challenge: bytes = None) -> dict:
        """
        Verify admin identity.

        For TPM2 binding:
        - Optionally verify signature on challenge
        - Check attestation freshness

        For software binding:
        - Only checks LCT ID match

        Args:
            team_id: Team ID
            lct_id: LCT claiming to be admin
            signature: Optional signature on challenge
            challenge: Optional challenge data

        Returns:
            Verification result dict
        """
        binding = self.get_binding(team_id)
        if not binding:
            return {
                "verified": False,
                "reason": "No admin binding found for team"
            }

        if binding.lct_id != lct_id:
            return {
                "verified": False,
                "reason": "LCT ID does not match admin binding"
            }

        # For software binding, just return match result
        if binding.binding_type == AdminBindingType.SOFTWARE:
            return {
                "verified": True,
                "binding_type": "software",
                "warning": "Software binding - no cryptographic verification",
                "trust_ceiling": 0.7
            }

        # For TPM2 binding, verify signature if provided
        if binding.binding_type == AdminBindingType.TPM2:
            result = {
                "verified": True,
                "binding_type": "tpm2",
                "hardware_anchor": binding.hardware_anchor,
                "trust_ceiling": 1.0
            }

            if signature and challenge and binding.public_key:
                # Verify signature
                if self.tpm_provider:
                    sig_valid = self.tpm_provider.verify_signature(
                        binding.public_key, challenge, signature
                    )
                    result["signature_valid"] = sig_valid
                    if not sig_valid:
                        result["verified"] = False
                        result["reason"] = "Signature verification failed"

            return result

        return {
            "verified": False,
            "reason": f"Unknown binding type: {binding.binding_type}"
        }

    def _store_binding(self, team_id: str, binding: AdminBinding):
        """Store admin binding in database."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO admin_bindings
                (team_id, lct_id, binding_type, public_key, hardware_anchor,
                 attestation, bound_at, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team_id,
                binding.lct_id,
                binding.binding_type.value,
                binding.public_key,
                binding.hardware_anchor,
                binding.attestation,
                binding.bound_at,
                1 if binding.verified else 0
            ))


def check_tpm_availability() -> dict:
    """
    Quick check for TPM availability.

    Returns:
        Status dict with availability info
    """
    manager = AdminBindingManager()
    return manager.get_tpm_status()


if __name__ == "__main__":
    print("=" * 60)
    print("Admin Binding - TPM Status Check")
    print("=" * 60)

    status = check_tpm_availability()
    print(f"\nTPM Available: {status.get('available', False)}")

    if status.get('available'):
        print(f"Hardware Type: {status.get('hardware_type')}")
        print(f"Trust Ceiling: {status.get('trust_ceiling')}")
        print(f"Platform: {status.get('platform')}")
    else:
        print(f"Reason: {status.get('reason')}")
        print(f"Recommendation: {status.get('recommendation')}")

    print("\n" + "=" * 60)
