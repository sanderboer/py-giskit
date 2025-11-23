"""PDOK Service Indexer and Health Monitor.

This module provides tools to:
1. Monitor health of registered PDOK services
2. Discover new PDOK services
3. Detect deprecated or changed services
4. Generate maintenance reports

Usage:
    # Check health of all registered services
    python -m giskit.indexer.monitor --check-all

    # Discover new services
    python -m giskit.indexer.monitor --discover

    # Generate full report
    python -m giskit.indexer.monitor --report
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from giskit.providers.pdok import PDOK_SERVICES


class PDOKServiceMonitor:
    """Monitor and maintain PDOK service index."""

    def __init__(self, timeout: float = 10.0):
        """Initialize monitor.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(PDOK_SERVICES),
            "healthy": [],
            "unhealthy": [],
            "warnings": [],
            "discovered": [],
        }

    async def check_service_health(self, service_id: str, service_info: dict) -> dict:
        """Check if a service is healthy and accessible.

        Args:
            service_id: Service identifier (e.g., "bgt")
            service_info: Service metadata from PDOK_SERVICES

        Returns:
            Health check result with status and metadata
        """
        result = {
            "service_id": service_id,
            "url": service_info["url"],
            "title": service_info["title"],
            "status": "unknown",
            "status_code": None,
            "response_time": None,
            "error": None,
            "collections_found": 0,
            "api_version": None,
        }

        try:
            # Check landing page
            start_time = datetime.now()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    service_info["url"],
                    params={"f": "json"},  # PDOK requires f=json
                )
            response_time = (datetime.now() - start_time).total_seconds()

            result["status_code"] = response.status_code
            result["response_time"] = response_time

            if response.status_code == 200:
                data = response.json()

                # Check for OGC Features API structure
                if "links" in data:
                    result["status"] = "healthy"

                    # Try to get collections count
                    collections_url = None
                    for link in data.get("links", []):
                        if link.get("rel") == "data" or "collections" in link.get("href", ""):
                            collections_url = link["href"]
                            break

                    if collections_url:
                        # Make collections URL absolute
                        if not collections_url.startswith("http"):
                            from urllib.parse import urljoin

                            collections_url = urljoin(service_info["url"], collections_url)

                        try:
                            coll_resp = await client.get(
                                collections_url,
                                params={"f": "json"},
                            )
                            if coll_resp.status_code == 200:
                                coll_data = coll_resp.json()
                                result["collections_found"] = len(coll_data.get("collections", []))
                        except Exception:
                            pass  # Collections check is optional

                    # Extract API version from URL or metadata
                    if "/ogc/v1" in service_info["url"]:
                        result["api_version"] = "v1.x"
                    elif "/ogc/v2" in service_info["url"]:
                        result["api_version"] = "v2.x"

                else:
                    result["status"] = "unhealthy"
                    result["error"] = "Invalid response structure (no 'links' found)"

            elif response.status_code == 404:
                result["status"] = "not_found"
                result["error"] = "Service not found (404) - may be deprecated"

            elif response.status_code >= 500:
                result["status"] = "server_error"
                result["error"] = f"Server error ({response.status_code})"

            else:
                result["status"] = "unhealthy"
                result["error"] = f"Unexpected status code: {response.status_code}"

        except httpx.TimeoutException:
            result["status"] = "timeout"
            result["error"] = f"Request timeout after {self.timeout}s"

        except httpx.ConnectError:
            result["status"] = "connection_error"
            result["error"] = "Cannot connect to service"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def check_all_services(self) -> dict:
        """Check health of all registered PDOK services.

        Uses parallel async requests for fast checking.

        Returns:
            Health check results for all services
        """
        print(f"Checking {len(PDOK_SERVICES)} PDOK services...")

        # Check all services in parallel with asyncio.gather
        tasks = []
        service_ids = []

        for service_id, service_info in PDOK_SERVICES.items():
            tasks.append(self.check_service_health(service_id, service_info))
            service_ids.append(service_id)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for service_id, result in zip(service_ids, results, strict=False):
            print(f"  {service_id}...", end=" ")

            if isinstance(result, Exception):
                result = {
                    "service_id": service_id,
                    "status": "error",
                    "error": str(result),
                }

            if result["status"] == "healthy":
                self.results["healthy"].append(result)
                print(f"✓ OK ({result['collections_found']} collections)")

            elif result["status"] == "not_found":
                self.results["unhealthy"].append(result)
                print("✗ NOT FOUND - may be deprecated!")

            elif result["status"] == "timeout":
                self.results["warnings"].append(result)
                print("⚠ TIMEOUT")

            else:
                self.results["unhealthy"].append(result)
                print(f"✗ UNHEALTHY: {result['error']}")

        return self.results

    def discover_new_services(self) -> list[dict]:
        """Discover new PDOK services not in our index.

        Returns:
            List of newly discovered services
        """
        discovered = []

        print("\nDiscovering new PDOK services...")

        # PDOK main API catalog
        catalog_urls = [
            "https://api.pdok.nl",
            "https://api.pdok.nl/lv",
            "https://api.pdok.nl/cbs",
            "https://api.pdok.nl/rws",
            "https://api.pdok.nl/kadaster",
        ]

        known_urls = {svc["url"] for svc in PDOK_SERVICES.values()}

        for catalog_url in catalog_urls:
            try:
                print(f"  Checking {catalog_url}...")
                with httpx.Client() as client:
                    response = client.get(catalog_url, timeout=self.timeout)

                    if response.status_code == 200:
                        # Try to parse as HTML and find API links
                        # (text variable not used - just checking status)

                        # Look for OGC API patterns in HTML
                        import re

                        ogc_pattern = r'https://api\.pdok\.nl/[^"\'>\s]+/ogc/v[^"\'>\s]*'
                        matches = re.findall(ogc_pattern, response.text, re.IGNORECASE)

                        for match in matches:
                            # Normalize URL (add trailing slash)
                            url = match if match.endswith("/") else match + "/"

                            if url not in known_urls:
                                # Found new service!
                                discovered.append(
                                    {
                                        "url": url,
                                        "found_in": catalog_url,
                                        "status": "discovered",
                                    }
                                )
                                known_urls.add(url)

            except Exception as e:
                print(f"    ⚠ Error checking {catalog_url}: {e}")

        self.results["discovered"] = discovered

        if discovered:
            print(f"\n✓ Found {len(discovered)} new services!")
        else:
            print("\n  No new services found.")

        return discovered

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate human-readable health report.

        Args:
            output_path: Optional path to save report

        Returns:
            Report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("PDOK SERVICE INDEX HEALTH REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.results['timestamp']}")
        lines.append(f"Total Services: {self.results['total_services']}")
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"  Healthy:    {len(self.results['healthy'])} services")
        lines.append(f"  Unhealthy:  {len(self.results['unhealthy'])} services")
        lines.append(f"  Warnings:   {len(self.results['warnings'])} services")
        lines.append(f"  Discovered: {len(self.results['discovered'])} new services")
        lines.append("")

        # Unhealthy services (critical)
        if self.results["unhealthy"]:
            lines.append("UNHEALTHY SERVICES (ACTION REQUIRED)")
            lines.append("-" * 80)
            for svc in self.results["unhealthy"]:
                lines.append(f"  ✗ {svc['service_id']}")
                lines.append(f"    URL:    {svc['url']}")
                lines.append(f"    Status: {svc['status']}")
                lines.append(f"    Error:  {svc['error']}")

                if svc["status"] == "not_found":
                    lines.append("    ⚠ ACTION: Service may be deprecated - check PDOK.nl")
                lines.append("")

        # Warnings
        if self.results["warnings"]:
            lines.append("WARNINGS")
            lines.append("-" * 80)
            for svc in self.results["warnings"]:
                lines.append(f"  ⚠ {svc['service_id']}: {svc['error']}")
            lines.append("")

        # Discovered services
        if self.results["discovered"]:
            lines.append("NEW SERVICES DISCOVERED")
            lines.append("-" * 80)
            lines.append("  Consider adding these to PDOK_SERVICES:")
            lines.append("")
            for svc in self.results["discovered"]:
                lines.append(f"  • {svc['url']}")
            lines.append("")

        # Healthy services (summary)
        if self.results["healthy"]:
            lines.append(f"HEALTHY SERVICES ({len(self.results['healthy'])})")
            lines.append("-" * 80)

            # Group by category
            by_category = {}
            for svc in self.results["healthy"]:
                service_id = svc["service_id"]
                service_info = PDOK_SERVICES.get(service_id, {})
                category = service_info.get("category", "unknown")

                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(svc)

            for category, services in sorted(by_category.items()):
                lines.append(f"  {category.replace('_', ' ').title()}: {len(services)} services")
            lines.append("")

        lines.append("=" * 80)

        report = "\n".join(lines)

        # Save to file if requested
        if output_path:
            output_path.write_text(report)
            print(f"\n✓ Report saved to: {output_path}")

        return report


def check_service_health(service_id: str) -> dict:
    """Quick health check for a single service.

    Args:
        service_id: Service ID from PDOK_SERVICES

    Returns:
        Health check result

    Example:
        >>> result = check_service_health("bgt")
        >>> print(result["status"])
        healthy
    """
    if service_id not in PDOK_SERVICES:
        return {"status": "error", "error": f"Unknown service: {service_id}"}

    monitor = PDOKServiceMonitor()
    return monitor.check_service_health(service_id, PDOK_SERVICES[service_id])


def discover_services() -> list[dict]:
    """Discover new PDOK services.

    Returns:
        List of discovered services

    Example:
        >>> new_services = discover_services()
        >>> for svc in new_services:
        ...     print(svc["url"])
    """
    monitor = PDOKServiceMonitor()
    return monitor.discover_new_services()
