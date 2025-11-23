"""Tests for quirks monitoring system."""

from datetime import datetime

import pytest

from giskit.protocols.quirks import ProtocolQuirks
from giskit.protocols.quirks_monitor import (
    QuirksMonitor,
    QuirkUsage,
    get_monitor,
    log_quirk_application,
)


class TestQuirkUsage:
    """Test QuirkUsage dataclass."""

    def test_initial_state(self):
        """Test initial state of QuirkUsage."""
        usage = QuirkUsage(provider="pdok", protocol="ogc-features", quirk_type="format_param")

        assert usage.provider == "pdok"
        assert usage.protocol == "ogc-features"
        assert usage.quirk_type == "format_param"
        assert usage.applied_count == 0
        assert usage.first_applied is None
        assert usage.last_applied is None

    def test_record_first_application(self):
        """Test recording the first application."""
        usage = QuirkUsage(provider="pdok", protocol="ogc-features", quirk_type="format_param")

        before = datetime.now()
        usage.record_application()
        after = datetime.now()

        assert usage.applied_count == 1
        assert usage.first_applied is not None
        assert usage.last_applied is not None
        assert before <= usage.first_applied <= after
        assert before <= usage.last_applied <= after
        assert usage.first_applied == usage.last_applied

    def test_record_multiple_applications(self):
        """Test recording multiple applications."""
        usage = QuirkUsage(provider="pdok", protocol="ogc-features", quirk_type="format_param")

        # First application
        usage.record_application()
        first_time = usage.first_applied

        # Second application (simulate delay)
        import time

        time.sleep(0.01)
        usage.record_application()

        assert usage.applied_count == 2
        assert usage.first_applied == first_time  # Should not change
        assert usage.last_applied > usage.first_applied

    def test_multiple_applications_increment_count(self):
        """Test that count increments correctly."""
        usage = QuirkUsage(provider="test", protocol="test-protocol", quirk_type="test_quirk")

        for _i in range(10):
            usage.record_application()

        assert usage.applied_count == 10


class TestQuirksMonitor:
    """Test QuirksMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor for each test."""
        mon = QuirksMonitor()
        mon.reset()
        return mon

    def test_initial_state(self, monitor):
        """Test initial state of monitor."""
        assert monitor._enabled is True
        stats = monitor.get_statistics()
        assert stats == {}

    def test_record_single_quirk(self, monitor):
        """Test recording a single quirk application."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")

        stats = monitor.get_statistics()
        assert "pdok" in stats
        assert "ogc-features" in stats["pdok"]
        assert "format_param" in stats["pdok"]["ogc-features"]

        usage = stats["pdok"]["ogc-features"]["format_param"]
        assert usage.provider == "pdok"
        assert usage.protocol == "ogc-features"
        assert usage.quirk_type == "format_param"
        assert usage.applied_count == 1

    def test_record_multiple_quirks_same_type(self, monitor):
        """Test recording same quirk multiple times."""
        for _ in range(5):
            monitor.record_quirk_applied("pdok", "ogc-features", "format_param")

        stats = monitor.get_statistics()
        usage = stats["pdok"]["ogc-features"]["format_param"]
        assert usage.applied_count == 5

    def test_record_different_quirk_types(self, monitor):
        """Test recording different quirk types."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "ogc-features", "trailing_slash")
        monitor.record_quirk_applied("pdok", "ogc-features", "max_features_limit")

        stats = monitor.get_statistics()
        assert len(stats["pdok"]["ogc-features"]) == 3
        assert stats["pdok"]["ogc-features"]["format_param"].applied_count == 1
        assert stats["pdok"]["ogc-features"]["trailing_slash"].applied_count == 1
        assert stats["pdok"]["ogc-features"]["max_features_limit"].applied_count == 1

    def test_record_different_providers(self, monitor):
        """Test recording quirks for different providers."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("osm", "overpass", "timeout")

        stats = monitor.get_statistics()
        assert "pdok" in stats
        assert "osm" in stats
        assert "ogc-features" in stats["pdok"]
        assert "overpass" in stats["osm"]

    def test_get_provider_stats(self, monitor):
        """Test getting stats for specific provider."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "wfs", "version_override")
        monitor.record_quirk_applied("osm", "overpass", "timeout")

        pdok_stats = monitor.get_provider_stats("pdok")
        assert "ogc-features" in pdok_stats
        assert "wfs" in pdok_stats
        assert "overpass" not in pdok_stats

        osm_stats = monitor.get_provider_stats("osm")
        assert "overpass" in osm_stats
        assert "ogc-features" not in osm_stats

    def test_get_provider_stats_nonexistent(self, monitor):
        """Test getting stats for non-existent provider."""
        stats = monitor.get_provider_stats("nonexistent")
        assert stats == {}

    def test_get_most_used_quirks(self, monitor):
        """Test getting most used quirks."""
        # Apply different quirks with different counts
        for _ in range(10):
            monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        for _ in range(5):
            monitor.record_quirk_applied("pdok", "ogc-features", "trailing_slash")
        for _ in range(15):
            monitor.record_quirk_applied("osm", "overpass", "timeout")
        for _ in range(3):
            monitor.record_quirk_applied("osm", "overpass", "custom_headers")

        most_used = monitor.get_most_used_quirks(limit=3)

        assert len(most_used) == 3
        # Should be sorted by count (descending)
        assert most_used[0].applied_count == 15  # osm/overpass/timeout
        assert most_used[1].applied_count == 10  # pdok/ogc-features/format_param
        assert most_used[2].applied_count == 5  # pdok/ogc-features/trailing_slash

    def test_get_most_used_quirks_empty(self, monitor):
        """Test getting most used quirks when none exist."""
        most_used = monitor.get_most_used_quirks()
        assert most_used == []

    def test_get_most_used_quirks_limit(self, monitor):
        """Test limit parameter of get_most_used_quirks."""
        # Create 10 different quirks
        for i in range(10):
            monitor.record_quirk_applied("provider", f"protocol_{i}", "quirk")

        most_used = monitor.get_most_used_quirks(limit=5)
        assert len(most_used) == 5

        most_used = monitor.get_most_used_quirks(limit=3)
        assert len(most_used) == 3

    def test_reset(self, monitor):
        """Test resetting statistics."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("osm", "overpass", "timeout")

        stats_before = monitor.get_statistics()
        assert len(stats_before) == 2

        monitor.reset()

        stats_after = monitor.get_statistics()
        assert stats_after == {}

    def test_disable_enable(self, monitor):
        """Test disabling and enabling monitoring."""
        # Record while enabled
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        assert monitor.get_statistics()["pdok"]["ogc-features"]["format_param"].applied_count == 1

        # Disable and try to record
        monitor.disable()
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        # Count should not change
        assert monitor.get_statistics()["pdok"]["ogc-features"]["format_param"].applied_count == 1

        # Enable and record again
        monitor.enable()
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        assert monitor.get_statistics()["pdok"]["ogc-features"]["format_param"].applied_count == 2

    def test_print_report_empty(self, monitor, capsys):
        """Test print_report with no data."""
        monitor.print_report()
        captured = capsys.readouterr()
        assert "QUIRKS USAGE REPORT" in captured.out
        assert "No quirks have been applied yet" in captured.out

    def test_print_report_with_data(self, monitor, capsys):
        """Test print_report with data."""
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("osm", "overpass", "timeout")

        monitor.print_report()
        captured = capsys.readouterr()

        assert "QUIRKS USAGE REPORT" in captured.out
        assert "Provider: pdok" in captured.out
        assert "Protocol: ogc-features" in captured.out
        assert "format_param:" in captured.out
        assert "Applied: 2 times" in captured.out
        assert "Top 5 Most Used Quirks:" in captured.out


class TestGlobalMonitor:
    """Test global monitor instance."""

    def test_get_monitor_returns_same_instance(self):
        """Test that get_monitor() returns the same instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        assert monitor1 is monitor2

    def test_global_monitor_persistence(self):
        """Test that global monitor persists data."""
        monitor = get_monitor()
        monitor.reset()  # Clean slate

        monitor.record_quirk_applied("test", "test", "test")

        # Get monitor again and check data is still there
        monitor2 = get_monitor()
        stats = monitor2.get_statistics()
        assert "test" in stats


class TestLogQuirkApplication:
    """Test log_quirk_application helper function."""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset global monitor before each test."""
        monitor = get_monitor()
        monitor.reset()
        yield

    def test_log_no_quirks(self):
        """Test logging when no quirks are active."""
        quirks = ProtocolQuirks()
        log_quirk_application(quirks, "pdok", "ogc-features", "get_capabilities")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert stats == {}

    def test_log_trailing_slash(self):
        """Test logging trailing_slash quirk."""
        quirks = ProtocolQuirks(requires_trailing_slash=True)
        log_quirk_application(quirks, "pdok", "ogc-features", "get_capabilities")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "trailing_slash" in stats["pdok"]["ogc-features"]
        assert stats["pdok"]["ogc-features"]["trailing_slash"].applied_count == 1

    def test_log_format_param(self):
        """Test logging format_param quirk."""
        quirks = ProtocolQuirks(
            require_format_param=True, format_param_name="f", format_param_value="json"
        )
        log_quirk_application(quirks, "pdok", "ogc-features", "get_capabilities")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "format_param" in stats["pdok"]["ogc-features"]

    def test_log_max_features_limit(self):
        """Test logging max_features_limit quirk."""
        quirks = ProtocolQuirks(max_features_limit=1000)
        log_quirk_application(quirks, "pdok", "ogc-features", "download")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "max_features_limit" in stats["pdok"]["ogc-features"]

    def test_log_custom_timeout(self):
        """Test logging custom_timeout quirk."""
        quirks = ProtocolQuirks(custom_timeout=120)
        log_quirk_application(quirks, "pdok", "ogc-features", "download")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "custom_timeout" in stats["pdok"]["ogc-features"]

    def test_log_custom_headers(self):
        """Test logging custom_headers quirk."""
        quirks = ProtocolQuirks(custom_headers={"User-Agent": "test"})
        log_quirk_application(quirks, "pdok", "ogc-features", "download")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "custom_headers" in stats["pdok"]["ogc-features"]

    def test_log_multiple_quirks(self):
        """Test logging multiple quirks at once."""
        quirks = ProtocolQuirks(
            requires_trailing_slash=True,
            require_format_param=True,
            format_param_name="f",
            format_param_value="json",
            max_features_limit=1000,
        )
        log_quirk_application(quirks, "pdok", "ogc-features", "download")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert "trailing_slash" in stats["pdok"]["ogc-features"]
        assert "format_param" in stats["pdok"]["ogc-features"]
        assert "max_features_limit" in stats["pdok"]["ogc-features"]

        # Each should have been applied once
        assert stats["pdok"]["ogc-features"]["trailing_slash"].applied_count == 1
        assert stats["pdok"]["ogc-features"]["format_param"].applied_count == 1
        assert stats["pdok"]["ogc-features"]["max_features_limit"].applied_count == 1

    def test_log_multiple_calls(self):
        """Test logging multiple calls increments counts."""
        quirks = ProtocolQuirks(requires_trailing_slash=True)

        # Call 3 times
        for i in range(3):
            log_quirk_application(quirks, "pdok", "ogc-features", f"operation_{i}")

        monitor = get_monitor()
        stats = monitor.get_statistics()
        assert stats["pdok"]["ogc-features"]["trailing_slash"].applied_count == 3
