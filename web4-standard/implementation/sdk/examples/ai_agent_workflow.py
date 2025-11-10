"""
AI Agent Workflow Example
=========================

This example demonstrates a complete AI agent workflow using the Web4 SDK:

1. Agent initializes with delegated authority
2. Agent checks its reputation and ATP budget
3. Agent performs multiple actions (read, compute, write)
4. Each action goes through authorization
5. Outcomes are reported to build reputation
6. Knowledge graph is queried for context

This represents a real-world AI research assistant scenario.

Author: Web4 Infrastructure Team
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web4_sdk import (
    Web4Client,
    Web4Workflow,
    Action,
    OutcomeType,
    AuthorizationDenied,
    InsufficientATP
)


async def simulate_read_papers(auth_result):
    """Simulate reading research papers"""
    print("    📖 Reading research papers...")
    await asyncio.sleep(0.5)  # Simulate work
    print("    ✅ Successfully read 10 papers")
    return {"papers_read": 10, "topics": ["AI safety", "coordination"]}


async def simulate_data_analysis(auth_result):
    """Simulate running data analysis"""
    print("    📊 Running data analysis...")
    await asyncio.sleep(1.0)  # Simulate compute work
    print("    ✅ Analysis complete")
    return {
        "insights": ["Pattern A detected", "Correlation between X and Y"],
        "confidence": 0.85
    }


async def simulate_write_report(auth_result):
    """Simulate writing analysis report"""
    print("    ✍️  Writing analysis report...")
    await asyncio.sleep(0.7)  # Simulate work
    print("    ✅ Report written")
    return {"report_id": "report_001", "pages": 15}


async def main():
    """
    Main workflow for AI research agent.
    """

    print("\n" + "="*70)
    print("  AI Agent Workflow Example - Web4 SDK")
    print("="*70 + "\n")

    # =========================================================================
    # Step 1: Initialize Web4 Client
    # =========================================================================

    print("📡 Initializing Web4 client...")

    # In production, these would come from environment or config
    client = Web4Client(
        identity_url="http://localhost:8001",
        auth_url="http://localhost:8003",
        reputation_url="http://localhost:8004",
        resources_url="http://localhost:8005",
        knowledge_url="http://localhost:8006",
        governance_url="http://localhost:8002",
        lct_id="lct:web4:ai:research_lab:agent_001",
        private_key=bytes(32)  # In production, load from secure storage
    )

    workflow = Web4Workflow(client)

    async with client:  # Use context manager for automatic cleanup

        # =====================================================================
        # Step 2: Check Agent Status
        # =====================================================================

        print("\n🔍 Checking agent status...\n")

        try:
            # Get LCT info
            lct_info = await client.get_lct_info()
            print(f"✅ LCT ID: {lct_info.lct_id}")
            print(f"   Entity Type: {lct_info.entity_type}")
            print(f"   Society: {lct_info.society}")
            print(f"   Status: {lct_info.status}")
            print(f"   Witnesses: {len(lct_info.witnesses)}")

            # Get reputation scores
            reputation = await client.get_reputation(role="research_assistant")
            print(f"\n📊 Reputation Scores:")
            print(f"   T3 (Trustworthiness): {reputation.t3_score:.3f}")
            print(f"   V3 (Value Creation): {reputation.v3_score:.3f}")
            print(f"   Total Actions: {reputation.action_count}")

            # Get law version
            law_info = await client.get_law_version()
            print(f"\n⚖️  Current Law: {law_info['version']}")

        except Exception as e:
            print(f"⚠️  Status check failed: {e}")
            print("   Continuing with demo (services may not be running)")

        # =====================================================================
        # Step 3: Execute Research Tasks
        # =====================================================================

        print("\n" + "="*70)
        print("  Executing Research Tasks")
        print("="*70 + "\n")

        tasks = [
            {
                "name": "Read Research Papers",
                "action": Action.READ,
                "resource": "papers:arxiv:ai_safety",
                "atp_cost": 100,
                "executor": simulate_read_papers
            },
            {
                "name": "Run Data Analysis",
                "action": Action.COMPUTE,
                "resource": "model:analysis:statistical",
                "atp_cost": 300,
                "executor": simulate_data_analysis
            },
            {
                "name": "Write Analysis Report",
                "action": Action.WRITE,
                "resource": "doc:report:analysis_001",
                "atp_cost": 150,
                "executor": simulate_write_report
            }
        ]

        results = []

        for i, task in enumerate(tasks, 1):
            print(f"\n{'─'*70}")
            print(f"Task {i}/{len(tasks)}: {task['name']}")
            print(f"{'─'*70}")

            try:
                # Execute complete workflow: authorize -> execute -> report
                result, updated_reputation = await workflow.execute_action_with_reporting(
                    action=task['action'],
                    resource=task['resource'],
                    atp_cost=task['atp_cost'],
                    executor_fn=task['executor'],
                    context={"delegation_id": "deleg:supervisor:001"}
                )

                print(f"\n  ✅ Task completed successfully")
                print(f"     Result: {result}")
                print(f"     Updated T3: {updated_reputation.t3_score:.3f}")
                print(f"     Updated V3: {updated_reputation.v3_score:.3f}")

                results.append({
                    "task": task['name'],
                    "status": "success",
                    "result": result,
                    "reputation": updated_reputation
                })

            except AuthorizationDenied as e:
                print(f"\n  ❌ Authorization denied: {e}")
                results.append({
                    "task": task['name'],
                    "status": "denied",
                    "error": str(e)
                })

            except InsufficientATP as e:
                print(f"\n  ❌ Insufficient ATP: {e}")
                results.append({
                    "task": task['name'],
                    "status": "insufficient_atp",
                    "error": str(e)
                })
                break  # Can't continue without ATP

            except Exception as e:
                print(f"\n  ⚠️  Task failed: {e}")
                results.append({
                    "task": task['name'],
                    "status": "error",
                    "error": str(e)
                })

        # =====================================================================
        # Step 4: Query Knowledge Graph
        # =====================================================================

        print("\n" + "="*70)
        print("  Querying Knowledge Graph")
        print("="*70 + "\n")

        try:
            # Query for trust relationships
            trust_data = await client.get_trust_propagation(
                start_entity=client.lct_id,
                max_depth=2
            )

            print(f"🕸️  Trust Network:")
            print(f"   Direct connections: {len(trust_data.get('direct', []))}")
            print(f"   Extended network: {len(trust_data.get('extended', []))}")

            # SPARQL query for recent actions
            sparql = f"""
            SELECT ?action ?timestamp WHERE {{
                <{client.lct_id}> performed ?action .
                ?action timestamp ?timestamp .
            }}
            ORDER BY DESC(?timestamp)
            LIMIT 5
            """

            recent_actions = await client.query_knowledge_graph(sparql)
            print(f"\n📝 Recent Actions: {len(recent_actions)}")

        except Exception as e:
            print(f"⚠️  Knowledge graph query failed: {e}")
            print("   (This is expected if services are not running)")

        # =====================================================================
        # Step 5: Final Summary
        # =====================================================================

        print("\n" + "="*70)
        print("  Workflow Complete - Summary")
        print("="*70 + "\n")

        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] != 'success')

        print(f"📈 Tasks Completed: {successful}/{len(tasks)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")

        if results:
            final_reputation = results[-1].get('reputation')
            if final_reputation:
                print(f"\n🏆 Final Reputation:")
                print(f"   T3: {final_reputation.t3_score:.3f}")
                print(f"   V3: {final_reputation.v3_score:.3f}")
                print(f"   Total Actions: {final_reputation.action_count}")

        print("\n✅ Workflow demonstration complete!")

        # =====================================================================
        # Step 6: Health Check
        # =====================================================================

        print("\n" + "="*70)
        print("  Service Health Check")
        print("="*70 + "\n")

        health = await workflow.health_check()

        for service, status in health.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {service.capitalize()}: {'UP' if status else 'DOWN'}")

    print("\n" + "="*70)
    print("  Session Closed")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
