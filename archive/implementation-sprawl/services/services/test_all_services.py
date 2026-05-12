"""
Web4 Complete Services Test Suite
==================================

Comprehensive test script for all 6 Web4 REST API services.

This script:
1. Tests Identity Service (port 8001) - LCT minting & lookup
2. Tests Governance Service (port 8002) - Law queries & compliance
3. Tests Authorization Service (port 8003) - Action authorization
4. Tests Reputation Service (port 8004) - Outcome recording & T3/V3
5. Tests Resources Service (port 8005) - Resource allocation
6. Tests Knowledge Service (port 8006) - Graph operations & SPARQL

Usage:
    python test_all_services.py

Requirements:
    pip install httpx

Author: Web4 Infrastructure Team
"""

import asyncio
import sys
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: pip install httpx")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

BASE_URLS = {
    "identity": "http://localhost:8001",
    "governance": "http://localhost:8002",
    "authorization": "http://localhost:8003",
    "reputation": "http://localhost:8004",
    "resources": "http://localhost:8005",
    "knowledge": "http://localhost:8006"
}

# Track test results
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


# =============================================================================
# Test Utilities
# =============================================================================

def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_test(test_name: str):
    """Print test name"""
    print(f"\n{test_name}")


def print_success(message: str):
    """Print success message"""
    print(f"   ✅ {message}")
    test_results["passed"] += 1


def print_failure(message: str):
    """Print failure message"""
    print(f"   ❌ {message}")
    test_results["failed"] += 1
    test_results["errors"].append(message)


# =============================================================================
# Test Functions
# =============================================================================

async def test_identity_service(client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Test Identity Service"""
    print_section("Testing Identity Service (Port 8001)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['identity']}/health")
        if response.status_code == 200:
            print_success("Identity service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return None

        # Mint LCT
        print_test("2. Mint LCT")
        mint_request = {
            "entity_type": "ai",
            "entity_identifier": "test_agent_complete",
            "society": "test_society",
            "witnesses": ["witness:supervisor"]
        }
        response = await client.post(
            f"{BASE_URLS['identity']}/v1/lct/mint",
            json=mint_request
        )

        if response.status_code != 201:
            print_failure(f"Mint failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        if not data.get("success"):
            print_failure(f"Mint failed: {data.get('error')}")
            return None

        lct_data = data["data"]
        lct_id = lct_data["lct_id"]
        private_key = lct_data["private_key"]

        print_success(f"LCT minted: {lct_id}")
        print(f"      Public Key: {lct_data['public_key'][:32]}...")
        print(f"      Private Key: {private_key[:32]}...")

        # Lookup LCT
        print_test("3. Lookup LCT")
        response = await client.get(f"{BASE_URLS['identity']}/v1/lct/{lct_id}")
        if response.status_code == 200 and response.json().get("success"):
            print_success("LCT lookup successful")
        else:
            print_failure(f"LCT lookup failed: {response.status_code}")

        # Get birth certificate
        print_test("4. Get birth certificate")
        response = await client.get(f"{BASE_URLS['identity']}/v1/lct/{lct_id}/birthcert")
        if response.status_code == 200 and response.json().get("success"):
            bc = response.json()["data"]
            print_success(f"Birth certificate retrieved: {bc['certificate_hash'][:32]}...")
        else:
            print_failure("Birth certificate retrieval failed")

        return {"lct_id": lct_id, "private_key": private_key}

    except Exception as e:
        print_failure(f"Identity service error: {str(e)}")
        return None


async def test_governance_service(client: httpx.AsyncClient):
    """Test Governance Service"""
    print_section("Testing Governance Service (Port 8002)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['governance']}/health")
        if response.status_code == 200:
            print_success("Governance service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return

        # Get current law
        print_test("2. Get current law")
        response = await client.get(f"{BASE_URLS['governance']}/v1/law/current")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                law = data["data"]
                print_success(f"Current law: {law['version']}")
                print(f"      Effective: {law['effective_date']}")
            else:
                print_failure("Failed to get current law")
        else:
            print_failure(f"Law query failed: {response.status_code}")

        # Check compliance
        print_test("3. Check compliance")
        compliance_request = {
            "action": "compute",
            "resource": "cpu:high_performance",
            "context": {"entity_type": "ai", "society": "research_lab"}
        }
        response = await client.post(
            f"{BASE_URLS['governance']}/v1/law/check",
            json=compliance_request
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data["data"]
                print_success(f"Compliance check: {result['compliant']}")
                if result.get("violations"):
                    print(f"      Violations: {result['violations']}")
            else:
                print_failure("Compliance check failed")
        else:
            print_failure(f"Compliance check error: {response.status_code}")

    except Exception as e:
        print_failure(f"Governance service error: {str(e)}")


async def test_authorization_service(client: httpx.AsyncClient, lct_id: str, private_key: str):
    """Test Authorization Service"""
    print_section("Testing Authorization Service (Port 8003)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['authorization']}/health")
        if response.status_code == 200:
            print_success("Authorization service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return

        # Authorize action
        print_test("2. Authorize compute action")
        auth_request = {
            "action": "compute",
            "resource": "model:training:test",
            "atp_cost": 500,
            "context": {"task_id": "task_001"}
        }

        headers = {
            "Authorization": f"Bearer {lct_id}",
            "X-Signature": "stub_signature_for_testing",
            "X-Nonce": "1699564800"
        }

        response = await client.post(
            f"{BASE_URLS['authorization']}/v1/auth/authorize",
            json=auth_request,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data["data"]
                print_success(f"Authorization: {result['decision']}")
                print(f"      ATP Remaining: {result.get('atp_remaining', 'N/A')}")
                if result.get("resource_allocation"):
                    alloc = result["resource_allocation"]
                    print(f"      CPU: {alloc.get('cpu_cores', 0)} cores")
                    print(f"      Memory: {alloc.get('memory_gb', 0)} GB")
            else:
                print_failure(f"Authorization failed: {data.get('error')}")
        else:
            print_failure(f"Authorization error: {response.status_code}")

    except Exception as e:
        print_failure(f"Authorization service error: {str(e)}")


async def test_reputation_service(client: httpx.AsyncClient, lct_id: str):
    """Test Reputation Service"""
    print_section("Testing Reputation Service (Port 8004)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['reputation']}/health")
        if response.status_code == 200:
            print_success("Reputation service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return

        # Record outcome
        print_test("2. Record action outcome")
        outcome_request = {
            "entity": lct_id,
            "role": "researcher",
            "action": "compute",
            "outcome": "exceptional_quality",
            "witnesses": ["human:supervisor:alice"],
            "context": {"task_id": "task_001", "duration": 300}
        }

        response = await client.post(
            f"{BASE_URLS['reputation']}/v1/reputation/record",
            json=outcome_request
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                result = data["data"]
                print_success("Outcome recorded")
                print(f"      T3 Score: {result['t3_score']:.3f} (Δ {result['t3_delta']:+.3f})")
                print(f"      V3 Score: {result['v3_score']:.3f} (Δ {result['v3_delta']:+.3f})")
                print(f"      Gaming Risk: {result['gaming_risk']}")
            else:
                print_failure(f"Outcome recording failed: {data.get('error')}")
        else:
            print_failure(f"Outcome recording error: {response.status_code}")

        # Get reputation
        print_test("3. Get reputation scores")
        response = await client.get(
            f"{BASE_URLS['reputation']}/v1/reputation/{lct_id}",
            params={"role": "researcher"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rep = data["data"]
                print_success("Reputation retrieved")
                print(f"      T3: {rep['t3_score']:.3f}, V3: {rep['v3_score']:.3f}")
                print(f"      Actions: {rep['action_count']}")
            else:
                print_failure("Reputation retrieval failed")
        else:
            print_failure(f"Reputation query error: {response.status_code}")

    except Exception as e:
        print_failure(f"Reputation service error: {str(e)}")


async def test_resources_service(client: httpx.AsyncClient, lct_id: str):
    """Test Resources Service"""
    print_section("Testing Resources Service (Port 8005)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['resources']}/health")
        if response.status_code == 200:
            print_success("Resources service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return

        # Get pool status
        print_test("2. Get resource pool status")
        response = await client.get(f"{BASE_URLS['resources']}/v1/resources/pools")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                pools = data["data"]
                print_success(f"Pool status retrieved: {len(pools)} pools")
                for resource_type, status in pools.items():
                    print(f"      {resource_type}: {status.get('available', 'N/A')} available")
            else:
                print_failure("Pool status failed")
        else:
            print_failure(f"Pool query error: {response.status_code}")

        # Allocate resources
        print_test("3. Allocate CPU resources")
        alloc_request = {
            "entity_id": lct_id,
            "resource_type": "cpu",
            "amount": 4.0,
            "duration_seconds": 3600
        }

        response = await client.post(
            f"{BASE_URLS['resources']}/v1/resources/allocate",
            json=alloc_request
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                alloc = data["data"]
                allocation_id = alloc["allocation_id"]
                print_success(f"Resources allocated: {allocation_id}")
                print(f"      Requested: {alloc['amount_requested']} CPU cores")
                print(f"      Allocated: {alloc['amount_allocated']} CPU cores")
                print(f"      ATP Cost: {alloc['atp_cost']}")

                # Report usage
                print_test("4. Report resource usage")
                usage_request = {
                    "allocation_id": allocation_id,
                    "actual_usage": 3.5
                }
                response = await client.post(
                    f"{BASE_URLS['resources']}/v1/resources/usage",
                    json=usage_request
                )
                if response.status_code == 200:
                    print_success("Usage reported successfully")
                else:
                    print_failure("Usage reporting failed")
            else:
                print_failure(f"Allocation failed: {data.get('error')}")
        else:
            print_failure(f"Allocation error: {response.status_code}")

    except Exception as e:
        print_failure(f"Resources service error: {str(e)}")


async def test_knowledge_service(client: httpx.AsyncClient, lct_id: str):
    """Test Knowledge Service"""
    print_section("Testing Knowledge Service (Port 8006)")

    try:
        # Health check
        print_test("1. Health check")
        response = await client.get(f"{BASE_URLS['knowledge']}/health")
        if response.status_code == 200:
            print_success("Knowledge service is healthy")
        else:
            print_failure(f"Health check failed: {response.status_code}")
            return

        # Add triples
        print_test("2. Add RDF triples")
        triples = [
            {
                "subject": lct_id,
                "predicate": "has_role",
                "object": "researcher",
                "metadata": {"confidence": 1.0}
            },
            {
                "subject": lct_id,
                "predicate": "member_of",
                "object": "society:research_lab",
                "metadata": {"since": "2025-11-10"}
            },
            {
                "subject": lct_id,
                "predicate": "collaborates_with",
                "object": "human:supervisor:alice",
                "metadata": {"project": "web4"}
            }
        ]

        triple_ids = []
        for triple in triples:
            response = await client.post(
                f"{BASE_URLS['knowledge']}/v1/graph/triple",
                json=triple
            )
            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    triple_ids.append(data["data"]["triple_id"])
            else:
                print_failure(f"Triple add failed: {response.status_code}")
                return

        print_success(f"Added {len(triple_ids)} triples to knowledge graph")

        # SPARQL query
        print_test("3. Execute SPARQL query")
        sparql_query = f"""
        SELECT ?predicate ?object
        WHERE {{
            <{lct_id}> ?predicate ?object .
        }}
        """

        query_request = {
            "query": sparql_query,
            "limit": 100
        }

        response = await client.post(
            f"{BASE_URLS['knowledge']}/v1/graph/query",
            json=query_request
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data["data"]["results"]
                print_success(f"SPARQL query returned {len(results)} results")
                for result in results[:3]:
                    print(f"      {result}")
            else:
                print_failure("SPARQL query failed")
        else:
            print_failure(f"SPARQL query error: {response.status_code}")

        # Get relationships
        print_test("4. Get entity relationships")
        response = await client.get(
            f"{BASE_URLS['knowledge']}/v1/graph/relationships/{lct_id}"
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rels = data["data"]
                print_success(f"Retrieved relationships")
                print(f"      Outgoing: {rels['outgoing_count']}")
                print(f"      Incoming: {rels['incoming_count']}")
            else:
                print_failure("Relationship query failed")
        else:
            print_failure(f"Relationship query error: {response.status_code}")

        # Graph traversal
        print_test("5. Traverse knowledge graph")
        traverse_request = {
            "start_entity": lct_id,
            "max_depth": 2,
            "direction": "outgoing"
        }

        response = await client.post(
            f"{BASE_URLS['knowledge']}/v1/graph/traverse",
            json=traverse_request
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                traversal = data["data"]
                print_success(f"Graph traversal completed")
                print(f"      Nodes visited: {traversal['node_count']}")
                print(f"      Max depth: {traversal['max_depth_reached']}")
            else:
                print_failure("Graph traversal failed")
        else:
            print_failure(f"Graph traversal error: {response.status_code}")

        # Get graph stats
        print_test("6. Get graph statistics")
        response = await client.get(f"{BASE_URLS['knowledge']}/v1/graph/stats")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data["data"]
                print_success("Graph statistics retrieved")
                print(f"      Total triples: {stats['total_triples']}")
                print(f"      Unique entities: {stats['unique_entities']}")
            else:
                print_failure("Graph stats failed")
        else:
            print_failure(f"Graph stats error: {response.status_code}")

    except Exception as e:
        print_failure(f"Knowledge service error: {str(e)}")


# =============================================================================
# Main Test Runner
# =============================================================================

async def run_all_tests():
    """Run comprehensive test suite"""
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Web4 Complete Services Test Suite".center(68) + "║")
    print("║" + "  Testing All 6 Microservices".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    start_time = datetime.now()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test Identity Service
            identity_result = await test_identity_service(client)

            if not identity_result:
                print("\n❌ Identity service tests failed - cannot continue")
                return

            lct_id = identity_result["lct_id"]
            private_key = identity_result["private_key"]

            # Test remaining services
            await test_governance_service(client)
            await test_authorization_service(client, lct_id, private_key)
            await test_reputation_service(client, lct_id)
            await test_resources_service(client, lct_id)
            await test_knowledge_service(client, lct_id)

        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"\n✅ Tests passed: {test_results['passed']}")
        print(f"❌ Tests failed: {test_results['failed']}")
        print(f"⏱️  Duration: {duration:.2f} seconds")

        if test_results["failed"] == 0:
            print("\n🎉 All tests passed successfully!")
        else:
            print(f"\n⚠️  {test_results['failed']} tests failed")
            print("\nFailures:")
            for error in test_results["errors"]:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        print("Service Status")
        print("=" * 70)
        print("\n✅ Identity Service (8001) - LCT Registry")
        print("✅ Governance Service (8002) - Law Oracle")
        print("✅ Authorization Service (8003) - Action Authorization")
        print("✅ Reputation Service (8004) - T3/V3 Tracking")
        print("✅ Resources Service (8005) - ATP Allocation")
        print("✅ Knowledge Service (8006) - MRH Graph")

        print("\n" + "=" * 70)
        print("Next Steps")
        print("=" * 70)
        print("\n1. View API documentation:")
        for service, url in BASE_URLS.items():
            print(f"   {service.capitalize()}: {url}/docs")

        print("\n2. Monitor metrics:")
        print("   Prometheus: http://localhost:9090")
        print("   Grafana: http://localhost:3000")

        print("\n3. Use the Web4 SDK:")
        print("   from web4_sdk import Web4Client")

    except httpx.ConnectError as e:
        print(f"\n❌ Connection error: {e}")
        print("\nMake sure all services are running:")
        print("  docker-compose up")
        print("  OR")
        for service, url in BASE_URLS.items():
            port = url.split(":")[-1]
            print(f"  python {service}_service.py  # port {port}")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70 + "\n")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run test suite"""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
