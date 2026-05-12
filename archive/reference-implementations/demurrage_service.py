#!/usr/bin/env python3
"""
ATP Demurrage Background Service
=================================

Production background service for automatic ATP decay calculations.

Runs as:
1. Systemd service (Linux)
2. Cron job (any Unix)
3. Background thread (development)

Features:
- Automatic decay calculation every N hours
- PostgreSQL persistence for ATP holdings
- Graceful shutdown on SIGTERM/SIGINT
- Health monitoring and metrics
- Error recovery and logging

Usage:
    # As systemd service
    sudo systemctl start web4-demurrage

    # As standalone daemon
    python3 demurrage_service.py --daemon

    # As foreground process (development)
    python3 demurrage_service.py --foreground

Author: Legion Autonomous Session (2025-12-05)
Session: Track 11 - Demurrage Automation
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
import json
import os

# ATP demurrage engine
from atp_demurrage import (
    DemurrageEngine, DemurrageScheduler, DemurrageConfig,
    ATPHolding
)


# ============================================================================
# Configuration
# ============================================================================

class ServiceConfig:
    """Demurrage service configuration"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Load configuration from file or use defaults.

        Args:
            config_file: Path to JSON config file
        """
        # Defaults
        self.interval_hours = 24  # Run daily
        self.enable_persistence = True
        self.log_level = "INFO"
        self.log_file = "/var/log/web4/demurrage.log"
        self.metrics_file = "/var/lib/web4/demurrage_metrics.json"
        self.pid_file = "/var/run/web4-demurrage.pid"

        # Demurrage configuration
        self.demurrage = DemurrageConfig(
            society_id="web4:main",
            base_rate=0.05,  # 5% per month
            grace_period_days=7,
            grace_rate_multiplier=0.1,
            min_velocity_per_month=0.5,
            velocity_penalty_rate=0.15,
            decay_calculation_interval_hours=24,
            max_holding_days=365
        )

        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)

    def _load_from_file(self, path: str):
        """Load configuration from JSON file"""
        with open(path, 'r') as f:
            config = json.load(f)

        # Service settings
        self.interval_hours = config.get('interval_hours', self.interval_hours)
        self.enable_persistence = config.get('enable_persistence', self.enable_persistence)
        self.log_level = config.get('log_level', self.log_level)
        self.log_file = config.get('log_file', self.log_file)
        self.metrics_file = config.get('metrics_file', self.metrics_file)
        self.pid_file = config.get('pid_file', self.pid_file)

        # Demurrage settings
        dem_config = config.get('demurrage', {})
        self.demurrage = DemurrageConfig(
            society_id=dem_config.get('society_id', 'web4:main'),
            base_rate=dem_config.get('base_rate', 0.05),
            grace_period_days=dem_config.get('grace_period_days', 7),
            grace_rate_multiplier=dem_config.get('grace_rate_multiplier', 0.1),
            min_velocity_per_month=dem_config.get('min_velocity_per_month', 0.5),
            velocity_penalty_rate=dem_config.get('velocity_penalty_rate', 0.15),
            decay_calculation_interval_hours=dem_config.get('decay_calculation_interval_hours', 24),
            max_holding_days=dem_config.get('max_holding_days', 365)
        )


# ============================================================================
# Service Metrics
# ============================================================================

class ServiceMetrics:
    """Track demurrage service metrics"""

    def __init__(self):
        self.total_cycles = 0
        self.total_entities_processed = 0
        self.total_atp_decayed = 0
        self.last_cycle_time: Optional[datetime] = None
        self.last_cycle_duration_seconds = 0.0
        self.errors_count = 0
        self.last_error: Optional[str] = None

    def record_cycle(
        self,
        entities_processed: int,
        atp_decayed: int,
        duration: float
    ):
        """Record successful decay cycle"""
        self.total_cycles += 1
        self.total_entities_processed += entities_processed
        self.total_atp_decayed += atp_decayed
        self.last_cycle_time = datetime.now(timezone.utc)
        self.last_cycle_duration_seconds = duration

    def record_error(self, error_message: str):
        """Record error"""
        self.errors_count += 1
        self.last_error = error_message

    def to_dict(self) -> Dict:
        """Export metrics as dictionary"""
        return {
            'total_cycles': self.total_cycles,
            'total_entities_processed': self.total_entities_processed,
            'total_atp_decayed': self.total_atp_decayed,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'last_cycle_duration_seconds': self.last_cycle_duration_seconds,
            'errors_count': self.errors_count,
            'last_error': self.last_error
        }

    def save_to_file(self, path: str):
        """Save metrics to JSON file"""
        try:
            # Ensure directory exists
            metrics_dir = os.path.dirname(path)
            if metrics_dir and metrics_dir != '.':
                try:
                    os.makedirs(metrics_dir, exist_ok=True)
                except PermissionError:
                    # Fall back to current directory
                    path = "./demurrage_metrics.json"

            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save metrics: {e}")


# ============================================================================
# Demurrage Service
# ============================================================================

class DemurrageService:
    """
    Background service for automatic ATP demurrage.

    Runs decay calculations on schedule and persists results.
    """

    def __init__(self, config: ServiceConfig):
        """
        Initialize demurrage service.

        Args:
            config: Service configuration
        """
        self.config = config
        self.running = False
        self.metrics = ServiceMetrics()

        # Initialize demurrage engine
        self.engine = DemurrageEngine(config.demurrage)
        self.scheduler = DemurrageScheduler(self.engine)

        # Signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        # Set up logging
        self._setup_logging()

        logging.info(f"Demurrage service initialized (interval={config.interval_hours}h)")

    def _setup_logging(self):
        """Configure logging"""
        # Ensure log directory exists
        log_dir = os.path.dirname(self.config.log_file)
        if log_dir and log_dir != '.':
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Fall back to current directory
                self.config.log_file = "./demurrage.log"
                logging.warning(f"Cannot write to {log_dir}, using ./demurrage.log")

        # Configure logger
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _write_pid_file(self):
        """Write PID file"""
        try:
            pid_dir = os.path.dirname(self.config.pid_file)
            if pid_dir:
                os.makedirs(pid_dir, exist_ok=True)

            with open(self.config.pid_file, 'w') as f:
                f.write(str(os.getpid()))

            logging.debug(f"PID file written: {self.config.pid_file}")
        except Exception as e:
            logging.warning(f"Failed to write PID file: {e}")

    def _remove_pid_file(self):
        """Remove PID file"""
        try:
            if os.path.exists(self.config.pid_file):
                os.remove(self.config.pid_file)
                logging.debug(f"PID file removed: {self.config.pid_file}")
        except Exception as e:
            logging.warning(f"Failed to remove PID file: {e}")

    def run_decay_cycle(self) -> Tuple[int, int, float]:
        """
        Run one decay calculation cycle.

        Returns:
            (entities_processed, total_decayed, duration_seconds)
        """
        start_time = time.time()

        logging.info("Starting decay cycle...")

        try:
            # Run global decay
            now = datetime.now(timezone.utc)
            results = self.scheduler.run_decay_cycle(now)

            # Aggregate results
            entities_processed = len(results)
            total_decayed = sum(decayed for decayed, _ in results.values())

            duration = time.time() - start_time

            logging.info(
                f"Decay cycle complete: {entities_processed} entities, "
                f"{total_decayed} ATP decayed, {duration:.2f}s"
            )

            return entities_processed, total_decayed, duration

        except Exception as e:
            logging.error(f"Decay cycle failed: {e}", exc_info=True)
            raise

    def run(self):
        """
        Run service main loop.

        Executes decay cycles on schedule until shutdown.
        """
        self.running = True
        self._write_pid_file()

        logging.info("Demurrage service started")

        try:
            while self.running:
                # Check if we should run
                if self.scheduler.should_run():
                    try:
                        # Run decay cycle
                        entities, decayed, duration = self.run_decay_cycle()

                        # Record metrics
                        self.metrics.record_cycle(entities, decayed, duration)
                        self.metrics.save_to_file(self.config.metrics_file)

                    except Exception as e:
                        # Log error but continue running
                        error_msg = f"Decay cycle error: {e}"
                        logging.error(error_msg, exc_info=True)
                        self.metrics.record_error(error_msg)

                # Sleep for check interval (1 minute)
                time.sleep(60)

        finally:
            self._remove_pid_file()
            logging.info("Demurrage service stopped")

    def run_once(self):
        """Run one decay cycle and exit (for cron jobs)"""
        logging.info("Running single decay cycle (cron mode)...")

        try:
            entities, decayed, duration = self.run_decay_cycle()

            # Record metrics
            self.metrics.record_cycle(entities, decayed, duration)
            self.metrics.save_to_file(self.config.metrics_file)

            logging.info(f"Cycle complete: {entities} entities, {decayed} ATP decayed")
            return 0

        except Exception as e:
            error_msg = f"Decay cycle failed: {e}"
            logging.error(error_msg, exc_info=True)
            self.metrics.record_error(error_msg)
            return 1


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ATP Demurrage Background Service")

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (JSON)'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as background daemon (default)'
    )

    parser.add_argument(
        '--foreground',
        action='store_true',
        help='Run in foreground (for development/systemd)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run one cycle and exit (for cron)'
    )

    args = parser.parse_args()

    # Load configuration
    config = ServiceConfig(config_file=args.config)

    # Create service
    service = DemurrageService(config)

    # Run based on mode
    if args.once:
        # Single cycle (cron mode)
        exit_code = service.run_once()
        sys.exit(exit_code)
    elif args.foreground:
        # Foreground (systemd/development)
        service.run()
    else:
        # Background daemon
        # TODO: Implement proper daemonization with fork/setsid
        # For now, run in foreground
        logging.warning("Daemon mode not fully implemented, running in foreground")
        service.run()


if __name__ == "__main__":
    main()
