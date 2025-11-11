"""
Prometheus Metrics Registry Helper

Provides separate registries for secured services to avoid metric name collisions.

Usage:
    from metrics_registry import get_secured_registry

    registry = get_secured_registry()
    counter = Counter('my_metric', 'Description', registry=registry)
"""

from prometheus_client import CollectorRegistry, REGISTRY

# Create separate registries for secured services
_secured_registries = {}


def get_secured_registry(service_name: str = "default") -> CollectorRegistry:
    """
    Get or create a separate registry for a secured service.

    This prevents metric name collisions when multiple services
    are imported in the same process.

    Args:
        service_name: Unique name for the service (e.g., "identity", "reputation")

    Returns:
        CollectorRegistry: A dedicated registry for this service
    """
    if service_name not in _secured_registries:
        _secured_registries[service_name] = CollectorRegistry()

    return _secured_registries[service_name]


def clear_default_registry():
    """
    Clear all collectors from the default registry.

    Useful when running multiple services in development/testing
    to avoid "Duplicated timeseries" errors.
    """
    try:
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass  # Already unregistered
    except Exception as e:
        print(f"Warning: Could not clear default registry: {e}")
