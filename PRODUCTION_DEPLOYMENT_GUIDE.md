# Web4 Identity Service - Production Deployment Guide

**Version**: 3.0.0-phase2
**Security Level**: Phase 2 Attack Resistance
**Status**: Production-Ready
**Last Updated**: 2025-11-13 (Session #22)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Security Validation](#security-validation)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Operational Procedures](#operational-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Security Hardening Checklist](#security-hardening-checklist)

---

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Memory**: Minimum 512MB RAM (1GB+ recommended)
- **CPU**: 1 core minimum (2+ recommended for production)
- **Disk**: 1GB+ free space
- **Network**: Stable internet connection

### Required Packages

```bash
pip install fastapi uvicorn pydantic prometheus_client
```

### Optional (Recommended for Production)

```bash
# For distributed rate limiting
pip install redis fastapi-limiter

# For database persistence
pip install psycopg2-binary sqlalchemy

# For API gateway
# Use nginx, traefik, or similar
```

---

## Security Validation

### Phase 2 Security Features

✅ **Validated** (Session #21):
- Rate limiting (0% DOS bypass)
- Input validation (0% injection bypass)
- Resource limits (0% overflow bypass)
- Proper error codes (409, 422, 429)
- Extra field rejection

### Pre-Deployment Security Checklist

Run security validation before deploying:

```bash
cd ~/ai-workspace/web4/web4-standard/implementation/services
export WEB4_TEST_MODE=true WEB4_IDENTITY_PORT=8001
python3 identity_service_phase2.py &

# Wait for service to start
sleep 3

# Run validation
cd /tmp
python3 phase2_security_validation.py

# Expected: 0% attack bypass rate
# If any attacks succeed, DO NOT deploy
```

---

## Configuration

### Environment Variables

```bash
# Required
export WEB4_IDENTITY_HOST="0.0.0.0"           # Listen on all interfaces
export WEB4_IDENTITY_PORT="8001"               # Service port

# Security
export WEB4_TEST_MODE="false"                  # CRITICAL: false in production
export RATE_LIMIT_MAX_REQUESTS_PER_IP="20"    # Adjust based on traffic
export RATE_LIMIT_WINDOW_SECONDS="60"         # Sliding window
export MAX_WITNESS_COUNT="10"                  # Max witnesses per LCT
export MAX_IDENTIFIER_LENGTH="512"             # Max identifier chars
export MAX_WITNESS_ID_LENGTH="256"             # Max witness ID chars

# ATP Configuration
export ATP_MINT_BASE_COST="100"                # Base ATP cost to mint LCT
export ATP_MINT_SCALE_FACTOR="1.5"            # Exponential scaling
export INITIAL_ATP_GRANT="10000"              # ATP granted to new entities

# Witness Validation
export MIN_WITNESS_REPUTATION="0.4"            # Minimum T3 score
export MIN_WITNESS_AGE_DAYS="30"               # Minimum witness age
export MIN_WITNESS_ACTIONS="50"                # Minimum witness actions

# Optional: Redis for distributed rate limiting
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

### Configuration File

Create `/etc/web4/identity_service.conf`:

```ini
[service]
host = 0.0.0.0
port = 8001

[security]
test_mode = false
rate_limit_per_ip = 20
rate_limit_window = 60
max_witness_count = 10
max_identifier_length = 512

[atp]
mint_base_cost = 100
mint_scale_factor = 1.5
initial_grant = 10000

[witness]
min_reputation = 0.4
min_age_days = 30
min_actions = 50
```

---

## Deployment Options

### Option 1: Standalone Service (Development/Testing)

```bash
cd ~/ai-workspace/web4/web4-standard/implementation/services

# Load configuration
source /etc/web4/identity_service.env

# Run service
python3 identity_service_phase2.py
```

**Pros**: Simple, easy to debug
**Cons**: Single point of failure, limited scalability

---

### Option 2: Systemd Service (Production)

Create `/etc/systemd/system/web4-identity.service`:

```ini
[Unit]
Description=Web4 Identity Service (Phase 2)
After=network.target

[Service]
Type=simple
User=web4
Group=web4
WorkingDirectory=/opt/web4/services
EnvironmentFile=/etc/web4/identity_service.env
ExecStart=/usr/bin/python3 identity_service_phase2.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/web4/data

[Install]
WantedBy=multi-user.target
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable web4-identity
sudo systemctl start web4-identity
sudo systemctl status web4-identity
```

**Pros**: Auto-restart, logging, standard management
**Cons**: Requires root access to configure

---

### Option 3: Docker Container (Recommended for Production)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    prometheus_client \
    redis \
    fastapi-limiter

# Create app user
RUN useradd -m -u 1000 web4

# Copy application
WORKDIR /app
COPY web4-standard/implementation/ /app/
COPY web4-standard/implementation/services/identity_service_phase2.py /app/

# Set ownership
RUN chown -R web4:web4 /app

# Switch to non-root user
USER web4

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import requests; requests.get('http://localhost:8001/health')"

# Run service
CMD ["python3", "identity_service_phase2.py"]
```

**Build and run**:

```bash
docker build -t web4-identity:phase2 .

docker run -d \
  --name web4-identity \
  --restart unless-stopped \
  -p 8001:8001 \
  --env-file /etc/web4/identity_service.env \
  -v /opt/web4/data:/app/data \
  web4-identity:phase2
```

**Pros**: Isolated, reproducible, easy scaling
**Cons**: Requires Docker infrastructure

---

### Option 4: Kubernetes Deployment (Enterprise)

Create `k8s/deployment.yaml`:

```yaml
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
      - name: identity-service
        image: web4-identity:phase2
        ports:
        - containerPort: 8001
        env:
        - name: WEB4_TEST_MODE
          value: "false"
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: web4-identity-service
  namespace: web4
spec:
  selector:
    app: web4-identity
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: LoadBalancer
```

**Deploy**:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods -n web4
kubectl logs -f deployment/web4-identity -n web4
```

**Pros**: High availability, auto-scaling, load balancing
**Cons**: Complex infrastructure, higher cost

---

## Monitoring & Alerts

### Prometheus Metrics

The service exposes metrics at `/metrics`:

```
# Key metrics to monitor
web4_identity_lct_minted_total{entity_type, society}
web4_identity_lct_mint_rejected_total{reason}
web4_identity_rate_limit_rejected_total{limit_type}
web4_identity_input_validation_rejected_total{field}
```

### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'web4-identity'
    static_configs:
      - targets: ['localhost:8001']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

### Grafana Dashboard

Create dashboard with panels:

1. **LCT Minting Rate**: `rate(web4_identity_lct_minted_total[5m])`
2. **Rejection Rate**: `rate(web4_identity_lct_mint_rejected_total[5m])`
3. **Rate Limit Hits**: `rate(web4_identity_rate_limit_rejected_total[5m])`
4. **Input Validation Failures**: `rate(web4_identity_input_validation_rejected_total[5m])`

### Alert Rules

Create `web4_alerts.yml`:

```yaml
groups:
  - name: web4_identity
    rules:
      - alert: HighRejectionRate
        expr: rate(web4_identity_lct_mint_rejected_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High LCT mint rejection rate"

      - alert: RateLimitingActive
        expr: rate(web4_identity_rate_limit_rejected_total[1m]) > 5
        for: 2m
        labels:
          severity: info
        annotations:
          summary: "Rate limiting actively blocking requests"

      - alert: ServiceDown
        expr: up{job="web4-identity"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Web4 Identity Service is down"
```

---

## Operational Procedures

### Starting the Service

```bash
# Check configuration
cat /etc/web4/identity_service.env

# Start service
sudo systemctl start web4-identity

# Verify health
curl http://localhost:8001/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-13T...",
#   "version": "3.0.0-phase2",
#   "security_level": "phase2_attack_resistance"
# }
```

### Stopping the Service

```bash
# Graceful stop
sudo systemctl stop web4-identity

# Check for clean shutdown
journalctl -u web4-identity -n 50
```

### Reloading Configuration

```bash
# Edit configuration
sudo vim /etc/web4/identity_service.env

# Reload systemd
sudo systemctl daemon-reload

# Restart service
sudo systemctl restart web4-identity
```

### Viewing Logs

```bash
# Real-time logs
sudo journalctl -u web4-identity -f

# Last 100 lines
sudo journalctl -u web4-identity -n 100

# Filter by date
sudo journalctl -u web4-identity --since "2025-11-13 00:00:00"

# Filter errors only
sudo journalctl -u web4-identity -p err
```

### Backup Procedures

```bash
# Backup LCT registry (if file-based)
tar -czf web4-lct-registry-$(date +%Y%m%d).tar.gz /opt/web4/data/lct_registry/

# Backup configuration
cp /etc/web4/identity_service.env /backup/identity_service.env.$(date +%Y%m%d)

# Backup logs
journalctl -u web4-identity --since "2025-11-01" > web4-logs-november.log
```

---

## Troubleshooting

### Service Won't Start

**Check configuration**:
```bash
# Verify env file exists
ls -l /etc/web4/identity_service.env

# Check for syntax errors
python3 -m py_compile identity_service_phase2.py
```

**Check port availability**:
```bash
# Is port already in use?
sudo lsof -i :8001

# Kill existing process if needed
sudo kill $(lsof -t -i:8001)
```

**Check permissions**:
```bash
# Service user can read files?
sudo -u web4 ls /opt/web4/services/
```

### High CPU Usage

**Check rate limiting**:
```bash
# View rate limit metrics
curl http://localhost:8001/metrics | grep rate_limit

# If rate_limit_rejected is high, possible attack
# Increase rate limits or add IP blocking
```

**Check for request loops**:
```bash
# View access logs
journalctl -u web4-identity | grep POST | tail -50

# Look for repeated requests from same IP
```

### High Memory Usage

**Check for memory leaks**:
```bash
# Monitor memory over time
ps aux | grep identity_service_phase2

# Restart service if memory continues growing
sudo systemctl restart web4-identity
```

**Reduce memory footprint**:
```python
# In production, limit in-memory storage
# Use database for LCT registry
# Use Redis for rate limiting
```

### Rate Limiting Too Aggressive

**Symptoms**:
- Legitimate users blocked (HTTP 429)
- `rate_limit_rejected` metric high

**Solution**:
```bash
# Increase limits in config
export RATE_LIMIT_MAX_REQUESTS_PER_IP="50"  # Was 20

# Or implement per-user rate limits
# Or use IP whitelisting for trusted sources
```

### ATP Costs Too High/Low

**Monitor minting costs**:
```bash
curl http://localhost:8001/metrics | grep lct_minting_cost
```

**Adjust scaling**:
```bash
# If attacks are economical, increase base cost
export ATP_MINT_BASE_COST="200"  # Was 100

# If legitimate users can't afford, decrease
export ATP_MINT_BASE_COST="50"
```

---

## Security Hardening Checklist

### Pre-Production Checklist

- [ ] **Test Mode Disabled**: `WEB4_TEST_MODE=false`
- [ ] **Rate Limiting Configured**: Appropriate limits for traffic
- [ ] **Input Validation Active**: Max lengths enforced
- [ ] **HTTPS Only**: TLS/SSL certificate configured
- [ ] **Firewall Rules**: Only necessary ports open
- [ ] **Monitoring Enabled**: Prometheus + Grafana
- [ ] **Alerts Configured**: Critical alerts to on-call
- [ ] **Backup Procedures**: Automated backups scheduled
- [ ] **Access Logs**: Enabled and rotated
- [ ] **Security Validation**: Phase 2 tests pass (0% bypass)

### Network Security

```bash
# Firewall rules (ufw example)
sudo ufw allow 8001/tcp  # Identity service
sudo ufw allow 80/tcp    # HTTP (if using reverse proxy)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Or use iptables
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

### Reverse Proxy (Nginx)

```nginx
upstream web4_identity {
    server localhost:8001;
    # Add more servers for load balancing
}

server {
    listen 443 ssl http2;
    server_name identity.web4.example.com;

    ssl_certificate /etc/letsencrypt/live/identity.web4.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/identity.web4.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting (additional layer)
    limit_req_zone $binary_remote_addr zone=identity_limit:10m rate=10r/m;
    limit_req zone=identity_limit burst=20;

    location / {
        proxy_pass http://web4_identity;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Security

```bash
# If using PostgreSQL for persistence
# Create dedicated user
sudo -u postgres createuser web4_identity

# Create database
sudo -u postgres createdb web4_identity_db

# Grant minimal permissions
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE web4_identity_db TO web4_identity;"
sudo -u postgres psql -c "GRANT USAGE ON SCHEMA public TO web4_identity;"
```

---

## Production Deployment Summary

### Recommended Architecture

```
[Internet]
    |
    v
[Load Balancer / WAF]
    |
    v
[Nginx Reverse Proxy]
    |
    v
[Web4 Identity Service (Phase 2)]
    |
    +---> [PostgreSQL] (LCT registry)
    +---> [Redis] (rate limiting)
    +---> [Prometheus] (metrics)
```

### Deployment Steps

1. **Prepare Infrastructure**
   - Provision servers/containers
   - Configure networking
   - Set up databases

2. **Configure Service**
   - Set all environment variables
   - Verify TEST_MODE=false
   - Configure rate limits

3. **Run Security Validation**
   - Execute phase2_security_validation.py
   - Verify 0% bypass rate
   - Review metrics

4. **Deploy Service**
   - Start with systemd or Docker
   - Verify health endpoint
   - Check logs for errors

5. **Configure Monitoring**
   - Set up Prometheus scraping
   - Create Grafana dashboards
   - Configure alerts

6. **Test End-to-End**
   - Mint test LCT
   - Verify ATP costs
   - Check witness validation
   - Confirm rate limiting

7. **Go Live**
   - Update DNS
   - Enable production traffic
   - Monitor closely for 24h

### Post-Deployment

- **Monitor metrics**: LCT minting rate, rejections, rate limits
- **Review logs daily**: Look for anomalies
- **Weekly security scans**: Re-run validation tests
- **Monthly backups**: Test restore procedures
- **Quarterly audits**: External security review

---

## Support & Documentation

### Additional Resources

- **Phase 2 Security Validation**: `private-context/insights/2025-11-13-phase2-security-validation-results.md`
- **Epistemic Status Registry**: `private-context/WEB4_EPISTEMIC_STATUS_REGISTRY.md`
- **Authorization System**: `web4/proposals/WEB4-AUTH-001-LCT-Authorization-System.md`
- **LCT Registry**: `web4-standard/implementation/reference/lct_registry.py`

### Contact

- **Issues**: https://github.com/dp-web4/web4/issues
- **Security**: Report critical vulnerabilities to security@web4.example.com

---

**Production Deployment Guide Version**: 1.0
**Service Version**: 3.0.0-phase2
**Security Level**: Phase 2 Attack Resistance (0% bypass rate)
**Status**: Production-Ready

**Last Updated**: 2025-11-13 (Session #22)
