"""
Web4 Services Test Script
=========================

Simple test script to demonstrate Web4 REST API services.

This script:
1. Mints a new LCT using Identity Service
2. Retrieves LCT information
3. Authorizes an action using Authorization Service
4. Checks service health

Usage:
    python test_services.py

Requirements:
    pip install httpx

Author: Web4 Infrastructure Team
"""

import asyncio
import sys
from typing import Optional

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: pip install httpx")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

IDENTITY_URL = "http://localhost:8001"
AUTH_URL = "http://localhost:8003"

# Test data
TEST_ENTITY = {
    "entity_type": "ai",
    "entity_identifier": "test_research_agent",
    "society": "test_lab",
    "witnesses": ["witness:test_supervisor"]
}


# =============================================================================
# Test Functions
# =============================================================================

async def test_identity_service():
    """Test Identity Service endpoints"""
    print("\n" + "="*70)
    print("Testing Identity Service")
    print("="*70)

    async with httpx.AsyncClient() as client:
        # Test health check
        print("\n1. Health check...")
        response = await client.get(f"{IDENTITY_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service healthy: {data['status']}")
        else:
            print(f"   ❌ Service unhealthy")
            return None

        # Test LCT minting
        print("\n2. Minting new LCT...")
        response = await client.post(
            f"{IDENTITY_URL}/v1/lct/mint",
            json=TEST_ENTITY
        )

        if response.status_code != 201:
            print(f"   ❌ Mint failed: {response.status_code}")
            print(f"      {response.text}")
            return None

        mint_data = response.json()
        if not mint_data.get("success"):
            print(f"   ❌ Mint failed: {mint_data.get('error')}")
            return None

        lct_data = mint_data["data"]
        lct_id = lct_data["lct_id"]
        private_key = lct_data["private_key"]

        print(f"   ✅ LCT minted:")
        print(f"      LCT ID: {lct_id}")
        print(f"      Public Key: {lct_data['public_key'][:32]}...")
        print(f"      Private Key: {private_key[:32]}... (SECURE THIS!)")
        print(f"      Witnesses: {len(lct_data['birth_certificate']['witnesses'])}")

        # Test LCT lookup
        print(f"\n3. Looking up LCT: {lct_id}")
        response = await client.get(f"{IDENTITY_URL}/v1/lct/{lct_id}")

        if response.status_code != 200:
            print(f"   ❌ Lookup failed: {response.status_code}")
            return lct_id, private_key

        lookup_data = response.json()
        if not lookup_data.get("success"):
            print(f"   ❌ Lookup failed: {lookup_data.get('error')}")
            return lct_id, private_key

        info = lookup_data["data"]
        print(f"   ✅ LCT found:")
        print(f"      Entity Type: {info['entity_type']}")
        print(f"      Identifier: {info['entity_identifier']}")
        print(f"      Society: {info['society']}")
        print(f"      Status: {info['status']}")

        # Test birth certificate
        print(f"\n4. Getting birth certificate...")
        response = await client.get(f"{IDENTITY_URL}/v1/lct/{lct_id}/birthcert")

        if response.status_code == 200:
            bc_data = response.json()
            if bc_data.get("success"):
                bc = bc_data["data"]
                print(f"   ✅ Birth certificate:")
                print(f"      Hash: {bc['certificate_hash'][:32]}...")
                print(f"      Witnesses: {bc['witnesses']}")
                print(f"      Created: {bc['creation_time']}")

        return lct_id, private_key


async def test_authorization_service(lct_id: str, private_key: str):
    """Test Authorization Service endpoints"""
    print("\n" + "="*70)
    print("Testing Authorization Service")
    print("="*70)

    async with httpx.AsyncClient() as client:
        # Test health check
        print("\n1. Health check...")
        response = await client.get(f"{AUTH_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service healthy: {data['status']}")
        else:
            print(f"   ❌ Service unhealthy")
            return

        # Test authorization
        print("\n2. Authorizing compute action...")

        # Prepare request
        auth_request = {
            "action": "compute",
            "resource": "model:training:test",
            "atp_cost": 500,
            "context": {
                "delegation_id": "deleg:test:001"
            }
        }

        # Add authentication headers
        # Note: In production, signature would be properly computed
        headers = {
            "Authorization": f"Bearer {lct_id}",
            "X-Signature": "stub_signature_for_testing",
            "X-Nonce": "1699564800"
        }

        response = await client.post(
            f"{AUTH_URL}/v1/auth/authorize",
            json=auth_request,
            headers=headers
        )

        if response.status_code != 200:
            print(f"   ❌ Authorization failed: {response.status_code}")
            print(f"      {response.text}")
            return

        auth_data = response.json()
        if not auth_data.get("success"):
            print(f"   ❌ Authorization failed: {auth_data.get('error')}")
            return

        result = auth_data["data"]
        metadata = auth_data.get("metadata", {})

        print(f"   ✅ Authorization:")
        print(f"      Decision: {result['decision']}")
        print(f"      ATP Remaining: {result.get('atp_remaining', 'N/A')}")
        if result.get("resource_allocation"):
            alloc = result["resource_allocation"]
            print(f"      Resource Allocation:")
            print(f"        CPU: {alloc.get('cpu_cores', 0)} cores")
            print(f"        Memory: {alloc.get('memory_gb', 0)} GB")
            print(f"        Storage: {alloc.get('storage_gb', 0)} GB")
        print(f"      Law Version: {metadata.get('law_version', 'N/A')}")
        print(f"      Duration: {metadata.get('duration_ms', 0):.2f} ms")

        # Test delegation lookup
        print("\n3. Looking up delegation...")
        response = await client.get(
            f"{AUTH_URL}/v1/delegation/deleg:test:001",
            headers=headers
        )

        if response.status_code == 200:
            deleg_data = response.json()
            if deleg_data.get("success"):
                deleg = deleg_data["data"]
                print(f"   ✅ Delegation found:")
                print(f"      Delegator: {deleg['delegator']}")
                print(f"      Role: {deleg['role']}")
                print(f"      Permissions: {deleg['permissions']}")
                print(f"      ATP Budget: {deleg['atp_budget']}")
                print(f"      Status: {deleg['status']}")


async def test_all_services():
    """Run all tests"""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  Web4 Services Test Suite".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    try:
        # Test Identity Service
        result = await test_identity_service()

        if not result:
            print("\n❌ Identity Service tests failed")
            return

        lct_id, private_key = result

        # Test Authorization Service
        await test_authorization_service(lct_id, private_key)

        # Summary
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        print("\n✅ All tests completed successfully!")
        print(f"\nTest LCT created: {lct_id}")
        print(f"Private key: {private_key[:32]}... (for testing only)")

        print("\n" + "="*70)
        print("Next Steps")
        print("="*70)
        print("\n1. Use the Web4 SDK to interact with services:")
        print("   from web4_sdk import Web4Client")
        print("")
        print("2. Check API documentation:")
        print(f"   Identity: {IDENTITY_URL}/docs")
        print(f"   Authorization: {AUTH_URL}/docs")
        print("")
        print("3. Monitor metrics:")
        print(f"   Identity: {IDENTITY_URL}/metrics")
        print(f"   Authorization: {AUTH_URL}/metrics")

    except httpx.ConnectError as e:
        print(f"\n❌ Connection error: {e}")
        print("\nMake sure services are running:")
        print("  python identity_service.py")
        print("  python authorization_service.py")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70 + "\n")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run test suite"""
    try:
        asyncio.run(test_all_services())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
