# Web4 REST API Services

Production-ready REST API servers for Web4 infrastructure.

## Overview

This directory contains FastAPI-based REST API servers for Web4 microservices:

- **Identity Service** (port 8001): LCT Registry - identity management
- **Authorization Service** (port 8003): Action authorization and law compliance
- **Reputation Service** (port 8004): T3/V3 reputation tracking (TODO)
- **Resources Service** (port 8005): ATP allocation and metering (TODO)
- **Knowledge Service** (port 8006): MRH graph and SPARQL queries (TODO)
- **Governance Service** (port 8002): Law Oracle and governance (TODO)

## Status

### ✅ Implemented (Session 08)

1. **Identity Service** (`identity_service.py`)
   - LCT minting
   - LCT lookup
   - Signature verification
   - Birth certificate retrieval
   - Health/readiness checks
   - Prometheus metrics

2. **Authorization Service** (`authorization_service.py`)
   - Action authorization
   - Request authentication
   - Delegation lookup
   - Health/readiness checks
   - Prometheus metrics

### 🚧 TODO (Future Sessions)

3. **Reputation Service** - T3/V3 computation and outcome recording
4. **Resources Service** - ATP allocation and resource metering
5. **Knowledge Service** - SPARQL queries and trust propagation
6. **Governance Service** - Law version and compliance checks

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

### Quick Start - All Services

```bash
# Terminal 1: Identity Service
cd implementation/services
python identity_service.py

# Terminal 2: Authorization Service
python authorization_service.py
```

### Individual Services

**Identity Service** (port 8001):
```bash
python identity_service.py
# or with environment variables:
WEB4_IDENTITY_PORT=8001 python identity_service.py
```

**Authorization Service** (port 8003):
```bash
python authorization_service.py
# or with environment variables:
WEB4_AUTH_PORT=8003 python authorization_service.py
```

### Service URLs

Once running:
- Identity Service: http://localhost:8001
  - Docs: http://localhost:8001/docs
  - Health: http://localhost:8001/health
  - Metrics: http://localhost:8001/metrics

- Authorization Service: http://localhost:8003
  - Docs: http://localhost:8003/docs
  - Health: http://localhost:8003/health
  - Metrics: http://localhost:8003/metrics

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

**Identity Service**:
- `WEB4_IDENTITY_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_IDENTITY_PORT`: Port to listen (default: 8001)
- `WEB4_IDENTITY_WORKERS`: Number of workers (default: 1)
- `WEB4_IDENTITY_DEBUG`: Debug mode (default: false)

**Authorization Service**:
- `WEB4_AUTH_HOST`: Host to bind (default: 0.0.0.0)
- `WEB4_AUTH_PORT`: Port to listen (default: 8003)
- `WEB4_AUTH_WORKERS`: Number of workers (default: 1)
- `WEB4_AUTH_DEBUG`: Debug mode (default: false)

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

**Authorization Service Metrics**:
- `web4_auth_requests_total`: Total authorization requests (by decision, action)
- `web4_auth_latency_seconds`: Authorization latency histogram
- `web4_auth_atp_budget_remaining`: ATP budget remaining gauge

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

Complete API documentation is available at:
- Identity Service: http://localhost:8001/docs
- Authorization Service: http://localhost:8003/docs

Or see OpenAPI specs:
- http://localhost:8001/openapi.json
- http://localhost:8003/openapi.json

## Contributing

When adding new services:

1. Follow the pattern from `identity_service.py` and `authorization_service.py`
2. Use FastAPI and Pydantic models
3. Implement health/ready/metrics endpoints
4. Add authentication where required
5. Add Prometheus metrics
6. Write tests
7. Update this README
8. Submit PR

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: See `../DEPLOYMENT_ARCHITECTURE.md` for infrastructure
- **SDK**: See `../sdk/README.md` for client library
- **Issues**: Report bugs at GitHub repository
- **Community**: Join Web4 community discussions

---

**Web4 Services**: Production-ready REST APIs for trust-native coordination.
