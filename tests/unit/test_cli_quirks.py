"""Tests for CLI quirks commands."""

import pytest
from click.testing import CliRunner

from giskit.cli.main import cli as app
from giskit.protocols.quirks_monitor import get_monitor

runner = CliRunner()


class TestQuirksListCommand:
    """Test 'giskit quirks list' command."""

    def test_quirks_list_shows_pdok(self):
        """Test that quirks list shows PDOK quirks."""
        result = runner.invoke(app, ["quirks", "list"])

        assert result.exit_code == 0
        assert "pdok" in result.stdout.lower()
        assert "ogc-features" in result.stdout.lower()

    def test_quirks_list_shows_known_quirks(self):
        """Test that quirks list shows known quirk types."""
        result = runner.invoke(app, ["quirks", "list"])

        assert result.exit_code == 0
        # Should show quirk types
        assert "trailing" in result.stdout.lower() or "slash" in result.stdout.lower()
        assert "format" in result.stdout.lower()

    def test_quirks_list_readable_format(self):
        """Test quirks list readable format."""
        result = runner.invoke(app, ["quirks", "list"])

        assert result.exit_code == 0
        # Should show table-like output
        assert "provider" in result.stdout.lower() or "pdok" in result.stdout.lower()


class TestQuirksShowCommand:
    """Test 'giskit quirks show' command."""

    def test_quirks_show_pdok_ogc(self):
        """Test showing PDOK OGC-Features quirks."""
        result = runner.invoke(app, ["quirks", "show", "pdok", "ogc-features"])

        assert result.exit_code == 0
        assert "pdok" in result.stdout.lower()
        assert "ogc-features" in result.stdout.lower()

        # Should show quirk details
        assert "trailing" in result.stdout.lower() or "slash" in result.stdout.lower()
        assert "format" in result.stdout.lower()

    def test_quirks_show_unknown_provider(self):
        """Test showing quirks for unknown provider."""
        result = runner.invoke(app, ["quirks", "show", "unknown", "protocol"])

        # Should exit gracefully and show defaults
        assert result.exit_code == 0
        assert "using defaults" in result.stdout.lower()

    def test_quirks_show_known_provider_unknown_protocol(self):
        """Test showing quirks for known provider but unknown protocol."""
        result = runner.invoke(app, ["quirks", "show", "pdok", "unknown-protocol"])

        # Should exit gracefully and show defaults
        assert result.exit_code == 0
        assert "using defaults" in result.stdout.lower()

    def test_quirks_show_details(self):
        """Test quirks show displays detailed information."""
        result = runner.invoke(app, ["quirks", "show", "pdok", "ogc-features"])

        assert result.exit_code == 0
        # Should show quirk configuration details
        assert "trailing_slash" in result.stdout.lower() or "slash" in result.stdout.lower()
        assert "format" in result.stdout.lower()
        assert "true" in result.stdout.lower()  # Should show True for enabled quirks


class TestQuirksMonitorCommand:
    """Test 'giskit quirks monitor' command."""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset global monitor before each test."""
        monitor = get_monitor()
        monitor.reset()
        yield

    def test_quirks_monitor_empty(self):
        """Test monitor command with no data."""
        result = runner.invoke(app, ["quirks", "monitor"])

        assert result.exit_code == 0
        assert "no quirks" in result.stdout.lower()

    def test_quirks_monitor_with_data(self):
        """Test monitor command with data."""
        # Record some quirks
        monitor = get_monitor()
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "ogc-features", "trailing_slash")

        result = runner.invoke(app, ["quirks", "monitor"])

        assert result.exit_code == 0
        assert "QUIRKS USAGE REPORT" in result.stdout
        assert "pdok" in result.stdout.lower()
        assert "format_param" in result.stdout.lower()
        assert "2 times" in result.stdout  # format_param applied twice

    def test_quirks_monitor_shows_top_quirks(self):
        """Test that monitor shows top quirks."""
        # Record different quirks with different counts
        monitor = get_monitor()
        for _ in range(10):
            monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        for _ in range(5):
            monitor.record_quirk_applied("pdok", "ogc-features", "trailing_slash")
        for _ in range(15):
            monitor.record_quirk_applied("osm", "overpass", "timeout")

        result = runner.invoke(app, ["quirks", "monitor"])

        assert result.exit_code == 0
        assert "Top" in result.stdout
        # Should show the most used quirk
        assert "timeout" in result.stdout.lower()
        assert "15 times" in result.stdout


class TestQuirksCommandIntegration:
    """Integration tests for quirks commands."""

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset global monitor before each test."""
        monitor = get_monitor()
        monitor.reset()
        yield

    def test_workflow_list_show_monitor(self):
        """Test workflow: list quirks, show details, check monitor."""
        # 1. List quirks
        result = runner.invoke(app, ["quirks", "list"])
        assert result.exit_code == 0
        assert "pdok" in result.stdout.lower()

        # 2. Show specific quirks
        result = runner.invoke(app, ["quirks", "show", "pdok", "ogc-features"])
        assert result.exit_code == 0
        assert "pdok" in result.stdout.lower()

        # 3. Check monitor (should be empty)
        result = runner.invoke(app, ["quirks", "monitor"])
        assert result.exit_code == 0
        assert "no quirks" in result.stdout.lower()

    def test_monitor_after_quirk_application(self):
        """Test that monitor shows data after quirks are applied."""
        # Apply some quirks
        monitor = get_monitor()
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")

        # Check monitor
        result = runner.invoke(app, ["quirks", "monitor"])
        assert result.exit_code == 0
        assert "QUIRKS USAGE REPORT" in result.stdout
        assert "format_param" in result.stdout.lower()
