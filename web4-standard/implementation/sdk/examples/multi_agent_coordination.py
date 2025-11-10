"""
Multi-Agent Coordination Example
=================================

This example demonstrates multiple AI agents coordinating through Web4:

Scenario: Research team with supervisor and two specialist agents
- Supervisor (human) delegates to agents
- Data analysis agent processes datasets
- Report writing agent creates documentation
- Agents respect ATP budgets and build reputation
- Knowledge graph tracks collaboration

This shows real-world multi-agent systems built on Web4.

Author: Web4 Infrastructure Team
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web4_sdk import (
    Web4Client,
    Web4Workflow,
    Action,
    OutcomeType,
    ReputationScore
)


class Agent:
    """
    Base agent class wrapping Web4Client.
    """

    def __init__(
        self,
        name: str,
        lct_id: str,
        private_key: bytes,
        role: str,
        services: Dict[str, str]
    ):
        self.name = name
        self.lct_id = lct_id
        self.role = role

        self.client = Web4Client(
            identity_url=services['identity'],
            auth_url=services['auth'],
            reputation_url=services.get('reputation'),
            resources_url=services.get('resources'),
            knowledge_url=services.get('knowledge'),
            governance_url=services.get('governance'),
            lct_id=lct_id,
            private_key=private_key
        )

        self.workflow = Web4Workflow(self.client)
        self.action_log: List[Dict] = []

    async def __aenter__(self):
        await self.client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        try:
            reputation = await self.client.get_reputation(role=self.role)
            return {
                "name": self.name,
                "lct_id": self.lct_id,
                "role": self.role,
                "t3_score": reputation.t3_score,
                "v3_score": reputation.v3_score,
                "actions": reputation.action_count,
                "available": True
            }
        except Exception as e:
            return {
                "name": self.name,
                "lct_id": self.lct_id,
                "role": self.role,
                "available": False,
                "error": str(e)
            }

    async def execute_task(
        self,
        task_name: str,
        action: Action,
        resource: str,
        atp_cost: int,
        executor_fn
    ) -> Dict[str, Any]:
        """Execute a task with full Web4 workflow"""
        print(f"\n  [{self.name}] Starting: {task_name}")
        print(f"            Action: {action.value}, Cost: {atp_cost} ATP")

        try:
            result, reputation = await self.workflow.execute_action_with_reporting(
                action=action,
                resource=resource,
                atp_cost=atp_cost,
                executor_fn=executor_fn,
                context={
                    "delegation_id": f"deleg:supervisor:{self.role}",
                    "task_name": task_name
                }
            )

            self.action_log.append({
                "task": task_name,
                "action": action.value,
                "status": "success",
                "result": result,
                "reputation": {
                    "t3": reputation.t3_score,
                    "v3": reputation.v3_score
                }
            })

            print(f"  [{self.name}] ✅ Success: {task_name}")
            print(f"            T3: {reputation.t3_score:.3f}, V3: {reputation.v3_score:.3f}")

            return {
                "status": "success",
                "result": result,
                "reputation": reputation
            }

        except Exception as e:
            print(f"  [{self.name}] ❌ Failed: {task_name} - {e}")

            self.action_log.append({
                "task": task_name,
                "action": action.value,
                "status": "failed",
                "error": str(e)
            })

            return {
                "status": "failed",
                "error": str(e)
            }


class DataAnalysisAgent(Agent):
    """Agent specialized in data analysis"""

    async def analyze_dataset(self, dataset_id: str, atp_budget: int):
        """Analyze a dataset"""

        async def analysis_work(auth_result):
            print(f"            🔬 Analyzing dataset: {dataset_id}")
            await asyncio.sleep(1.0)  # Simulate analysis
            return {
                "dataset": dataset_id,
                "insights": [
                    "Trend: increasing over time",
                    "Outliers detected: 3",
                    "Correlation coefficient: 0.78"
                ],
                "confidence": 0.89
            }

        return await self.execute_task(
            task_name=f"Analyze dataset {dataset_id}",
            action=Action.COMPUTE,
            resource=f"dataset:{dataset_id}",
            atp_cost=atp_budget,
            executor_fn=analysis_work
        )

    async def query_data(self, query: str, atp_budget: int):
        """Query existing data"""

        async def query_work(auth_result):
            print(f"            🔎 Executing query: {query[:50]}...")
            await asyncio.sleep(0.5)
            return {
                "query": query,
                "rows": 1247,
                "columns": ["id", "timestamp", "value", "category"]
            }

        return await self.execute_task(
            task_name="Query data",
            action=Action.QUERY,
            resource="database:research",
            atp_cost=atp_budget,
            executor_fn=query_work
        )


class ReportWritingAgent(Agent):
    """Agent specialized in report writing"""

    async def write_report(self, analysis_results: List[Dict], atp_budget: int):
        """Write analysis report"""

        async def writing_work(auth_result):
            print(f"            ✍️  Writing report from {len(analysis_results)} analyses")
            await asyncio.sleep(0.8)
            return {
                "report_id": "report_001",
                "title": "Multi-Dataset Analysis Report",
                "sections": 5,
                "pages": 12,
                "analyses_included": len(analysis_results)
            }

        return await self.execute_task(
            task_name="Write analysis report",
            action=Action.WRITE,
            resource="doc:report:multi_analysis",
            atp_cost=atp_budget,
            executor_fn=writing_work
        )

    async def format_summary(self, content: Dict, atp_budget: int):
        """Format executive summary"""

        async def formatting_work(auth_result):
            print(f"            📄 Formatting executive summary")
            await asyncio.sleep(0.3)
            return {
                "summary_id": "summary_001",
                "format": "markdown",
                "length": "2 pages"
            }

        return await self.execute_task(
            task_name="Format summary",
            action=Action.WRITE,
            resource="doc:summary:executive",
            atp_cost=atp_budget,
            executor_fn=formatting_work
        )


async def main():
    """
    Main coordination workflow.
    """

    print("\n" + "="*70)
    print("  Multi-Agent Coordination Example - Web4 SDK")
    print("="*70 + "\n")

    # Service URLs (would come from config in production)
    services = {
        'identity': 'http://localhost:8001',
        'auth': 'http://localhost:8003',
        'reputation': 'http://localhost:8004',
        'resources': 'http://localhost:8005',
        'knowledge': 'http://localhost:8006',
        'governance': 'http://localhost:8002'
    }

    # =========================================================================
    # Step 1: Initialize Agents
    # =========================================================================

    print("🤖 Initializing agent team...\n")

    # In production, keys would be loaded from secure storage
    analyst_key = bytes(32)  # Dummy key
    writer_key = bytes(32)   # Dummy key

    analyst = DataAnalysisAgent(
        name="Data Analyst",
        lct_id="lct:web4:ai:research_lab:analyst_001",
        private_key=analyst_key,
        role="data_analyst",
        services=services
    )

    writer = ReportWritingAgent(
        name="Report Writer",
        lct_id="lct:web4:ai:research_lab:writer_001",
        private_key=writer_key,
        role="report_writer",
        services=services
    )

    agents = [analyst, writer]

    async with analyst, writer:

        # =====================================================================
        # Step 2: Check Agent Status
        # =====================================================================

        print("─" * 70)
        print("Agent Status Check")
        print("─" * 70)

        statuses = await asyncio.gather(*[agent.get_status() for agent in agents])

        for status in statuses:
            print(f"\n  {status['name']}:")
            print(f"    LCT: {status['lct_id']}")
            print(f"    Role: {status['role']}")
            if status['available']:
                print(f"    T3: {status['t3_score']:.3f}, V3: {status['v3_score']:.3f}")
                print(f"    Actions: {status['actions']}")
                print(f"    Status: ✅ Available")
            else:
                print(f"    Status: ⚠️  Unavailable - {status.get('error', 'Unknown')}")

        # =====================================================================
        # Step 3: Coordinate Multi-Step Research Task
        # =====================================================================

        print("\n" + "="*70)
        print("  Coordinated Research Task")
        print("="*70)
        print("\nTask: Analyze multiple datasets and create comprehensive report\n")

        # Phase 1: Data analysis by analyst agent
        print("─" * 70)
        print("Phase 1: Data Analysis")
        print("─" * 70)

        datasets = ["sensor_data_2024", "user_behavior_logs", "performance_metrics"]
        analysis_results = []

        for dataset in datasets:
            result = await analyst.analyze_dataset(
                dataset_id=dataset,
                atp_budget=300
            )
            if result['status'] == 'success':
                analysis_results.append(result['result'])

        print(f"\n  📊 Completed {len(analysis_results)}/{len(datasets)} analyses")

        # Phase 2: Query additional data
        print("\n" + "─" * 70)
        print("Phase 2: Additional Data Queries")
        print("─" * 70)

        query_result = await analyst.query_data(
            query="SELECT * FROM historical_data WHERE date > '2024-01-01'",
            atp_budget=100
        )

        if query_result['status'] == 'success':
            analysis_results.append(query_result['result'])

        # Phase 3: Report writing by writer agent
        print("\n" + "─" * 70)
        print("Phase 3: Report Generation")
        print("─" * 70)

        report_result = await writer.write_report(
            analysis_results=analysis_results,
            atp_budget=200
        )

        # Phase 4: Summary formatting
        print("\n" + "─" * 70)
        print("Phase 4: Executive Summary")
        print("─" * 70)

        if report_result['status'] == 'success':
            summary_result = await writer.format_summary(
                content=report_result['result'],
                atp_budget=100
            )

        # =====================================================================
        # Step 4: Team Performance Summary
        # =====================================================================

        print("\n" + "="*70)
        print("  Team Performance Summary")
        print("="*70 + "\n")

        for agent in agents:
            print(f"  {agent.name}:")
            print(f"    Total tasks: {len(agent.action_log)}")

            successful = sum(1 for log in agent.action_log if log['status'] == 'success')
            failed = sum(1 for log in agent.action_log if log['status'] == 'failed')

            print(f"    Successful: {successful}")
            print(f"    Failed: {failed}")

            if agent.action_log and agent.action_log[-1]['status'] == 'success':
                final_rep = agent.action_log[-1]['reputation']
                print(f"    Final T3: {final_rep['t3']:.3f}")
                print(f"    Final V3: {final_rep['v3']:.3f}")

            print()

        # =====================================================================
        # Step 5: Collaboration Network Query
        # =====================================================================

        print("="*70)
        print("  Collaboration Network")
        print("="*70 + "\n")

        try:
            # Query knowledge graph for collaboration patterns
            for agent in agents:
                trust_network = await agent.client.get_trust_propagation(
                    start_entity=agent.lct_id,
                    max_depth=2
                )

                print(f"  {agent.name}:")
                print(f"    Direct connections: {len(trust_network.get('direct', []))}")
                print(f"    Extended network: {len(trust_network.get('extended', []))}")
                print()

        except Exception as e:
            print(f"  ⚠️  Network query failed: {e}")
            print("     (Expected if services not running)")

        # =====================================================================
        # Step 6: ATP Budget Analysis
        # =====================================================================

        print("="*70)
        print("  ATP Budget Analysis")
        print("="*70 + "\n")

        total_atp = 0
        for agent in agents:
            agent_atp = sum(
                300 if 'analyze' in log['task'].lower() else
                200 if 'write' in log['task'].lower() else
                100
                for log in agent.action_log
                if log['status'] == 'success'
            )
            total_atp += agent_atp
            print(f"  {agent.name}: {agent_atp} ATP")

        print(f"\n  Total ATP consumed: {total_atp}")
        print(f"  Average per agent: {total_atp / len(agents):.0f}")

        # =====================================================================
        # Final Summary
        # =====================================================================

        print("\n" + "="*70)
        print("  Workflow Complete")
        print("="*70 + "\n")

        total_tasks = sum(len(agent.action_log) for agent in agents)
        total_success = sum(
            sum(1 for log in agent.action_log if log['status'] == 'success')
            for agent in agents
        )

        print(f"  ✅ Multi-agent coordination successful")
        print(f"     Total tasks executed: {total_tasks}")
        print(f"     Success rate: {total_success}/{total_tasks} ({100*total_success/total_tasks:.0f}%)")
        print(f"     Agents participated: {len(agents)}")
        print(f"     Total ATP consumed: {total_atp}")

        print("\n  🎯 Deliverables:")
        print(f"     • {len(analysis_results)} dataset analyses")
        print(f"     • 1 comprehensive report")
        print(f"     • 1 executive summary")

        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
