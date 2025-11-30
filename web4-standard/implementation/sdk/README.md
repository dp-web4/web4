# Web4 Python SDK

Research prototype Python SDK for building applications on Web4 infrastructure.

## Overview

The Web4 SDK provides high-level abstractions for interacting with Web4 services:

- **Identity Management**: LCT-based cryptographic identity
- **Authorization**: Request and verify permissions
- **Reputation Tracking**: Build trust through verified actions
- **Resource Allocation**: Manage ATP budgets and resource usage
- **Knowledge Graphs**: Query trust networks and relationships
- **Governance**: Check law compliance and norms

## Installation

### Requirements

```bash
pip install aiohttp pynacl
```

### From Source

```bash
cd web4-standard/implementation/sdk
pip install -e .
```

## Quick Start

### Basic Usage

```python
import asyncio
from web4_sdk import Web4Client, Action

async def main():
    # Initialize client
    client = Web4Client(
        identity_url="http://localhost:8001",
        auth_url="http://localhost:8003",
        lct_id="lct:web4:ai:society:001",
        private_key=your_private_key_bytes
    )

    async with client:
        # Request authorization
        result = await client.authorize(
            action=Action.COMPUTE,
            resource="model:training",
            atp_cost=500
        )

        if result.decision == "granted":
            print(f"✅ Authorized! ATP remaining: {result.atp_remaining}")

            # Execute your action here
            ...

            # Report outcome
            reputation = await client.report_outcome(
                action=Action.COMPUTE,
                outcome=OutcomeType.SUCCESS,
                quality_score=0.85
            )

            print(f"📊 Reputation: T3={reputation.t3_score:.3f}, V3={reputation.v3_score:.3f}")

asyncio.run(main())
```

### Environment-Based Configuration

```python
import os
from web4_sdk import create_client_from_env

# Set environment variables:
# WEB4_IDENTITY_URL=http://localhost:8001
# WEB4_AUTH_URL=http://localhost:8003
# WEB4_LCT_ID=lct:web4:ai:society:001
# WEB4_PRIVATE_KEY=<hex_encoded_key>

client = create_client_from_env()
```

## Core Concepts

### Actions

Standard Web4 actions:

```python
from web4_sdk import Action

Action.READ       # Read data
Action.WRITE      # Write data
Action.COMPUTE    # Execute computation
Action.QUERY      # Query databases
Action.DELEGATE   # Delegate authority
Action.ALLOCATE   # Allocate resources
```

### Outcomes

Report action outcomes to build reputation:

```python
from web4_sdk import OutcomeType

OutcomeType.SUCCESS              # Standard success
OutcomeType.EXCEPTIONAL_QUALITY  # High-quality result
OutcomeType.PARTIAL_SUCCESS      # Partial completion
OutcomeType.FAILURE              # Task failed
OutcomeType.POOR_QUALITY         # Low-quality result
```

### Resources

Allocate specific resource types:

```python
from web4_sdk import ResourceType

ResourceType.CPU      # CPU cycles
ResourceType.MEMORY   # RAM
ResourceType.STORAGE  # Disk space
ResourceType.NETWORK  # Bandwidth
```

## API Reference

### Web4Client

Main client for Web4 services.

#### Identity Methods

```python
# Get LCT information
lct_info = await client.get_lct_info(lct_id="lct:web4:...")

# Verify signature from another entity
is_valid = await client.verify_lct_signature(
    lct_id="lct:web4:...",
    message=message_bytes,
    signature=signature_bytes
)
```

#### Authorization Methods

```python
# Request authorization
result = await client.authorize(
    action=Action.COMPUTE,
    resource="model:training",
    atp_cost=500,
    context={"delegation_id": "deleg:001"}
)

# Check delegation
delegation = await client.check_delegation("deleg:001")
```

#### Reputation Methods

```python
# Get reputation scores
reputation = await client.get_reputation(
    entity_id="lct:web4:...",  # Optional, defaults to self
    role="researcher"           # Optional role filter
)

# Report action outcome
updated_rep = await client.report_outcome(
    action=Action.COMPUTE,
    outcome=OutcomeType.SUCCESS,
    quality_score=0.85,
    witnesses=["lct:web4:human:..."],
    context={"task_id": "task_001"}
)
```

#### Resource Methods

```python
# Allocate resources
allocation = await client.allocate_resources(
    resource_type=ResourceType.CPU,
    amount=4.0,  # 4 CPU cores
    duration_seconds=3600
)

# Report actual usage
usage_report = await client.report_resource_usage(
    allocation_id=allocation.allocation_id,
    actual_usage=3.5  # Actually used 3.5 cores
)
```

#### Knowledge Graph Methods

```python
# Execute SPARQL query
results = await client.query_knowledge_graph(
    sparql_query="""
        SELECT ?action ?timestamp WHERE {
            <lct:web4:ai:...> performed ?action .
            ?action timestamp ?timestamp .
        }
        ORDER BY DESC(?timestamp)
        LIMIT 10
    """
)

# Get trust propagation
trust_network = await client.get_trust_propagation(
    start_entity="lct:web4:...",
    max_depth=3
)
```

#### Governance Methods

```python
# Get current law version
law_info = await client.get_law_version()

# Check if action is legal
is_legal = await client.check_action_legal(
    action=Action.COMPUTE,
    entity_type="ai",
    role="researcher"
)
```

### Web4Workflow

High-level workflow helpers.

```python
from web4_sdk import Web4Workflow

workflow = Web4Workflow(client)

# Complete workflow: authorize -> execute -> report
async def my_computation(auth_result):
    # Your computation logic
    return {"result": 42}

result, reputation = await workflow.execute_action_with_reporting(
    action=Action.COMPUTE,
    resource="model:training",
    atp_cost=500,
    executor_fn=my_computation,
    context={"delegation_id": "deleg:001"}
)

# Health check all services
health = await workflow.health_check()
for service, status in health.items():
    print(f"{service}: {'UP' if status else 'DOWN'}")
```

## Examples

### Example 1: AI Agent Workflow

Complete workflow for an AI research agent:

```bash
python examples/ai_agent_workflow.py
```

Features demonstrated:
- Agent initialization
- Status checking (LCT, reputation, law)
- Multiple authorized actions
- Outcome reporting
- Knowledge graph queries
- Service health checks

### Example 2: Multi-Agent Coordination

Team of specialized agents coordinating on a task:

```bash
python examples/multi_agent_coordination.py
```

Features demonstrated:
- Multiple agent initialization
- Role-based specialization (data analyst, report writer)
- Coordinated multi-phase workflow
- ATP budget tracking
- Team performance analytics
- Collaboration network analysis

## Error Handling

The SDK provides specific exceptions for different error conditions:

```python
from web4_sdk import (
    Web4Error,              # Base exception
    AuthorizationDenied,    # Auth request denied
    InsufficientATP,        # Not enough ATP budget
    InvalidSignature,       # Signature verification failed
    ServiceUnavailable      # Service is down
)

try:
    result = await client.authorize(
        action=Action.COMPUTE,
        resource="expensive_model",
        atp_cost=10000
    )
except InsufficientATP as e:
    print(f"Need more ATP: {e}")
except AuthorizationDenied as e:
    print(f"Permission denied: {e}")
except ServiceUnavailable as e:
    print(f"Service down: {e}")
except Web4Error as e:
    print(f"General error: {e}")
```

## Best Practices

### 1. Use Context Managers

Always use async context managers for automatic cleanup:

```python
async with Web4Client(...) as client:
    # Your code here
    pass
# Client automatically disconnected
```

### 2. Report All Outcomes

Build reputation by reporting outcomes of all actions:

```python
result = await client.authorize(...)
try:
    # Execute action
    data = perform_computation()
    outcome = OutcomeType.SUCCESS
    quality = 0.85
except Exception:
    outcome = OutcomeType.FAILURE
    quality = 0.0

await client.report_outcome(
    action=action,
    outcome=outcome,
    quality_score=quality
)
```

### 3. Handle ATP Budgets

Check remaining ATP and handle exhaustion gracefully:

```python
result = await client.authorize(
    action=Action.COMPUTE,
    resource="model",
    atp_cost=500
)

print(f"ATP remaining: {result.atp_remaining}")

if result.atp_remaining < 100:
    print("⚠️  Running low on ATP!")
```

### 4. Use Workflow Helpers

For common patterns, use Web4Workflow:

```python
workflow = Web4Workflow(client)

result, reputation = await workflow.execute_action_with_reporting(
    action=Action.COMPUTE,
    resource="model",
    atp_cost=500,
    executor_fn=my_function
)
```

### 5. Check Service Health

Periodically check service health:

```python
health = await workflow.health_check()
all_healthy = all(health.values())

if not all_healthy:
    print("⚠️  Some services are down:")
    for service, status in health.items():
        if not status:
            print(f"   - {service}")
```

### 6. Secure Key Management

**Never** hardcode private keys:

```python
# ❌ BAD
client = Web4Client(
    private_key=b"hardcoded_key_here..."
)

# ✅ GOOD
import os
key_hex = os.environ['WEB4_PRIVATE_KEY']
client = Web4Client(
    private_key=bytes.fromhex(key_hex)
)

# ✅ BETTER
client = create_client_from_env()
```

### 7. Implement Retries

For production, implement application-level retries:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def resilient_authorize(...):
    return await client.authorize(...)
```

## Configuration

### Service URLs

Configure Web4 service URLs:

```python
client = Web4Client(
    # Required
    identity_url="http://identity:8001",
    auth_url="http://auth:8003",
    lct_id="lct:web4:ai:society:001",
    private_key=key_bytes,

    # Optional services
    reputation_url="http://reputation:8004",
    resources_url="http://resources:8005",
    knowledge_url="http://knowledge:8006",
    governance_url="http://governance:8002",

    # Timeouts and retries
    timeout=30,
    max_retries=3
)
```

### Environment Variables

For environment-based configuration:

```bash
# Required
export WEB4_IDENTITY_URL=http://localhost:8001
export WEB4_AUTH_URL=http://localhost:8003
export WEB4_LCT_ID=lct:web4:ai:society:001
export WEB4_PRIVATE_KEY=<hex_encoded_32_byte_key>

# Optional
export WEB4_REPUTATION_URL=http://localhost:8004
export WEB4_RESOURCES_URL=http://localhost:8005
export WEB4_KNOWLEDGE_URL=http://localhost:8006
export WEB4_GOVERNANCE_URL=http://localhost:8002
```

Then use `create_client_from_env()`.

## Performance Tips

### 1. Connection Pooling

The SDK uses aiohttp connection pooling automatically. Reuse client instances:

```python
# ✅ GOOD - Reuse client
client = Web4Client(...)
async with client:
    for i in range(100):
        await client.authorize(...)

# ❌ BAD - Creating new client each time
for i in range(100):
    async with Web4Client(...) as client:
        await client.authorize(...)
```

### 2. Parallel Requests

Use asyncio.gather for parallel requests:

```python
# Authorize multiple actions in parallel
results = await asyncio.gather(
    client.authorize(action=Action.READ, resource="data1", atp_cost=100),
    client.authorize(action=Action.READ, resource="data2", atp_cost=100),
    client.authorize(action=Action.READ, resource="data3", atp_cost=100)
)
```

### 3. Batch Operations

Where possible, batch related operations:

```python
# Report multiple outcomes together
outcomes = [
    client.report_outcome(action=Action.COMPUTE, outcome=OutcomeType.SUCCESS),
    client.report_outcome(action=Action.WRITE, outcome=OutcomeType.SUCCESS),
    client.report_outcome(action=Action.READ, outcome=OutcomeType.SUCCESS)
]

results = await asyncio.gather(*outcomes)
```

## Testing

### Unit Tests

```python
import pytest
from web4_sdk import Web4Client, Action

@pytest.mark.asyncio
async def test_authorization():
    client = Web4Client(
        identity_url="http://test:8001",
        auth_url="http://test:8003",
        lct_id="lct:web4:test:001",
        private_key=test_key
    )

    async with client:
        result = await client.authorize(
            action=Action.READ,
            resource="test:resource",
            atp_cost=100
        )

        assert result.decision == "granted"
        assert result.atp_remaining is not None
```

### Integration Tests

See `examples/` directory for complete integration test scenarios.

## Troubleshooting

### Connection Errors

```python
from web4_sdk import ServiceUnavailable

try:
    await client.get_lct_info()
except ServiceUnavailable as e:
    print(f"Service unavailable: {e}")
    # Check service URLs
    # Verify services are running
    # Check network connectivity
```

### Authentication Failures

```python
from web4_sdk import InvalidSignature, AuthorizationDenied

try:
    result = await client.authorize(...)
except InvalidSignature:
    # Check private key is correct
    # Verify LCT ID matches key
    print("Invalid signature - check credentials")
except AuthorizationDenied:
    # Check delegation is valid
    # Verify law allows this action
    # Check ATP budget
    print("Authorization denied - check permissions")
```

### ATP Budget Issues

```python
from web4_sdk import InsufficientATP

try:
    result = await client.authorize(
        action=Action.COMPUTE,
        resource="expensive",
        atp_cost=10000
    )
except InsufficientATP as e:
    print(f"Not enough ATP: {e}")
    # Request smaller ATP cost
    # Wait for budget replenishment
    # Prioritize essential actions
```

## Support

- **Documentation**: See `DEPLOYMENT_ARCHITECTURE.md` for infrastructure details
- **Examples**: Check `examples/` directory for working code
- **Issues**: Report bugs at GitHub repository
- **Community**: Join Web4 community discussions

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## Roadmap

### v1.1 (Planned)

- Synchronous API wrapper
- CLI tool for SDK operations
- Additional workflow helpers
- Performance optimizations
- Enhanced error messages

### v1.2 (Planned)

- WebSocket support for real-time updates
- Event streaming from knowledge graph
- Bulk operation APIs
- Caching layer for repeated queries
- Metrics and observability helpers

### v2.0 (Future)

- TypeScript/JavaScript SDK
- Go SDK
- Rust SDK
- gRPC support
- GraphQL query interface

## Version History

### v1.0.0 (Current)

- Initial release
- Core Web4 service integration
- Async HTTP client
- Cryptographic signing (Ed25519)
- High-level workflow helpers
- Comprehensive examples
- Comprehensive error handling

---

**Web4 SDK**: Build trust-native applications with research prototype tools.
