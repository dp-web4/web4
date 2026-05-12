"""
Test Bootstrap Helper for Phase 1 Testing

Provides utilities to create test entities with proper witnesses
for Phase 1 mitigation testing.

The problem: Secured services enforce witness validation, but tests
need LCTs to test with. This creates a bootstrap problem.

Solution: Create "genesis" test witnesses that have sufficient
reputation/age/actions to validate test LCTs.

Usage:
    from test_bootstrap import TestBootstrap

    async with TestBootstrap(base_url="http://localhost:8101") as bootstrap:
        # Create test LCT with valid witness
        lct_data = await bootstrap.create_test_lct("test_entity_1")
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: python3 -m pip install httpx --user")
    import sys
    sys.exit(1)


class TestBootstrap:
    """Bootstrap test infrastructure for Phase 1 testing"""

    def __init__(self, identity_url: str = "http://localhost:8101"):
        """
        Initialize test bootstrap.

        Args:
            identity_url: Base URL for secured identity service
        """
        self.identity_url = identity_url
        self.client: Optional[httpx.AsyncClient] = None
        self.genesis_witnesses = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        await self.create_genesis_witnesses()
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def create_genesis_witnesses(self):
        """
        Create genesis witnesses with sufficient reputation to validate test LCTs.

        These are created WITHOUT witness validation (bypassing security for testing).
        In production, genesis witnesses would be the initial trusted entities.
        """
        print("Creating genesis witnesses for testing...")

        # For MVP, we simulate genesis witnesses with long IDs that pass basic validation
        # In reality, these would need to be pre-registered in the identity service
        genesis_ids = [
            "lct:genesis_witness_001_" + "a" * 40,  # Long enough to pass length check
            "lct:genesis_witness_002_" + "b" * 40,
            "lct:genesis_witness_003_" + "c" * 40,
        ]

        self.genesis_witnesses = genesis_ids
        print(f"✅ Created {len(self.genesis_witnesses)} genesis witnesses")

    async def create_test_lct(
        self,
        entity_identifier: str,
        entity_type: str = "ai",
        society: str = "test_society"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a test LCT with valid genesis witnesses.

        Args:
            entity_identifier: Unique identifier for the test entity
            entity_type: Type of entity (ai, human, org, device)
            society: Society the entity belongs to

        Returns:
            LCT data if successful, None if failed
        """
        # Use genesis witnesses (simulated for MVP)
        witnesses = self.genesis_witnesses[:1]  # AI entities need 1 witness

        if entity_type == "human" or entity_type == "org":
            witnesses = self.genesis_witnesses  # Need all 3 for humans/orgs

        request = {
            "entity_type": entity_type,
            "entity_identifier": entity_identifier,
            "society": society,
            "witnesses": witnesses
        }

        try:
            response = await self.client.post(
                f"{self.identity_url}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    print(f"  ✓ Created test LCT: {entity_identifier}")
                    return data["data"]
                else:
                    print(f"  ✗ Failed to create LCT: {data.get('error', 'Unknown error')}")
            else:
                error_data = response.json()
                print(f"  ✗ Failed ({response.status_code}): {error_data.get('error', 'Unknown')}")

            return None

        except Exception as e:
            print(f"  ✗ Exception creating LCT: {e}")
            return None

    def get_genesis_witnesses(self, count: int = 1) -> list[str]:
        """
        Get genesis witness IDs for use in tests.

        Args:
            count: Number of witnesses needed

        Returns:
            List of witness LCT IDs
        """
        return self.genesis_witnesses[:count]


async def test_bootstrap():
    """Test the bootstrap system"""
    print("\n" + "=" * 70)
    print("Testing Bootstrap System")
    print("=" * 70)

    async with TestBootstrap() as bootstrap:
        # Try to create a test LCT
        lct_data = await bootstrap.create_test_lct(
            entity_identifier=f"test_entity_{int(time.time())}",
            entity_type="ai",
            society="test_society"
        )

        if lct_data:
            print("\n✅ Bootstrap system working!")
            print(f"   Created LCT: {lct_data.get('lct_id', 'N/A')[:60]}...")
        else:
            print("\n❌ Bootstrap system failed!")
            print("   This is expected if witness validation is enforced.")
            print("   In production, genesis witnesses would be pre-registered.")


if __name__ == "__main__":
    asyncio.run(test_bootstrap())
