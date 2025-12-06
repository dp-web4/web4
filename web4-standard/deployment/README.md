# Web4 Deployment Guide

Production deployment configurations for Web4 services.

## Services

### ATP Demurrage Service

Automatic ATP decay calculation running on schedule.

#### Option 1: Systemd Service (Recommended for Production)

**Install**:
```bash
# Copy service file
sudo cp systemd/web4-demurrage.service /etc/systemd/system/

# Copy configuration
sudo mkdir -p /etc/web4
sudo cp config/demurrage.example.json /etc/web4/demurrage.json

# Edit configuration
sudo nano /etc/web4/demurrage.json

# Create user
sudo useradd -r -s /bin/false web4

# Create directories
sudo mkdir -p /var/log/web4 /var/lib/web4 /opt/web4
sudo chown web4:web4 /var/log/web4 /var/lib/web4 /opt/web4

# Copy service code
sudo cp ../implementation/reference/demurrage_service.py /opt/web4/
sudo cp ../implementation/reference/atp_demurrage.py /opt/web4/
sudo chown web4:web4 /opt/web4/*.py

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable web4-demurrage
sudo systemctl start web4-demurrage
```

**Monitor**:
```bash
# Status
sudo systemctl status web4-demurrage

# Logs
sudo journalctl -u web4-demurrage -f

# Metrics
cat /var/lib/web4/demurrage_metrics.json
```

**Manage**:
```bash
# Restart
sudo systemctl restart web4-demurrage

# Stop
sudo systemctl stop web4-demurrage

# Disable
sudo systemctl disable web4-demurrage
```

#### Option 2: Cron Job (Simple Deployments)

**Install**:
```bash
# Copy configuration
sudo mkdir -p /etc/web4
sudo cp config/demurrage.example.json /etc/web4/demurrage.json

# Create user
sudo useradd -r -s /bin/false web4

# Create directories
sudo mkdir -p /var/log/web4 /var/lib/web4 /opt/web4
sudo chown web4:web4 /var/log/web4 /var/lib/web4 /opt/web4

# Copy service code
sudo cp ../implementation/reference/demurrage_service.py /opt/web4/
sudo cp ../implementation/reference/atp_demurrage.py /opt/web4/
sudo chown web4:web4 /opt/web4/*.py

# Install cron job
sudo cp cron/web4-demurrage.cron /etc/cron.d/web4-demurrage
sudo chmod 644 /etc/cron.d/web4-demurrage
```

**Monitor**:
```bash
# Cron logs
tail -f /var/log/web4/demurrage-cron.log

# Metrics
cat /var/lib/web4/demurrage_metrics.json
```

**Test**:
```bash
# Run manually
sudo -u web4 /usr/bin/python3 /opt/web4/demurrage_service.py --once --config /etc/web4/demurrage.json
```

#### Option 3: Development Mode

For local testing and development:

```bash
# Foreground mode (see output)
python3 demurrage_service.py --foreground

# Single cycle test
python3 demurrage_service.py --once

# With custom config
python3 demurrage_service.py --foreground --config my_config.json
```

## Configuration

Edit `/etc/web4/demurrage.json`:

```json
{
  "interval_hours": 24,
  "demurrage": {
    "society_id": "web4:main",
    "base_rate": 0.05,
    "grace_period_days": 7,
    "grace_rate_multiplier": 0.1,
    "max_holding_days": 365
  }
}
```

**Parameters**:
- `base_rate`: Monthly decay rate (0.05 = 5% per month)
- `grace_period_days`: Reduced decay for first N days
- `grace_rate_multiplier`: Decay multiplier during grace (0.1 = 10% of base)
- `max_holding_days`: Force ADP conversion after N days

**Rate Presets**:
- None: 0.00 (testing only)
- Low: 0.01 (1% per month, ~12% per year)
- Moderate: 0.05 (5% per month, ~45% per year)
- High: 0.10 (10% per month, ~68% per year)
- Aggressive: 0.20 (20% per month, ~89% per year)

## Monitoring

### Metrics

Check `/var/lib/web4/demurrage_metrics.json`:

```json
{
  "total_cycles": 30,
  "total_entities_processed": 1250,
  "total_atp_decayed": 45000,
  "last_cycle_time": "2025-12-05T02:00:00Z",
  "last_cycle_duration_seconds": 2.5,
  "errors_count": 0,
  "last_error": null
}
```

### Health Checks

**Systemd**:
```bash
# Service running?
systemctl is-active web4-demurrage

# Last run time
systemctl show web4-demurrage -p ActiveEnterTimestamp

# Memory usage
systemctl show web4-demurrage -p MemoryCurrent
```

**Cron**:
```bash
# Last run (check logs)
tail -1 /var/log/web4/demurrage-cron.log

# Metrics file age
stat -c %y /var/lib/web4/demurrage_metrics.json
```

### Alerts

Add to monitoring system:

```bash
# Alert if last cycle > 25 hours ago
LAST_CYCLE=$(jq -r .last_cycle_time /var/lib/web4/demurrage_metrics.json)
AGE_HOURS=$(( ($(date +%s) - $(date -d "$LAST_CYCLE" +%s)) / 3600 ))
if [ $AGE_HOURS -gt 25 ]; then
  echo "ALERT: Demurrage cycle overdue by $AGE_HOURS hours"
fi

# Alert on errors
ERROR_COUNT=$(jq -r .errors_count /var/lib/web4/demurrage_metrics.json)
if [ $ERROR_COUNT -gt 0 ]; then
  echo "ALERT: Demurrage service has $ERROR_COUNT errors"
fi
```

## Troubleshooting

### Service won't start

```bash
# Check status
sudo systemctl status web4-demurrage

# Check logs
sudo journalctl -u web4-demurrage -n 50

# Common issues:
# 1. Permissions: sudo chown web4:web4 /var/log/web4 /var/lib/web4
# 2. Python path: which python3
# 3. Missing modules: sudo pip3 install <module>
```

### No decay happening

```bash
# Check if service is running
systemctl is-active web4-demurrage

# Check last cycle time
jq -r .last_cycle_time /var/lib/web4/demurrage_metrics.json

# Check holdings (need database access)
# psql -U postgres -d web4 -c "SELECT COUNT(*) FROM atp_holdings;"
```

### High memory usage

```bash
# Check memory
systemctl show web4-demurrage -p MemoryCurrent

# If > 100MB, check holdings count
# Large number of holdings = more memory
# Consider batch processing or rate limiting
```

## Security

**Principle of Least Privilege**:
- Service runs as dedicated `web4` user
- No shell access (`/bin/false`)
- Read-only filesystem except logs/metrics
- No network access required (local DB only)

**File Permissions**:
```bash
# Service files
sudo chmod 644 /etc/systemd/system/web4-demurrage.service
sudo chmod 644 /etc/cron.d/web4-demurrage

# Configuration (may contain DB credentials)
sudo chmod 600 /etc/web4/demurrage.json
sudo chown root:root /etc/web4/demurrage.json

# Code (read-only)
sudo chmod 555 /opt/web4/demurrage_service.py
sudo chown root:root /opt/web4/demurrage_service.py

# Logs (web4 writes)
sudo chmod 755 /var/log/web4
sudo chown web4:web4 /var/log/web4
```

## Backup and Recovery

**Backup**:
```bash
# Configuration
sudo cp /etc/web4/demurrage.json /backup/web4/

# Metrics history
sudo cp /var/lib/web4/demurrage_metrics.json /backup/web4/

# Database (if using PostgreSQL)
pg_dump -U postgres web4 > /backup/web4/db_$(date +%Y%m%d).sql
```

**Recovery**:
```bash
# Restore configuration
sudo cp /backup/web4/demurrage.json /etc/web4/

# Restart service
sudo systemctl restart web4-demurrage

# Database (if needed)
psql -U postgres -d web4 < /backup/web4/db_20251205.sql
```

## Performance Tuning

**For large societies (>100k entities)**:

1. **Increase interval**: `interval_hours: 48` (every 2 days)
2. **Batch processing**: Add pagination to `apply_global_decay()`
3. **Database indexing**: Ensure `atp_holdings` has indexes on `entity_lct` and `last_decay_calculated`
4. **Parallel processing**: Use multiprocessing for independent holdings

**For low-resource environments**:

1. **Reduce log verbosity**: `log_level: WARNING`
2. **Disable persistence**: `enable_persistence: false` (in-memory only)
3. **Increase check interval**: Sleep 300 (5 minutes instead of 1)

## Migration

**From in-memory to persistent**:

```bash
# 1. Stop service
sudo systemctl stop web4-demurrage

# 2. Export current holdings (if possible)
# python3 export_holdings.py > holdings.json

# 3. Update config to enable persistence
sudo nano /etc/web4/demurrage.json
# Set: "enable_persistence": true

# 4. Import holdings (if exported)
# python3 import_holdings.py < holdings.json

# 5. Restart service
sudo systemctl start web4-demurrage
```

---

**Last Updated**: 2025-12-05
**Version**: 1.0.0
**Author**: Legion Autonomous Web4 Research
