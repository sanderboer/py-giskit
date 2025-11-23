"""Unit tests for Protocol Quirks system."""


from giskit.protocols.quirks import KNOWN_QUIRKS, ProtocolQuirks, get_format_quirks, get_quirks


class TestProtocolQuirks:
    """Test ProtocolQuirks configuration and application."""

    def test_default_quirks_no_modifications(self):
        """Test default quirks don't modify anything."""
        quirks = ProtocolQuirks()

        # URL shouldn't change
        assert quirks.apply_to_url("https://example.com/api") == "https://example.com/api"

        # Params shouldn't change
        params = {"bbox": "1,2,3,4", "limit": 100}
        assert quirks.apply_to_params(params) == params

        # Headers shouldn't change
        headers = {"Accept": "application/json"}
        assert quirks.apply_to_headers(headers) == headers

        # Timeout should return default
        assert quirks.get_timeout(30.0) == 30.0

    def test_trailing_slash_quirk(self):
        """Test trailing slash addition to URLs."""
        quirks = ProtocolQuirks(requires_trailing_slash=True)

        # Should add trailing slash
        assert quirks.apply_to_url("https://example.com/api") == "https://example.com/api/"

        # Should not duplicate if already present
        assert quirks.apply_to_url("https://example.com/api/") == "https://example.com/api/"

    def test_format_param_quirk(self):
        """Test format parameter addition."""
        quirks = ProtocolQuirks(
            require_format_param=True, format_param_name="f", format_param_value="json"
        )

        params = {"bbox": "1,2,3,4"}
        result = quirks.apply_to_params(params)

        assert result["f"] == "json"
        assert result["bbox"] == "1,2,3,4"  # Original preserved

    def test_max_features_limit_quirk(self):
        """Test max features limit enforcement."""
        quirks = ProtocolQuirks(max_features_limit=5000)

        # Should cap to 5000
        params = {"limit": 10000}
        result = quirks.apply_to_params(params)
        assert result["limit"] == 5000

        # Should allow lower limits
        params = {"limit": 1000}
        result = quirks.apply_to_params(params)
        assert result["limit"] == 1000

    def test_custom_timeout_quirk(self):
        """Test custom timeout override."""
        quirks = ProtocolQuirks(custom_timeout=60.0)

        # Should override default
        assert quirks.get_timeout(30.0) == 60.0

    def test_custom_headers_quirk(self):
        """Test custom header addition."""
        quirks = ProtocolQuirks(custom_headers={"X-API-Key": "secret123"})

        headers = {"Accept": "application/json"}
        result = quirks.apply_to_headers(headers)

        assert result["X-API-Key"] == "secret123"
        assert result["Accept"] == "application/json"

    def test_combined_quirks(self):
        """Test multiple quirks applied together."""
        quirks = ProtocolQuirks(
            requires_trailing_slash=True,
            require_format_param=True,
            format_param_name="f",
            format_param_value="geojson",
            max_features_limit=1000,
            custom_timeout=45.0,
            custom_headers={"User-Agent": "GISKit/1.0"},
        )

        # URL
        url = quirks.apply_to_url("https://api.example.com/v1")
        assert url == "https://api.example.com/v1/"

        # Params
        params = quirks.apply_to_params({"bbox": "1,2,3,4", "limit": 5000})
        assert params["f"] == "geojson"
        assert params["limit"] == 1000  # Capped

        # Headers
        headers = quirks.apply_to_headers({})
        assert headers["User-Agent"] == "GISKit/1.0"

        # Timeout
        assert quirks.get_timeout(30.0) == 45.0


class TestKnownQuirks:
    """Test known quirks registry."""

    def test_pdok_quirks_registered(self):
        """Test PDOK quirks are registered."""
        assert "pdok" in KNOWN_QUIRKS
        assert "ogc-features" in KNOWN_QUIRKS["pdok"]

    def test_pdok_ogc_quirks_configuration(self):
        """Test PDOK OGC Features quirks are correctly configured."""
        quirks = KNOWN_QUIRKS["pdok"]["ogc-features"]

        # Should have trailing slash requirement
        assert quirks.requires_trailing_slash is True

        # Should require f=json parameter
        assert quirks.require_format_param is True
        assert quirks.format_param_name == "f"
        assert quirks.format_param_value == "json"

        # Should have metadata
        assert quirks.description is not None
        assert "PDOK" in quirks.description
        assert quirks.workaround_date is not None

    def test_get_quirks_pdok(self):
        """Test get_quirks() function for PDOK."""
        quirks = get_quirks("pdok", "ogc-features")

        assert isinstance(quirks, ProtocolQuirks)
        assert quirks.require_format_param is True

    def test_get_quirks_unknown_provider(self):
        """Test get_quirks() returns default for unknown provider."""
        quirks = get_quirks("unknown-provider", "ogc-features")

        # Should return default quirks (no modifications)
        assert isinstance(quirks, ProtocolQuirks)
        assert quirks.require_format_param is False
        assert quirks.requires_trailing_slash is False

    def test_get_quirks_unknown_protocol(self):
        """Test get_quirks() returns default for unknown protocol."""
        quirks = get_quirks("pdok", "unknown-protocol")

        # Should return default quirks
        assert isinstance(quirks, ProtocolQuirks)
        assert quirks.require_format_param is False


class TestQuirksDocumentation:
    """Test quirks documentation features."""

    def test_quirks_with_metadata(self):
        """Test quirks can store metadata."""
        quirks = ProtocolQuirks(
            description="API requires special header",
            issue_url="https://github.com/provider/issues/123",
            workaround_date="2024-11-22",
        )

        assert quirks.description == "API requires special header"
        assert quirks.issue_url == "https://github.com/provider/issues/123"
        assert quirks.workaround_date == "2024-11-22"

    def test_pdok_quirks_documented(self):
        """Test PDOK quirks have proper documentation."""
        quirks = get_quirks("pdok", "ogc-features")

        # Should have description
        assert quirks.description is not None
        assert len(quirks.description) > 10

        # Should explain the quirk
        assert "json" in quirks.description.lower() or "f=" in quirks.description

    def test_quirks_can_reference_issues(self):
        """Test quirks can link to issue trackers."""
        quirks = get_quirks("pdok", "ogc-features")

        # May or may not have issue URL (optional)
        if quirks.issue_url:
            assert quirks.issue_url.startswith("http")


class TestQuirksInProtocol:
    """Test quirks integration with Protocol class."""

    def test_protocol_accepts_quirks(self):
        """Test OGCFeaturesProtocol accepts quirks parameter."""
        from giskit.protocols.ogc_features import OGCFeaturesProtocol

        quirks = ProtocolQuirks(requires_trailing_slash=True)
        protocol = OGCFeaturesProtocol(base_url="https://example.com/api", quirks=quirks)

        # Base URL should have trailing slash applied
        assert protocol.base_url.endswith("/")

    def test_protocol_applies_url_quirks_on_init(self):
        """Test protocol applies URL quirks during initialization."""
        from giskit.protocols.ogc_features import OGCFeaturesProtocol

        quirks = ProtocolQuirks(requires_trailing_slash=True)
        protocol = OGCFeaturesProtocol(base_url="https://example.com/api/v1", quirks=quirks)

        assert protocol.base_url == "https://example.com/api/v1/"

    def test_protocol_without_quirks_uses_defaults(self):
        """Test protocol works without quirks (uses defaults)."""
        from giskit.protocols.ogc_features import OGCFeaturesProtocol

        protocol = OGCFeaturesProtocol(base_url="https://example.com/api")

        # Should have default quirks
        assert isinstance(protocol.quirks, ProtocolQuirks)
        assert protocol.quirks.require_format_param is False


class TestQuirksRealWorld:
    """Test quirks with real-world scenarios."""

    def test_pdok_url_construction(self):
        """Test PDOK quirks fix urljoin issue."""
        quirks = get_quirks("pdok", "ogc-features")

        # Simulate PDOK URL
        base_url = "https://api.pdok.nl/lv/bgt/ogc/v1_0"
        fixed_url = quirks.apply_to_url(base_url)

        # Should have trailing slash
        assert fixed_url == "https://api.pdok.nl/lv/bgt/ogc/v1_0/"

        # Now urljoin should work correctly
        from urllib.parse import urljoin

        result = urljoin(fixed_url, "collections")
        assert result == "https://api.pdok.nl/lv/bgt/ogc/v1_0/collections"

    def test_pdok_request_params(self):
        """Test PDOK quirks add required parameters."""
        quirks = get_quirks("pdok", "ogc-features")

        # Original params
        params = {"bbox": "4.0,52.0,5.0,53.0", "limit": 1000}

        # Apply quirks
        result = quirks.apply_to_params(params)

        # Should add f=json
        assert result["f"] == "json"
        # Should preserve original params
        assert result["bbox"] == "4.0,52.0,5.0,53.0"
        assert result["limit"] == 1000


class TestCityJSONFormatQuirks:
    """Test CityJSON format quirks (BAG3D, 3D-basisvoorziening, etc.)."""

    def test_cityjson_format_quirks_registered(self):
        """Test CityJSON format quirks are in registry."""
        assert "cityjson" in KNOWN_QUIRKS
        assert "format" in KNOWN_QUIRKS["cityjson"]

    def test_cityjson_format_flags(self):
        """Test CityJSON format quirks have correct flags set."""
        quirks = get_quirks("cityjson", "format")

        # Format identification
        assert quirks.format_is_cityjson is True
        assert quirks.cityjson_version == "2.0"
        assert quirks.geometry_in_city_objects is True
        assert quirks.has_lod_hierarchy is True

        # CRITICAL: Transform quirks
        assert quirks.has_per_page_transform is True, "CRITICAL: Missing per-page transform warning"
        assert quirks.transform_applies_to_vertices is True
        assert quirks.vertices_are_integers is True

    def test_cityjson_quirks_timeout(self):
        """Test CityJSON format has longer timeout for 3D data."""
        quirks = get_quirks("cityjson", "format")
        assert quirks.custom_timeout == 60.0
        assert quirks.get_timeout(30.0) == 60.0  # Overrides default

    def test_cityjson_quirks_documentation(self):
        """Test CityJSON quirks have critical documentation."""
        quirks = get_quirks("cityjson", "format")

        # Must have description
        assert quirks.description is not None
        assert len(quirks.description) > 50

        # Must mention the critical transform issue
        assert "CRITICAL" in quirks.description
        assert "transform" in quirks.description.lower()
        assert "page" in quirks.description.lower()

        # Must have link to spec or docs
        assert quirks.issue_url is not None
        assert "cityjson" in quirks.issue_url.lower()

    def test_get_format_quirks_helper(self):
        """Test get_format_quirks() convenience function."""
        from giskit.protocols.quirks import get_format_quirks

        quirks = get_format_quirks("cityjson")
        assert quirks.format_is_cityjson is True
        assert quirks.has_per_page_transform is True

    def test_bag3d_inherits_cityjson_quirks(self):
        """Test BAG3D service has CityJSON format quirks."""
        quirks = get_quirks("bag3d", "ogc-features")

        # Should have all CityJSON format flags
        assert quirks.format_is_cityjson is True
        assert quirks.has_per_page_transform is True
        assert quirks.transform_applies_to_vertices is True
        assert quirks.vertices_are_integers is True
        assert quirks.geometry_in_city_objects is True
        assert quirks.has_lod_hierarchy is True

    def test_bag3d_quirks_reference_cityjson(self):
        """Test BAG3D quirks documentation references CityJSON format."""
        quirks = get_quirks("bag3d", "ogc-features")

        # Should mention CityJSON in description
        assert quirks.description is not None
        assert "cityjson" in quirks.description.lower()

    def test_cityjson_transform_warning_critical(self):
        """Test that per-page transform quirk is marked as CRITICAL."""
        quirks = get_format_quirks("cityjson")

        # This is the bug that caused production issues in Sitedb!
        assert quirks.has_per_page_transform is True, (
            "CRITICAL QUIRK MISSING! Each pagination page has different transform. "
            "See Sitedb bag3d_downloader.py:87-100 for the fix that was needed."
        )

        # Verify description warns about coordinate errors
        assert "coordinate" in quirks.description.lower() or "coord" in quirks.description.lower()


class TestServiceFormatMetadata:
    """Test services correctly identify their format."""

    def test_pdok_services_have_format_metadata(self):
        """Test 3D services in PDOK provider specify CityJSON format."""
        from giskit.providers.pdok import PDOK_SERVICES

        # These services should have format="cityjson"
        cityjson_services = ["bag3d", "3d-basisvoorziening", "3d-geluid"]

        for service_id in cityjson_services:
            if service_id in PDOK_SERVICES:
                service = PDOK_SERVICES[service_id]
                assert (
                    service.get("format") == "cityjson"
                ), f"Service {service_id} uses CityJSON but format not specified"

    def test_non_3d_services_no_cityjson_format(self):
        """Test regular 2D services don't have CityJSON format."""
        from giskit.providers.pdok import PDOK_SERVICES

        # These 2D services should NOT have format="cityjson"
        regular_services = ["bgt", "bag", "brk"]

        for service_id in regular_services:
            if service_id in PDOK_SERVICES:
                service = PDOK_SERVICES[service_id]
                assert (
                    service.get("format") != "cityjson"
                ), f"Service {service_id} is 2D but marked as CityJSON"
