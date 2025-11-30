# Web4 Deployment Architecture

**Status**: Research Prototype Reference Architecture
**Version**: 1.0.0
**Last Updated**: 2025-11-09

This document describes the complete deployment architecture for Web4 infrastructure, including service design, API contracts, deployment configurations, and operational runbooks.

---

## Table of Contents

1. [Service Architecture](#service-architecture)
2. [API Contracts](#api-contracts)
3. [Deployment Configurations](#deployment-configurations)
4. [Monitoring & Observability](#monitoring--observability)
5. [Operational Runbooks](#operational-runbooks)
6. [Security Considerations](#security-considerations)
7. [Scaling Strategy](#scaling-strategy)

---

## Service Architecture

### Overview

Web4 infrastructure is deployed as a collection of microservices, each responsible for a specific aspect of trust-native coordination.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│                 (Authentication, Rate Limiting)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                              ▼                                 ▼
                ┌─────────────────────────┐     ┌──────────────────────────┐
                │   Identity Service      │     │   Governance Service     │
                │   (LCT Registry)        │     │   (Law Oracle)           │
                └─────────────────────────┘     └──────────────────────────┘
                              │                                 │
                              ▼                                 ▼
                ┌─────────────────────────┐     ┌──────────────────────────┐
                │  Authorization Service  │     │  Reputation Service      │
                │  (Auth Engine)          │     │  (Rep Engine)            │
                └─────────────────────────┘     └──────────────────────────┘
                              │                                 │
                              ▼                                 ▼
                ┌─────────────────────────┐     ┌──────────────────────────┐
                │   Resource Service      │     │  Knowledge Service       │
                │   (Resource Allocator)  │     │  (MRH Graph)             │
                └─────────────────────────┘     └──────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────────────────────────────┐
                │                Infrastructure Services                   │
                ├──────────────────┬──────────────────┬───────────────────┤
                │  HSM Service     │  Ledger Service  │  Storage Service  │
                │  (TPM/SE)        │  (Blockchain)    │  (RDF Store)      │
                └──────────────────┴──────────────────┴───────────────────┘
```

### Core Services

#### 1. Identity Service (LCT Registry)

**Responsibilities**:
- LCT minting and lifecycle management
- Birth certificate creation and verification
- Hardware-backed credential management
- Identity chain tracking

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: PostgreSQL (metadata) + Ledger (immutable records)
- Hardware: TPM 2.0 integration
- Port: 8001

**Endpoints**:
```
POST   /v1/lct/mint              - Mint new LCT
GET    /v1/lct/{lct_id}          - Get LCT details
POST   /v1/lct/{lct_id}/suspend  - Suspend LCT
POST   /v1/lct/{lct_id}/revoke   - Revoke LCT
GET    /v1/lct/{lct_id}/verify   - Verify LCT signature
POST   /v1/lct/{lct_id}/transition - Identity transition
```

**Dependencies**: Ledger Service, HSM Service

#### 2. Governance Service (Law Oracle)

**Responsibilities**:
- Law dataset publication and versioning
- Role permission queries
- Action legality verification
- Witness requirement determination

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: PostgreSQL + Ledger
- Cache: Redis (for law datasets)
- Port: 8002

**Endpoints**:
```
POST   /v1/law/publish           - Publish law dataset
GET    /v1/law/version/{version} - Get law dataset
POST   /v1/law/check             - Check action legality
GET    /v1/law/permissions/{role} - Get role permissions
POST   /v1/law/interpretation    - Add interpretation
```

**Dependencies**: Ledger Service

#### 3. Authorization Service (Auth Engine)

**Responsibilities**:
- Runtime authorization decisions
- LCT signature verification
- Delegation management
- ATP budget tracking

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: Redis (for active delegations)
- Port: 8003

**Endpoints**:
```
POST   /v1/auth/authorize        - Authorize action
POST   /v1/auth/delegate         - Create delegation
DELETE /v1/auth/delegate/{id}    - Revoke delegation
GET    /v1/auth/delegation/{id}  - Get delegation status
```

**Dependencies**: Identity Service, Governance Service, Reputation Service

#### 4. Reputation Service (Rep Engine)

**Responsibilities**:
- T3/V3 tensor computation
- Outcome recording and processing
- Reputation queries
- Gaming detection

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: PostgreSQL (reputation data) + Ledger (outcomes)
- Port: 8004

**Endpoints**:
```
POST   /v1/reputation/outcome    - Record outcome
GET    /v1/reputation/{entity}/{role} - Get reputation
POST   /v1/reputation/delta      - Compute delta
GET    /v1/reputation/stats      - Get statistics
```

**Dependencies**: Ledger Service

#### 5. Resource Service (Resource Allocator)

**Responsibilities**:
- ATP to resource conversion
- Resource pool management
- Allocation and metering
- Usage tracking

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: Redis (active allocations)
- Port: 8005

**Endpoints**:
```
POST   /v1/resources/allocate    - Allocate resources
POST   /v1/resources/release     - Release resources
GET    /v1/resources/pool/stats  - Pool statistics
POST   /v1/resources/rates       - Update conversion rates
```

**Dependencies**: None (standalone)

#### 6. Knowledge Service (MRH Graph)

**Responsibilities**:
- RDF triple storage and queries
- Graph traversal and path finding
- Trust propagation
- SPARQL query interface

**Technology Stack**:
- Runtime: Python 3.10+
- Framework: FastAPI
- Storage: Blazegraph or GraphDB (RDF triplestore)
- Port: 8006

**Endpoints**:
```
POST   /v1/graph/triple          - Add triple
GET    /v1/graph/query           - SPARQL query
POST   /v1/graph/traverse        - Traverse from entity
GET    /v1/graph/paths           - Find paths
POST   /v1/graph/trust           - Compute trust propagation
```

**Dependencies**: None (standalone)

### Infrastructure Services

#### HSM Service

**Purpose**: Hardware security module access
**Implementation**: gRPC service wrapping TPM 2.0
**Deployment**: Co-located with services requiring signing

#### Ledger Service

**Purpose**: Blockchain integration
**Implementation**: Cosmos SDK or Ethereum node
**Deployment**: Dedicated cluster with validators

#### Storage Service

**Purpose**: Persistent data storage
**Implementation**: PostgreSQL cluster
**Deployment**: Multi-region with replication

---

## API Contracts

### Common Patterns

All Web4 services follow REST conventions with:

**Authentication**:
```
Authorization: Bearer {LCT_TOKEN}
X-Signature: {Ed25519_SIGNATURE}
X-Nonce: {REQUEST_NONCE}
```

**Response Format**:
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2025-11-09T12:00:00Z",
    "law_hash": "sha256:...",
    "ledger_ref": "cosmos:tx:..."
  }
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_ATP",
    "message": "Budget exhausted",
    "details": { ... }
  }
}
```

### Example: Authorization Request

**Request**:
```http
POST /v1/auth/authorize HTTP/1.1
Host: auth.web4.io
Content-Type: application/json
Authorization: Bearer lct:web4:ai:society:001
X-Signature: {ed25519_signature}
X-Nonce: 12345

{
  "action": "compute",
  "resource": "model:training",
  "atp_cost": 500,
  "context": {
    "delegation_id": "deleg:001"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "decision": "granted",
    "atp_remaining": 4500,
    "requires_witness": false,
    "decision_hash": "sha256:..."
  },
  "metadata": {
    "request_id": "uuid-1234",
    "timestamp": "2025-11-09T12:00:00Z",
    "law_hash": "sha256:abc123...",
    "ledger_ref": "cosmos:tx:def456..."
  }
}
```

---

## Deployment Configurations

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  # API Gateway
  gateway:
    image: web4/gateway:latest
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=info
    depends_on:
      - identity
      - governance
      - authorization

  # Identity Service
  identity:
    image: web4/identity:latest
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres@db/identity
      - LEDGER_URL=http://ledger:26657
      - HSM_TYPE=software
    depends_on:
      - db
      - ledger
    volumes:
      - ./keys:/app/keys

  # Governance Service
  governance:
    image: web4/governance:latest
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://postgres@db/governance
      - LEDGER_URL=http://ledger:26657
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - ledger
      - redis

  # Authorization Service
  authorization:
    image: web4/authorization:latest
    ports:
      - "8003:8003"
    environment:
      - REDIS_URL=redis://redis:6379
      - IDENTITY_SERVICE=http://identity:8001
      - GOVERNANCE_SERVICE=http://governance:8002
    depends_on:
      - redis

  # Reputation Service
  reputation:
    image: web4/reputation:latest
    ports:
      - "8004:8004"
    environment:
      - DATABASE_URL=postgresql://postgres@db/reputation
      - LEDGER_URL=http://ledger:26657
    depends_on:
      - db
      - ledger

  # Resource Service
  resources:
    image: web4/resources:latest
    ports:
      - "8005:8005"
    environment:
      - REDIS_URL=redis://redis:6379

  # Knowledge Service
  knowledge:
    image: web4/knowledge:latest
    ports:
      - "8006:8006"
    environment:
      - TRIPLESTORE_URL=http://blazegraph:9999
    depends_on:
      - blazegraph

  # Infrastructure
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=web4dev
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  ledger:
    image: cosmoshub/gaia:latest
    ports:
      - "26657:26657"
    volumes:
      - ledgerdata:/root/.gaia

  blazegraph:
    image: nawer/blazegraph:latest
    ports:
      - "9999:9999"
    volumes:
      - graphdata:/var/lib/blazegraph

volumes:
  pgdata:
  redisdata:
  ledgerdata:
  graphdata:
```

### Kubernetes (Production)

```yaml
# identity-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web4-identity
  namespace: web4
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web4-identity
  template:
    metadata:
      labels:
        app: web4-identity
    spec:
      containers:
      - name: identity
        image: web4/identity:v1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: web4-secrets
              key: database-url
        - name: LEDGER_URL
          value: "http://ledger-service:26657"
        - name: HSM_TYPE
          value: "tpm2"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: tpm
          mountPath: /dev/tpm0
      volumes:
      - name: tpm
        hostPath:
          path: /dev/tpm0

---
apiVersion: v1
kind: Service
metadata:
  name: identity-service
  namespace: web4
spec:
  selector:
    app: web4-identity
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

### Environment Variables

**Identity Service**:
```env
DATABASE_URL=postgresql://user:pass@host:5432/identity
LEDGER_URL=http://cosmos-node:26657
HSM_TYPE=tpm2|software|yubikey
LOG_LEVEL=info
PORT=8001
WORKERS=4
```

**Governance Service**:
```env
DATABASE_URL=postgresql://user:pass@host:5432/governance
LEDGER_URL=http://cosmos-node:26657
REDIS_URL=redis://redis:6379
LAW_CACHE_TTL=3600
PORT=8002
```

**Authorization Service**:
```env
REDIS_URL=redis://redis:6379
IDENTITY_SERVICE=http://identity-service:8001
GOVERNANCE_SERVICE=http://governance-service:8002
REPUTATION_SERVICE=http://reputation-service:8004
PORT=8003
```

---

## Monitoring & Observability

### Metrics

All services expose Prometheus metrics at `/metrics`:

**Key Metrics**:
```
# Identity Service
web4_lct_minted_total{entity_type}
web4_lct_active_count{entity_type}
web4_signature_verification_duration_seconds
web4_birth_certificate_ledger_write_duration_seconds

# Authorization Service
web4_authorization_requests_total{decision}
web4_authorization_duration_seconds
web4_delegation_active_count
web4_atp_budget_remaining{delegation_id}

# Reputation Service
web4_reputation_updates_total{outcome_type}
web4_reputation_t3_score{entity,role}
web4_reputation_v3_score{entity,role}
web4_gaming_detected_total

# Resource Service
web4_resource_allocations_total{resource_type}
web4_resource_pool_utilization{resource_type}
web4_atp_conversion_rate{resource_type}

# Knowledge Service
web4_graph_triples_total
web4_sparql_query_duration_seconds
web4_graph_traversal_depth
```

### Logging

**Structured Logging** (JSON format):
```json
{
  "timestamp": "2025-11-09T12:00:00Z",
  "level": "INFO",
  "service": "identity",
  "request_id": "uuid-1234",
  "lct_id": "lct:web4:ai:001",
  "event": "lct_minted",
  "details": {
    "entity_type": "AI",
    "society_id": "society:prod",
    "witnesses": 2
  },
  "ledger_tx": "cosmos:tx:abc123",
  "duration_ms": 245
}
```

**Log Levels**:
- ERROR: Failed operations, exceptions
- WARN: Degraded performance, near-limits
- INFO: Successful operations, state changes
- DEBUG: Detailed execution traces

### Tracing

**OpenTelemetry** integration for distributed tracing:

**Trace Context**:
```
traceparent: 00-{trace-id}-{span-id}-01
```

**Example Trace**:
```
AuthorizeAction (8003)
├─ VerifyLCT (8001) [120ms]
│  ├─ QueryDatabase [45ms]
│  └─ VerifySignature [75ms]
├─ CheckLawCompliance (8002) [80ms]
│  ├─ GetLawDataset [20ms]
│  └─ EvaluateNorms [60ms]
├─ GetReputation (8004) [95ms]
│  └─ QueryDatabase [90ms]
└─ RecordDecision (ledger) [200ms]
Total: 495ms
```

### Alerting

**Critical Alerts** (PagerDuty):
- Service down for >1 minute
- Error rate >5%
- P99 latency >5 seconds
- Ledger sync lag >100 blocks
- Database connection pool exhausted

**Warning Alerts** (Slack):
- Error rate >1%
- P99 latency >1 second
- Disk usage >80%
- Memory usage >80%
- ATP pool depletion >90%

---

## Operational Runbooks

### Deployment Procedure

**Pre-Deployment Checklist**:
- [ ] Database migrations tested
- [ ] Configuration validated
- [ ] Secrets rotated
- [ ] Monitoring dashboard ready
- [ ] Rollback plan prepared

**Deployment Steps**:

1. **Update Ledger Schema** (if needed)
   ```bash
   ./scripts/ledger-migrate.sh v1.1.0
   ```

2. **Deploy Database Migrations**
   ```bash
   kubectl apply -f migrations/v1.1.0-job.yaml
   kubectl wait --for=condition=complete job/migration-v1.1.0
   ```

3. **Rolling Update Services**
   ```bash
   kubectl set image deployment/web4-identity \
     identity=web4/identity:v1.1.0
   kubectl rollout status deployment/web4-identity
   ```

4. **Verify Health**
   ```bash
   curl https://identity.web4.io/health
   curl https://identity.web4.io/ready
   ```

5. **Smoke Tests**
   ```bash
   ./scripts/smoke-test.sh production
   ```

### Incident Response

**Severity Levels**:
- **P0**: Complete outage, data loss
- **P1**: Degraded performance, partial outage
- **P2**: Minor issues, workaround available
- **P3**: Cosmetic issues, low impact

**P0 Response**:

1. **Assess** (5 minutes)
   - Check service health endpoints
   - Review error rates in Grafana
   - Check ledger sync status

2. **Mitigate** (15 minutes)
   - Scale up if resource constrained
   - Rollback if recent deployment
   - Failover to backup region

3. **Communicate** (ongoing)
   - Update status page
   - Notify stakeholders
   - Post to incident channel

4. **Resolve** (variable)
   - Fix root cause
   - Deploy patch
   - Verify resolution

5. **Post-Mortem** (48 hours)
   - Document timeline
   - Identify root cause
   - Create action items

### Backup & Recovery

**Backup Schedule**:
- Database: Full daily, incremental hourly
- Ledger: Continuous replication
- RDF Store: Full daily

**Recovery Procedures**:

**Database Recovery**:
```bash
# Stop service
kubectl scale deployment/web4-identity --replicas=0

# Restore from backup
pg_restore -d identity backups/identity-2025-11-09.dump

# Restart service
kubectl scale deployment/web4-identity --replicas=3
```

**Ledger Recovery**:
```bash
# Sync from validator network
gaiad start --state-sync-rpc-servers="https://node1,https://node2"
```

**RDF Store Recovery**:
```bash
# Restore from daily backup
./scripts/blazegraph-restore.sh backups/graph-2025-11-09.jnl
```

---

## Security Considerations

### Network Security

**Firewall Rules**:
```
# Public endpoints
Allow 443/tcp from Internet to API Gateway

# Internal services
Allow 8001-8006/tcp from Gateway to Services
Allow 5432/tcp from Services to Database
Allow 6379/tcp from Services to Redis
Allow 26657/tcp from Services to Ledger

# Deny all other traffic
```

**TLS Configuration**:
- All external traffic: TLS 1.3
- All internal traffic: mTLS
- Certificate rotation: 90 days
- Cipher suites: Modern only

### Access Control

**Service-to-Service Authentication**:
- mTLS certificates
- Service mesh (Istio recommended)
- Network policies

**API Authentication**:
- LCT-based authentication
- Ed25519 signature verification
- Nonce-based replay protection

### Secret Management

**Secrets Storage**: Kubernetes Secrets or HashiCorp Vault

**Secrets**:
- Database credentials
- Redis passwords
- Ledger validator keys
- HSM access credentials
- TLS certificates

**Rotation Schedule**:
- Database passwords: 90 days
- API keys: 30 days
- TLS certificates: 90 days
- Validator keys: Never (requires governance)

---

## Scaling Strategy

### Horizontal Scaling

**Auto-Scaling Rules**:

**Identity Service**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web4-identity
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web4-identity
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: web4_authorization_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

**Load Distribution**:
- Round-robin for stateless services
- Consistent hashing for cache-heavy services
- Geo-aware routing for multi-region

### Vertical Scaling

**Resource Allocation** (per service):

| Service | CPU (req/limit) | Memory (req/limit) |
|---------|-----------------|-------------------|
| Identity | 500m / 1000m | 512Mi / 1Gi |
| Governance | 250m / 500m | 256Mi / 512Mi |
| Authorization | 500m / 1000m | 512Mi / 1Gi |
| Reputation | 500m / 1000m | 1Gi / 2Gi |
| Resources | 250m / 500m | 256Mi / 512Mi |
| Knowledge | 1000m / 2000m | 2Gi / 4Gi |

### Database Scaling

**PostgreSQL**:
- Read replicas for query load
- Connection pooling (PgBouncer)
- Partitioning by entity_id
- Archival of old data

**Redis**:
- Redis Cluster for horizontal scaling
- Separate clusters per service
- Persistence: RDB snapshots + AOF

**Blazegraph**:
- Federation for very large graphs
- Read replicas for queries
- Write-ahead logging

---

## Cost Optimization

### Resource Efficiency

**Cost Breakdown** (estimated monthly, moderate scale):
- Compute (K8s cluster): $2,000
- Database (managed PostgreSQL): $800
- Redis (managed): $400
- Ledger (validator nodes): $1,500
- Egress bandwidth: $300
- **Total**: ~$5,000/month

**Optimization Strategies**:
1. Use spot instances for non-critical workloads
2. Right-size resources based on metrics
3. Implement caching aggressively
4. Batch ledger writes
5. Compress RDF triples

### Performance Targets

**Latency SLOs**:
- P50: <100ms
- P95: <500ms
- P99: <1000ms

**Throughput Targets**:
- Authorization requests: 10,000 req/s
- LCT minting: 100 req/s
- Reputation updates: 1,000 req/s

**Availability**: 99.9% uptime (43 minutes/month downtime allowed)

---

## Appendix: Service Startup

**Service Initialization Order**:

1. Infrastructure (db, redis, ledger)
2. Identity Service (first to start)
3. Governance Service
4. Reputation Service
5. Resource Service
6. Knowledge Service
7. Authorization Service (last, depends on all)
8. API Gateway

**Health Check Endpoints**:

All services implement:
- `GET /health` - Simple alive check
- `GET /ready` - Ready for traffic (dependencies up)
- `GET /metrics` - Prometheus metrics

**Graceful Shutdown**:
1. Stop accepting new requests
2. Finish in-flight requests (30s timeout)
3. Close database connections
4. Flush metrics
5. Exit

---

**End of Deployment Architecture**

For questions or updates, contact: web4-ops@example.com
