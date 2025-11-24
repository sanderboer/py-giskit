"""Integration tests for Klimaateffectatlas climate data integration.

Tests the Klimaateffectatlas provider configuration and service availability.
Full data retrieval tests are covered in the quirks monitor and recipe executor.

These tests use the Amsterdam area as test region.
"""

import pytest

from giskit.catalog import list_all_services  # type: ignore
from giskit.providers.base import get_provider


class TestKlimaateffectatlasConfiguration:
    """Test Klimaateffectatlas provider configuration."""

    @pytest.mark.integration
    def test_provider_loads(self):
        """Test that klimaateffectatlas provider can be loaded."""
        provider = get_provider("klimaateffectatlas")
        assert provider is not None
        assert provider.name == "klimaateffectatlas"

    @pytest.mark.integration
    def test_provider_has_26_services(self):
        """Test that all 26 climate services are configured."""
        catalog = list_all_services()
        kea = catalog.get("klimaateffectatlas", {})

        assert kea.get("service_count") == 26
        assert "wfs" in kea.get("protocols", [])

    @pytest.mark.integration
    def test_heat_stress_services_available(self):
        """Test heat stress services are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        heat_services = [
            "sociale-kwetsbaarheid-hitte",
            "gevoelstemperatuur-buurt",
            "hitteeiland-effect",
            "afstand-tot-koelte",
            "schaduwkaart-fiets-wandelpaden",
            "eenzame-75plussers",
        ]

        for service in heat_services:
            assert service in kea_services, f"Missing heat service: {service}"
            assert kea_services[service]["protocol"] == "wfs"

    @pytest.mark.integration
    def test_flooding_services_available(self):
        """Test flooding risk services are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        flood_services = [
            "dagen-15mm-huidig",
            "dagen-15mm-2050-hoog",
            "dagen-25mm-huidig",
            "dagen-25mm-2050-laag",
            "kans-grondwateroverlast-2050-hoog",
            "droge-plekken-extreem-kleine-kans",
            "droge-verdiepingen-extreem-kleine-kans",
        ]

        for service in flood_services:
            assert service in kea_services, f"Missing flood service: {service}"
            assert kea_services[service]["protocol"] == "wfs"

    @pytest.mark.integration
    def test_drought_services_available(self):
        """Test drought risk services are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        drought_services = [
            "neerslagtekort-10j-huidig",
            "neerslagtekort-10j-2050-hoog",
            "droogtegevoeligheid-natuur",
            "oppervlaktewaterverzilting-3m",
        ]

        for service in drought_services:
            assert service in kea_services, f"Missing drought service: {service}"
            assert kea_services[service]["protocol"] == "wfs"

    @pytest.mark.integration
    def test_scenario_comparison_services_available(self):
        """Test current vs 2050 scenario pairs are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        scenario_pairs = [
            ("dagen-15mm-huidig", "dagen-15mm-2050-hoog"),
            ("dagen-25mm-huidig", "dagen-25mm-2050-laag"),
            ("neerslagtekort-10j-huidig", "neerslagtekort-10j-2050-hoog"),
            ("neerslag-jaar-huidig", "neerslag-jaar-2050-hoog"),
            ("ijsdagen-huidig", "ijsdagen-2050-hoog"),
        ]

        for current, future in scenario_pairs:
            assert current in kea_services, f"Missing current scenario: {current}"
            assert future in kea_services, f"Missing future scenario: {future}"

    @pytest.mark.integration
    def test_urban_characteristics_services_available(self):
        """Test urban characteristic services are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        urban_services = [
            "groen-per-buurt",
            "grijs-per-buurt",
            "water-per-buurt",
            "gemeentegrenzen-klimaat",
        ]

        for service in urban_services:
            assert service in kea_services, f"Missing urban service: {service}"

    @pytest.mark.integration
    def test_nature_biodiversity_services_available(self):
        """Test nature and biodiversity services are configured."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        nature_services = [
            "bkns-dreigingen-kansen",
            "droogtegevoeligheid-natuur",
        ]

        for service in nature_services:
            assert service in kea_services, f"Missing nature service: {service}"


class TestKlimaateffectatlasServiceMetadata:
    """Test service metadata quality."""

    @pytest.mark.integration
    def test_all_services_have_titles(self):
        """Test all services have descriptive titles."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        for service_id, service_data in kea_services.items():
            assert "title" in service_data, f"Service {service_id} missing title"
            assert len(service_data["title"]) > 10, f"Service {service_id} title too short"

    @pytest.mark.integration
    def test_all_services_have_descriptions(self):
        """Test all services have descriptions."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        for service_id, service_data in kea_services.items():
            assert "description" in service_data, f"Service {service_id} missing description"
            assert (
                len(service_data["description"]) > 20
            ), f"Service {service_id} description too short"

    @pytest.mark.integration
    def test_all_services_have_keywords(self):
        """Test all services have relevant keywords."""
        catalog = list_all_services(detailed=True)
        kea_services = catalog.get("klimaateffectatlas", {}).get("services", {})

        for service_id, service_data in kea_services.items():
            assert "keywords" in service_data, f"Service {service_id} missing keywords"
            assert len(service_data["keywords"]) >= 3, f"Service {service_id} needs more keywords"
            # All services should have 'klimaat' keyword
            assert (
                "klimaat" in service_data["keywords"]
            ), f"Service {service_id} missing 'klimaat' keyword"
