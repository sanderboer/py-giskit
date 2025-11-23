"""PDOK Service Indexer and Health Monitor.

This module provides tools to:
1. Monitor health of registered PDOK services
2. Discover new PDOK services
3. Detect deprecated or changed services
4. Generate maintenance reports

Usage:
    # Check health of all services
    python -m giskit.indexer check-all

    # Check specific service
    python -m giskit.indexer check bgt

    # Discover new services
    python -m giskit.indexer discover

    # Generate full report
    python -m giskit.indexer report --output report.txt
"""

from giskit.indexer.monitor import (
    PDOKServiceMonitor,
    check_service_health,
    discover_services,
)

__all__ = [
    "PDOKServiceMonitor",
    "check_service_health",
    "discover_services",
]
