# Web4 REST API Services

Research prototype REST API servers for Web4 infrastructure.

## Overview

This directory contains FastAPI-based REST API servers for Web4 microservices:

- **Identity Service** (port 8001): LCT Registry - identity management
- **Governance Service** (port 8002): Law Oracle and governance procedures
- **Authorization Service** (port 8003): Action authorization and law compliance
- **Reputation Service** (port 8004): T3/V3 reputation tracking
- **Resources Service** (port 8005): ATP allocation and metering
- **Knowledge Service** (port 8006): MRH graph and SPARQL queries

## Status

### ✅ All Services Implemented (Sessions 08-10)

1. **Identity Service** (`identity_service.py`) - Session 08
   - LCT minting with Ed25519 keypairs
   - LCT lookup and verification
   - Signature verification
   - Birth certificate retrieval
   - Health/readiness checks
   - Prometheus metrics

2. **Governance Service** (`governance_service.py`) - Session 09
   - Law version queries
   - Compliance checking
   - Governance procedures
   - Law history
   - Health/readiness checks
   - Prometheus metrics

3. **Authorization Service** (`authorization_service.py`) - Session 08
   - Action authorization with law enforcement
   - Request authentication (Bearer + signature + nonce)
   - Delegation lookup and validation
   - ATP budget tracking
   - Health/readiness checks
   - Prometheus metrics

4. **Reputation Service** (`reputation_service.py`) - Session 09
   - T3/V3 reputation computation
   - Outcome recording
   - Gaming detection
   - Reputation history
   - Leaderboards
   - Health/readiness checks
   - Prometheus metrics

5. **Resources Service** (`resources_service.py`) - Session 09
   - ATP-based resource allocation
   - Usage metering and reporting
   - Resource pool management
   - Refund calculation
   - Health/readiness checks
   - Prometheus metrics

6. **Knowledge Service** (`knowledge_service.py`) - Session 10
   - RDF triple storage
   - SPARQL query execution
   - Trust propagation (MRH-based)
   - Graph traversal
   - Relationship queries
   - Health/readiness checks
   - Prometheus metrics

## Installation

### Requirements

```bash
pip install fastapi uvicorn pydantic prometheus-client
```

### Optional (for development)

```bash
pip install httpx pytest pytest-asyncio
```

## Running Services

### Quick Start - All Services (Docker Compose)

The easiest way to run all services:

```bash
cd implementation/services
docker-compose up -d
```

This starts all 6 services plus Prometheus and Grafana for monitoring.

### Quick Start - Individual Services

```bash
cd implementation/services

# Terminal 1: Identity Service
python identity_service.py

# Terminal 2: Governance Service
python governance_service.py

# Terminal 3: Authorization Service
python authorization_service.py

# Terminal 4: Reputation Service
python reputation_service.py

# Terminal 5: Resources Service
python resources_service.py

# Terminal 6: Knowledge Service
python knowledge_service.py
```

### Individual Services Configuration

**Identity Service** (port 8001):
```bash
python identity_service.py
# or with environment variables:
WEB4_IDENTITY_PORT=8001 WEB4_IDENTITY_DEBUG=true python identity_service.py
```

**Governance Service** (port 8002):
```bash
python governance_service.py
# or with environment variables:
WEB4_GOVERNANCE_PORT=8002 python governance_service.py
```

**Authorization Service** (port 8003):
```bash
python authorization_service.py
# or with environment variables:
WEB4_AUTH_PORT=8003 python authorization_service.py
```

**Reputation Service** (port 8004):
```bash
python reputation_service.py
# or with environment variables:
WEB4_REPUTATION_PORT=8004 python reputation_service.py
```

**Resources Service** (port 8005):
```bash
python resources_service.py
# or with environment variables:
WEB4_RESOURCES_PORT=8005 python resources_service.py
```

**Knowledge Service** (port 8006):
```bash
python knowledge_service.py
# or with environment variables:
WEB4_KNOWLEDGE_PORT=8006 python knowledge_service.py
```

### Service URLs

Once running, all services expose the same endpoints:

- **Identity Service**: http://localhost:8001
  - Docs: http://localhost:8001/docs
  - Health: http://localhost:8001/health
  - Metrics: http://localhost:8001/metrics

- **Governance Service**: http://localhost:8002
  - Docs: http://localhost:8002/docs
  - Health: http://localhost:8002/health
  - Metrics: http://localhost:8002/metrics

- **Authorization Service**: http://localhost:8003
  - Docs: http://localhost:8003/docs
  - Health: http://localhost:8003/health
  - Metrics: http://localhost:8003/metrics

- **Reputation Service**: http://localhost:8004
  - Docs: http://localhost:8004/docs
  - Health: http://localhost:8004/health
  - Metrics: http://localhost:8004/metrics

- **Resources Service**: http://localhost:8005
  - Docs: http://localhost:8005/docs
  - Health: http://localhost:8005/health
  - Metrics: http://localhost:8005/metrics

- **Knowledge Service**: http://localhost:8006
  - Docs: http://localhost:8006/docs
  - Health: http://localhost:8006/health
  - Metrics: http://localhost:8006/metrics

### Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## API Usage

### Identity Service Examples

**Mint a new LCT**:
```bash
curl -X POST http://localhost:8001/v1/lct/mint \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "ai",
    "entity_identifier": "research_agent_001",
    "society": "ai_research_lab",
    "witnesses": ["witness:hr_dept"]
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "lct_id": "lct:web4:ai:ai_research_lab:abc123",
    "public_key": "1234abcd...",
    "private_key": "5678efgh...",
    "birth_certificate": {
      "certificate_hash": "sha256:...",
      "witnesses": ["witness:hr_dept"],
      "creation_time": "2025-11-09T..."
    },
    "status": "active"
  }
}
```

**Get LCT information**:
```bash
curl http://localhost:8001/v1/lct/lct:web4:ai:ai_research_lab:abc123
```

**Verify signature**:
```bash
curl -X POST http://localhost:8001/v1/lct/{lct_id}/verify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "48656c6c6f",
    "signature": "abcd1234..."
  }'
```

### Authorization Service Examples

**Authorize an action**:
```bash
curl -X POST http://localhost:8003/v1/auth/authorize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lct:web4:ai:society:001" \
  -H "X-Signature: abc123..." \
  -H "X-Nonce: 1699564800" \
  -d '{
    "action": "compute",
    "resource": "model:training",
    "atp_cost": 500,
    "context": {
      "delegation_id": "deleg:001"
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "decision": "granted",
    "atp_remaining": 4500,
    "resource_allocation": {
      "cpu_cores": 2.0,
      "memory_gb": 8.0
    }
  },
  "metadata": {
    "law_version": "v1.0.0",
    "law_hash": "sha256:...",
    "timestamp": "2025-11-09T..."
  }
}
```

**Get delegation details**:
```bash
curl http://localhost:8003/v1/delegation/deleg:001 \
  -H "Authorization: Bearer lct:web4:ai:society:001" \
  -H "X-Signature: abc123..." \
  -H "X-Nonce: 1699564801"
```

### Reputation Service Examples

**Record action outcome**:
```bash
curl -X POST http://localhost:8004/v1/reputation/record \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "lct:web4:ai:society:001",
    "role": "researcher",
    "action": "compute",
    "outcome": "exceptional_quality",
    "witnesses": ["human:supervisor:alice"],
    "context": {"task_id": "task_001"}
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "entity_id": "lct:web4:ai:society:001",
    "role": "researcher",
    "t3_score": 0.55,
    "v3_score": 0.62,
    "t3_delta": 0.05,
    "v3_delta": 0.12,
    "gaming_risk": "low"
  }
}
```

**Get reputation scores**:
```bash
curl "http://localhost:8004/v1/reputation/lct:web4:ai:society:001?role=researcher"
```

### Resources Service Examples

**Allocate CPU resources**:
```bash
curl -X POST http://localhost:8005/v1/resources/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "lct:web4:ai:society:001",
    "resource_type": "cpu",
    "amount": 4.0,
    "duration_seconds": 3600
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "allocation_id": "alloc:abc123...",
    "amount_allocated": 4.0,
    "atp_cost": 40,
    "status": "active"
  }
}
```

**Get resource pool status**:
```bash
curl http://localhost:8005/v1/resources/pools
```

### Knowledge Service Examples

**Add RDF triple**:
```bash
curl -X POST http://localhost:8006/v1/graph/triple \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "lct:web4:ai:society:001",
    "predicate": "has_role",
    "object": "researcher",
    "metadata": {"confidence": 1.0}
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "triple_id": "triple:abc123...",
    "subject": "lct:web4:ai:society:001",
    "predicate": "has_role",
    "object": "researcher",
    "timestamp": "2025-11-10T..."
  }
}
```

**Execute SPARQL query**:
```bash
curl -X POST http://localhost:8006/v1/graph/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT ?predicate ?object WHERE { <lct:web4:ai:society:001> ?predicate ?object . }",
    "limit": 100
  }'
```

**Get entity relationships**:
```bash
curl http://localhost:8006/v1/graph/relationships/lct:web4:ai:society:001
```

**Traverse graph**:
```bash
curl -X POST http://localhost:8006/v1/graph/traverse \
  -H "Content-Type: application/json" \
  -d '{
    "start_entity": "lct:web4:ai:society:001",
    "max_depth": 2,
    "direction": "outgoing"
  }'
```

### Governance Service Examples

**Get current law**:
```bash
curl http://localhost:8002/v1/law/current
```

**Check compliance**:
```bash
curl -X POST http://localhost:8002/v1/law/check \
  -H "Content-Type: application/json" \
  -d '{
    "action": "compute",
    "resource": "cpu:high_performance",
    "context": {"entity_type": "ai", "society": "research_lab"}
  }'
```

## Using with Web4 SDK

The services are designed to work with the Web4 Python SDK from Session 07:

```python
from web4_sdk import Web4Client, Action

client = Web4Client(
    identity_url="http://localhost:8001",
    auth_url="http://localhost:8003",
    lct_id="lct:web4:ai:society:001",
    private_key=your_private_key
)

async with client:
    # Mint LCT
    lct_info = await client.get_lct_info()

    # Authorize action
    result = await client.authorize(
        action=Action.COMPUTE,
        resource="model:training",
        atp_cost=500
    )

    print(f"Decision: {result.decision}")
    print(f"ATP remaining: {result.atp_remaining}")
```

## Configuration

### Environment Variables

All services follow the same configuration pattern:

**Identity Service** (port 8001):
- `WEB4_IDENTITY_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_IDENTITY_PORT`: Port to listen (default: 8001)
- `WEB4_IDENTITY_WORKERS`: Number of workers (default: 1)
- `WEB4_IDENTITY_DEBUG`: Debug mode (default: false)

**Governance Service** (port 8002):
- `WEB4_GOVERNANCE_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_GOVERNANCE_PORT`: Port to listen (default: 8002)
- `WEB4_GOVERNANCE_WORKERS`: Number of workers (default: 1)
- `WEB4_GOVERNANCE_DEBUG`: Debug mode (default: false)

**Authorization Service** (port 8003):
- `WEB4_AUTH_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_AUTH_PORT`: Port to listen (default: 8003)
- `WEB4_AUTH_WORKERS`: Number of workers (default: 1)
- `WEB4_AUTH_DEBUG`: Debug mode (default: false)

**Reputation Service** (port 8004):
- `WEB4_REPUTATION_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_REPUTATION_PORT`: Port to listen (default: 8004)
- `WEB4_REPUTATION_WORKERS`: Number of workers (default: 1)
- `WEB4_REPUTATION_DEBUG`: Debug mode (default: false)

**Resources Service** (port 8005):
- `WEB4_RESOURCES_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_RESOURCES_PORT`: Port to listen (default: 8005)
- `WEB4_RESOURCES_WORKERS`: Number of workers (default: 1)
- `WEB4_RESOURCES_DEBUG`: Debug mode (default: false)

**Knowledge Service** (port 8006):
- `WEB4_KNOWLEDGE_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_KNOWLEDGE_PORT`: Port to listen (default: 8006)
- `WEB4_KNOWLEDGE_WORKERS`: Number of workers (default: 1)
- `WEB4_KNOWLEDGE_DEBUG`: Debug mode (default: false)

## Monitoring

### Health Checks

All services expose health check endpoints:

```bash
# Health check (liveness probe)
curl http://localhost:8001/health

# Readiness check
curl http://localhost:8001/ready
```

### Prometheus Metrics

Metrics are exposed at `/metrics` endpoint:

```bash
curl http://localhost:8001/metrics
```

**Identity Service Metrics**:
- `web4_identity_lct_minted_total`: Total LCTs minted (by entity_type, society)
- `web4_identity_lct_lookup_total`: Total LCT lookups (by found status)
- `web4_identity_signature_verify_total`: Total signature verifications (by valid status)
- `web4_identity_request_duration_seconds`: Request duration histogram

**Governance Service Metrics**:
- `web4_governance_law_queries_total`: Total law queries (by version, query_type)
- `web4_governance_compliance_checks_total`: Total compliance checks (by compliant)
- `web4_governance_current_law_version`: Current law version gauge

**Authorization Service Metrics**:
- `web4_auth_requests_total`: Total authorization requests (by decision, action)
- `web4_auth_latency_seconds`: Authorization latency histogram
- `web4_auth_atp_budget_remaining`: ATP budget remaining gauge

**Reputation Service Metrics**:
- `web4_reputation_updates_total`: Total reputation updates (by entity_type, role, outcome)
- `web4_reputation_t3_score`: T3 (trustworthiness) score gauge (by entity, role)
- `web4_reputation_v3_score`: V3 (value creation) score gauge (by entity, role)
- `web4_reputation_gaming_detected_total`: Gaming detection events (by entity, severity)

**Resources Service Metrics**:
- `web4_resources_allocations_total`: Total resource allocations (by resource_type, entity_type)
- `web4_resources_pool_utilization`: Resource pool utilization gauge (by resource_type)
- `web4_resources_atp_consumed_total`: Total ATP consumed (by resource_type)

**Knowledge Service Metrics**:
- `web4_knowledge_triples_total`: Total RDF triples added (by predicate_type)
- `web4_knowledge_graph_size`: Current graph size gauge
- `web4_knowledge_sparql_queries_total`: Total SPARQL queries (by query_type)
- `web4_knowledge_query_duration_seconds`: Query duration histogram
- `web4_knowledge_trust_propagation_total`: Trust propagation computations

### Grafana Dashboards

Metrics can be scraped by Prometheus and visualized in Grafana. See `../DEPLOYMENT_ARCHITECTURE.md` for complete monitoring setup.

## Development

### Adding New Endpoints

1. Add Pydantic models for request/response
2. Implement endpoint function with FastAPI decorator
3. Add authentication if required
4. Update metrics
5. Add tests
6. Update this README

Example:
```python
from pydantic import BaseModel
from fastapi import Depends

class MyRequest(BaseModel):
    param: str

@app.post("/v1/my-endpoint")
async def my_endpoint(
    req: MyRequest,
    lct_id: str = Depends(authenticate_request)
):
    # Implementation
    return {"success": True, "data": {...}}
```

### Testing

Run tests with pytest:

```bash
pip install pytest pytest-asyncio httpx

# Test all services
pytest tests/

# Test specific service
pytest tests/test_identity_service.py
```

Example test:
```python
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_mint_lct():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/v1/lct/mint", json={
            "entity_type": "ai",
            "entity_identifier": "test_agent",
            "witnesses": []
        })

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "lct_id" in data["data"]
```

## Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t web4-identity:latest -f Dockerfile.identity .

# Run container
docker run -p 8001:8001 \
  -e WEB4_IDENTITY_HOST=0.0.0.0 \
  -e WEB4_IDENTITY_PORT=8001 \
  web4-identity:latest
```

### Kubernetes

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/identity-deployment.yaml
kubectl apply -f k8s/identity-service.yaml
```

See `../DEPLOYMENT_ARCHITECTURE.md` for complete Kubernetes setup.

### Docker Compose

Run all services with Docker Compose:

```bash
docker-compose up -d
```

See `docker-compose.yml` in root directory.

## Security

### Authentication

All endpoints (except `/health`, `/ready`, `/metrics`) require authentication:

1. **Bearer Token**: LCT ID in `Authorization` header
2. **Signature**: Ed25519 signature in `X-Signature` header
3. **Nonce**: Monotonic nonce in `X-Nonce` header

Signature format:
```
payload = f"{method}|{path}|{nonce}|{json_body}"
signature = ed25519_sign(payload, private_key)
```

### TLS

In production, always use TLS:

```bash
uvicorn identity_service:app \
  --host 0.0.0.0 \
  --port 8001 \
  --ssl-keyfile /path/to/key.pem \
  --ssl-certfile /path/to/cert.pem
```

Or use reverse proxy (nginx, Traefik) for TLS termination.

### Rate Limiting

TODO: Implement rate limiting per LCT:
- 100 requests/minute for standard users
- 1000 requests/minute for verified users
- Exponential backoff on violations

## Troubleshooting

### Service Won't Start

```bash
# Check port availability
lsof -i :8001

# Check logs
python identity_service.py 2>&1 | tee service.log

# Enable debug mode
WEB4_IDENTITY_DEBUG=true python identity_service.py
```

### Connection Refused

```bash
# Check service is running
curl http://localhost:8001/health

# Check firewall
sudo ufw status
sudo ufw allow 8001/tcp

# Check network
netstat -tlnp | grep 8001
```

### Authentication Errors

```bash
# Verify LCT ID format
echo "lct:web4:ai:society:001" | grep -E "^lct:web4:[a-z]+:[a-z_]+:[a-z0-9]+"

# Check signature generation
# Use Web4 SDK for correct signature format

# Verify nonce is monotonic
# Each request must have higher nonce than previous
```

## API Reference

Complete API documentation is available at the `/docs` endpoint for each service:

- **Identity Service**: http://localhost:8001/docs (OpenAPI: http://localhost:8001/openapi.json)
- **Governance Service**: http://localhost:8002/docs (OpenAPI: http://localhost:8002/openapi.json)
- **Authorization Service**: http://localhost:8003/docs (OpenAPI: http://localhost:8003/openapi.json)
- **Reputation Service**: http://localhost:8004/docs (OpenAPI: http://localhost:8004/openapi.json)
- **Resources Service**: http://localhost:8005/docs (OpenAPI: http://localhost:8005/openapi.json)
- **Knowledge Service**: http://localhost:8006/docs (OpenAPI: http://localhost:8006/openapi.json)

All services provide interactive API documentation powered by FastAPI's Swagger UI.

## Contributing

When adding new endpoints or services:

1. Follow the established pattern from existing services (all 6 services use the same structure)
2. Use FastAPI with async/await for all endpoints
3. Define Pydantic models for request/response validation
4. Implement standard endpoints: `/health`, `/ready`, `/metrics`
5. Add authentication where required (Bearer + signature + nonce)
6. Add Prometheus metrics (Counter, Gauge, Histogram as appropriate)
7. Write comprehensive tests
8. Update this README with examples
9. Update docker-compose.yml if adding a new service
10. Update prometheus.yml for metrics scraping

The 6 existing services provide excellent templates for any new service development.

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: See `../DEPLOYMENT_ARCHITECTURE.md` for infrastructure
- **SDK**: See `../sdk/README.md` for client library
- **Issues**: Report bugs at GitHub repository
- **Community**: Join Web4 community discussions

---

**Web4 Services**: Research prototype REST APIs for trust-native coordination.

**Status**: All 6 core services implemented and ready for deployment (Sessions 08-10).

## Test Suite

A comprehensive test script is available to validate all services:

```bash
# Install test dependencies
pip install httpx

# Run complete test suite
python test_all_services.py
```

The test script validates:
- Health checks for all 6 services
- Identity: LCT minting and lookup
- Governance: Law queries and compliance
- Authorization: Action authorization
- Reputation: Outcome recording and T3/V3 scores
- Resources: ATP allocation and metering
- Knowledge: Graph operations and SPARQL queries

**Total Test Coverage**: 25+ integration tests across all microservices.
