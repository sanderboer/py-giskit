"""PDOK (Publieke Dienstverlening Op de Kaart) provider implementation.

PDOK is the Dutch national spatial data infrastructure provider.
Provides access to: BGT, BAG, BAG3D, BRK, AHN, and more.

Homepage: https://www.pdok.nl
"""

from pathlib import Path
from typing import Any

import geopandas as gpd

from giskit.core.recipe import Dataset, Location
from giskit.protocols.ogc_features import OGCFeaturesProtocol
from giskit.protocols.quirks import get_quirks, get_service_quirks
from giskit.protocols.wfs import WFSProtocol
from giskit.providers.base import Provider, register_provider

# PDOK OGC API Features endpoints with metadata
# Comprehensive catalog of 89+ PDOK services across 6 categories
# This is the legacy/fallback configuration - prefer loading from config/services/pdok.yml
LEGACY_PDOK_SERVICES = {
    # ===== BASE REGISTERS (Basisregistraties) =====
    # Core Dutch government registers

    "bgt": {
        "url": "https://api.pdok.nl/lv/bgt/ogc/v1_0/",
        "title": "Basisregistratie Grootschalige Topografie",
        "category": "base_registers",
        "description": "Large-scale topography base register with detailed object information",
        "keywords": ["bgt", "topografie", "gebouwen", "wegen", "water"],
    },
    "bag": {
        "url": "https://api.pdok.nl/lv/bag/ogc/v1_0/",
        "title": "Basisregistratie Adressen en Gebouwen",
        "category": "base_registers",
        "description": "National address and building register",
        "keywords": ["bag", "adressen", "gebouwen", "panden", "verblijfsobjecten"],
    },
    "brk": {
        "url": "https://api.pdok.nl/lv/brk/ogc/v1_0/",
        "title": "Basisregistratie Kadaster - Kadastrale Kaart",
        "category": "base_registers",
        "description": "Cadastral map with parcel boundaries",
        "keywords": ["brk", "kadaster", "percelen", "eigendom"],
    },

    # ===== TOPOGRAPHY (Topografie) =====
    # Maps and 3D models

    "3d-basisvoorziening": {
        "url": "https://api.pdok.nl/kadaster/3d-basisvoorziening/ogc/v1",
        "title": "3D Basisvoorziening",
        "category": "topography",
        "description": "3D base map with height information from BGT, BAG, and AHN4",
        "keywords": ["3d", "hoogte", "dtm", "dsm", "ahn4"],
        "format": "cityjson",  # Uses CityJSON format with transform quirks
    },
    "3d-geluid": {
        "url": "https://api.pdok.nl/kadaster/3d-geluid/ogc/v1",
        "title": "3D Geluid",
        "category": "topography",
        "description": "3D environment model for noise calculations",
        "keywords": ["3d", "geluid", "akoestiek", "geluidsberekening"],
        "format": "cityjson",  # Uses CityJSON format with transform quirks
    },
    "brt-achtergrondkaart": {
        "url": "https://api.pdok.nl/kadaster/brt-achtergrondkaart/ogc/v1",
        "title": "BRT Achtergrondkaart",
        "category": "topography",
        "description": "Background map derived from TOP10NL",
        "keywords": ["brt", "achtergrondkaart", "kaart"],
    },
    "top10nl": {
        "url": "https://api.pdok.nl/brt/top10nl/ogc/v1/",
        "title": "BRT TOP10NL",
        "category": "topography",
        "description": "Topographic map at 1:10,000 scale",
        "keywords": ["brt", "top10nl", "topografie", "kaart"],
    },
    "brt-bodemgebruik": {
        "url": "https://api.pdok.nl/kadaster/brt-bodemgebruik/ogc/v1",
        "title": "Bodemgebruik - Land Cover (INSPIRE)",
        "category": "topography",
        "description": "Land cover classification (INSPIRE harmonized)",
        "keywords": ["bodemgebruik", "landcover", "grondgebruik", "inspire"],
    },
    "brt-geografische-namen": {
        "url": "https://api.pdok.nl/kadaster/brt-geografische-namen/ogc/v1",
        "title": "Geografische Namen (INSPIRE)",
        "category": "topography",
        "description": "Geographic place names (INSPIRE harmonized)",
        "keywords": ["namen", "plaatsnamen", "toponiemen", "inspire"],
    },
    "brt-hydrografie": {
        "url": "https://api.pdok.nl/kadaster/brt-hydrografie/ogc/v1",
        "title": "Hydrografie (INSPIRE)",
        "category": "topography",
        "description": "Water features and hydrography (INSPIRE harmonized)",
        "keywords": ["hydrografie", "water", "rivieren", "meren", "inspire"],
    },
    "brt-vervoersnetwerken": {
        "url": "https://api.pdok.nl/kadaster/brt-vervoersnetwerken/ogc/v1",
        "title": "Vervoersnetwerken (INSPIRE)",
        "category": "topography",
        "description": "Transport networks (INSPIRE harmonized)",
        "keywords": ["transport", "wegen", "spoor", "vaarwegen", "inspire"],
    },
    "brt-zeegebieden": {
        "url": "https://api.pdok.nl/kadaster/brt-zeegebieden/ogc/v1",
        "title": "Zeegebieden (INSPIRE)",
        "category": "topography",
        "description": "Sea areas (INSPIRE harmonized)",
        "keywords": ["zee", "noordzee", "kustwater", "inspire"],
    },

    # ===== CBS STATISTICS (Statistieken) =====
    # Demographics and statistical data

    "cbs-wijken-buurten-2024": {
        "url": "https://api.pdok.nl/cbs/wijken-en-buurten-2024/ogc/v1",
        "title": "CBS Wijken en Buurten 2024",
        "category": "statistics",
        "description": "Neighborhoods and districts with demographic statistics for 2024",
        "keywords": ["cbs", "wijken", "buurten", "demografie", "statistiek"],
    },
    "cbs-wijken-buurten-2023": {
        "url": "https://api.pdok.nl/cbs/wijken-en-buurten-2023/ogc/v1",
        "title": "CBS Wijken en Buurten 2023",
        "category": "statistics",
        "description": "Neighborhoods and districts with demographic statistics for 2023",
        "keywords": ["cbs", "wijken", "buurten", "demografie", "statistiek"],
    },
    "cbs-wijken-buurten-2022": {
        "url": "https://api.pdok.nl/cbs/wijken-en-buurten-2022/ogc/v1",
        "title": "CBS Wijken en Buurten 2022",
        "category": "statistics",
        "description": "Neighborhoods and districts with demographic statistics for 2022",
        "keywords": ["cbs", "wijken", "buurten", "demografie", "statistiek"],
    },
    "cbs-gebiedsindelingen": {
        "url": "https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1",
        "title": "CBS Gebiedsindelingen 2016-heden",
        "category": "statistics",
        "description": "Current administrative area divisions",
        "keywords": ["cbs", "gebieden", "gemeenten", "provincies"],
    },
    "cbs-gebiedsindelingen-historisch": {
        "url": "https://api.pdok.nl/cbs/gebiedsindelingen-historisch/ogc/v1",
        "title": "CBS Gebiedsindelingen 1995-2015",
        "category": "statistics",
        "description": "Historical administrative area divisions (1995-2015)",
        "keywords": ["cbs", "gebieden", "historisch", "gemeenten"],
    },
    "cbs-vierkant-100m": {
        "url": "https://api.pdok.nl/cbs/vierkantstatistieken100m/ogc/v1",
        "title": "CBS Vierkantstatistieken 100m",
        "category": "statistics",
        "description": "100m grid statistics",
        "keywords": ["cbs", "grid", "statistiek", "vierkant"],
    },
    "cbs-vierkant-500m": {
        "url": "https://api.pdok.nl/cbs/vierkantstatistieken500m/ogc/v1",
        "title": "CBS Vierkantstatistieken 500m",
        "category": "statistics",
        "description": "500m grid statistics",
        "keywords": ["cbs", "grid", "statistiek", "vierkant"],
    },
    "cbs-postcode4": {
        "url": "https://api.pdok.nl/cbs/postcode4/ogc/v1",
        "title": "CBS Postcode4 statistieken",
        "category": "statistics",
        "description": "4-digit postcode area statistics",
        "keywords": ["cbs", "postcode", "statistiek"],
    },
    "cbs-postcode6": {
        "url": "https://api.pdok.nl/cbs/postcode6/ogc/v1",
        "title": "CBS Postcode6 statistieken",
        "category": "statistics",
        "description": "6-digit postcode area statistics",
        "keywords": ["cbs", "postcode", "statistiek"],
    },
    "cbs-bevolkingskernen-2021": {
        "url": "https://api.pdok.nl/cbs/bevolkingskernen-2021/ogc/v1",
        "title": "CBS Bevolkingskernen 2021",
        "category": "statistics",
        "description": "Population centers 2021",
        "keywords": ["cbs", "bevolking", "kernen", "steden"],
    },
    "cbs-bevolkingskernen-2011": {
        "url": "https://api.pdok.nl/cbs/bevolkingskernen-2011/ogc/v1",
        "title": "CBS Bevolkingskernen 2011",
        "category": "statistics",
        "description": "Population centers 2011",
        "keywords": ["cbs", "bevolking", "kernen", "steden"],
    },
    "cbs-bodemgebruik-2017": {
        "url": "https://api.pdok.nl/cbs/bestand-bodemgebruik-2017/ogc/v1",
        "title": "CBS Bestand Bodemgebruik 2017",
        "category": "statistics",
        "description": "Land use statistics 2017",
        "keywords": ["cbs", "bodemgebruik", "landgebruik"],
    },
    "cbs-bodemgebruik-2015": {
        "url": "https://api.pdok.nl/cbs/bestand-bodemgebruik-2015/ogc/v1",
        "title": "CBS Bestand Bodemgebruik 2015",
        "category": "statistics",
        "description": "Land use statistics 2015",
        "keywords": ["cbs", "bodemgebruik", "landgebruik"],
    },
    "cbs-bodemgebruik-2010": {
        "url": "https://api.pdok.nl/cbs/bestand-bodemgebruik-2010/ogc/v1",
        "title": "CBS Bestand Bodemgebruik 2010",
        "category": "statistics",
        "description": "Land use statistics 2010",
        "keywords": ["cbs", "bodemgebruik", "landgebruik"],
    },
    "cbs-landuse": {
        "url": "https://api.pdok.nl/cbs/landuse/ogc/v1/",
        "title": "CBS Existing Land Use (INSPIRE)",
        "category": "statistics",
        "description": "Land use (INSPIRE harmonized)",
        "keywords": ["cbs", "landuse", "grondgebruik", "inspire"],
    },
    "cbs-population-distribution": {
        "url": "https://api.pdok.nl/cbs/population-distribution/ogc/v1",
        "title": "CBS Population Distribution (INSPIRE)",
        "category": "statistics",
        "description": "Population distribution (INSPIRE harmonized)",
        "keywords": ["cbs", "bevolking", "demografie", "inspire"],
    },
    "cbs-human-health": {
        "url": "https://api.pdok.nl/cbs/human-health-statistics/ogc/v1",
        "title": "CBS Human Health Statistics (INSPIRE)",
        "category": "statistics",
        "description": "Health statistics (INSPIRE harmonized)",
        "keywords": ["cbs", "gezondheid", "health", "inspire"],
    },

    # ===== INFRASTRUCTURE (Infrastructuur) =====
    # Roads, railways, waterways

    "nwb-wegen": {
        "url": "https://api.pdok.nl/rws/nationaal-wegenbestand-wegen/ogc/v1/",
        "title": "Nationaal Wegenbestand - Wegen",
        "category": "infrastructure",
        "description": "National road network",
        "keywords": ["nwb", "wegen", "verkeer", "infrastructuur"],
    },
    "nwb-vaarwegen": {
        "url": "https://api.pdok.nl/rws/nationaal-wegenbestand-vaarwegen/ogc/v1",
        "title": "Nationaal Wegenbestand - Vaarwegen",
        "category": "infrastructure",
        "description": "National waterway network",
        "keywords": ["nwb", "vaarwegen", "scheepvaart", "waterwegen"],
    },
    "spoorwegen": {
        "url": "https://api.pdok.nl/prorail/spoorwegen/ogc/v1",
        "title": "Spoorwegen",
        "category": "infrastructure",
        "description": "Railway network",
        "keywords": ["spoor", "trein", "rail", "prorail"],
    },
    "weggegevens": {
        "url": "https://api.pdok.nl/rws/weggegevens/ogc/v1",
        "title": "Weggegevens",
        "category": "infrastructure",
        "description": "Road data and attributes",
        "keywords": ["wegen", "verkeer", "rijkswegen"],
    },
    "vaarwegmarkeringen": {
        "url": "https://api.pdok.nl/rws/vaarwegmarkeringen-nederland/ogc/v1",
        "title": "Vaarwegmarkeringen Nederland",
        "category": "infrastructure",
        "description": "Waterway markings and navigation aids",
        "keywords": ["vaarweg", "markering", "scheepvaart", "navigatie"],
    },

    # ===== ENVIRONMENT (Milieu & Natuur) =====
    # Nature, water, sustainability

    "natura2000": {
        "url": "https://api.pdok.nl/rvo/natura2000/ogc/v1",
        "title": "Natura 2000",
        "category": "environment",
        "description": "EU protected nature areas",
        "keywords": ["natura2000", "natuur", "beschermd", "eu"],
    },
    "natura2000-inspire": {
        "url": "https://api.pdok.nl/rvo/natura2000-geharmoniseerd/ogc/v1",
        "title": "Natura 2000 (INSPIRE)",
        "category": "environment",
        "description": "EU protected nature areas (INSPIRE harmonized)",
        "keywords": ["natura2000", "natuur", "beschermd", "inspire"],
    },
    "nationale-parken": {
        "url": "https://api.pdok.nl/rvo/nationale-parken/ogc/v1/",
        "title": "Nationale Parken",
        "category": "environment",
        "description": "Dutch national parks",
        "keywords": ["natuur", "park", "nationaalpark", "natuurgebied"],
    },
    "nationale-parken-inspire": {
        "url": "https://api.pdok.nl/rvo/nationale-parken-geharmoniseerd/ogc/v1/",
        "title": "Nationale Parken (INSPIRE)",
        "category": "environment",
        "description": "Dutch national parks (INSPIRE harmonized)",
        "keywords": ["natuur", "park", "nationaalpark", "inspire"],
    },
    "gewaspercelen": {
        "url": "https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/",
        "title": "Basisregistratie Gewaspercelen (BRP)",
        "category": "environment",
        "description": "Agricultural crop parcels",
        "keywords": ["landbouw", "gewas", "perceel", "brp"],
    },
    "habitatrichtlijn-typen": {
        "url": "https://api.pdok.nl/rvo/habitatrichtlijn-verspreiding-typen/ogc/v1",
        "title": "Habitatrichtlijn - Verspreiding Habitattypen",
        "category": "environment",
        "description": "Habitat types distribution (Habitat Directive)",
        "keywords": ["habitat", "natuur", "biodiversiteit", "eu"],
    },
    "habitatrichtlijn-soorten": {
        "url": "https://api.pdok.nl/rvo/habitatrichtlijn-verspreiding-soorten/ogc/v1",
        "title": "Habitatrichtlijn - Verspreiding Soorten",
        "category": "environment",
        "description": "Species distribution (Habitat Directive)",
        "keywords": ["soorten", "fauna", "flora", "biodiversiteit"],
    },
    "vogelrichtlijn-soorten": {
        "url": "https://api.pdok.nl/rvo/vogelrichtlijn-verspreiding-soorten/ogc/v1",
        "title": "Vogelrichtlijn - Verspreiding Soorten",
        "category": "environment",
        "description": "Bird species distribution (Birds Directive)",
        "keywords": ["vogels", "avifauna", "biodiversiteit", "eu"],
    },
    "wetlands": {
        "url": "https://api.pdok.nl/rvo/wetlands/ogc/v1",
        "title": "Wetlands",
        "category": "environment",
        "description": "Wetland areas",
        "keywords": ["wetland", "moeras", "natuur", "water"],
    },
    "wetlands-inspire": {
        "url": "https://api.pdok.nl/rvo/wetlands-geharmoniseerd/ogc/v1",
        "title": "Wetlands (INSPIRE)",
        "category": "environment",
        "description": "Wetland areas (INSPIRE harmonized)",
        "keywords": ["wetland", "moeras", "natuur", "inspire"],
    },

    # ===== OTHER (Overig) =====
    # Miscellaneous datasets

    "bestuurlijkegebieden": {
        "url": "https://api.pdok.nl/kadaster/bestuurlijkegebieden/ogc/v1/",
        "title": "Bestuurlijke Gebieden",
        "category": "administrative",
        "description": "Administrative boundaries (municipalities, provinces, water boards)",
        "keywords": ["bestuur", "gemeenten", "provincies", "waterschappen"],
    },
    "cultureel-erfgoed": {
        "url": "https://api.pdok.nl/rce/beschermde-gebieden-cultuurhistorie/ogc/v1/",
        "title": "Beschermde Gebieden - Cultuurhistorie (INSPIRE)",
        "category": "culture",
        "description": "Cultural heritage protected areas (INSPIRE harmonized)",
        "keywords": ["cultuur", "erfgoed", "monumenten", "unesco"],
    },
    "drone-nofly": {
        "url": "https://api.pdok.nl/lvnl/drone-no-flyzones/ogc/v1/",
        "title": "Drone No-Fly Zones",
        "category": "aviation",
        "description": "Restricted airspace for drones",
        "keywords": ["drone", "luchtruim", "vliegverbod"],
    },

    # ===== SPECIAL CASE: BAG3D (Different Host) =====
    # === EXTERNAL SERVICES (not hosted by PDOK) ===
    # These services are registered under "pdok" provider for convenience,
    # but are actually hosted externally and may use different formats/protocols

    # BAG3D: 3D building models from api.3dbag.nl (NOT api.pdok.nl)
    # Uses CityJSON format instead of standard GeoJSON
    # Provides multiple LODs (Level of Detail): 0, 1.2, 1.3, 2.2
    "bag3d": {
        "url": "https://api.3dbag.nl",
        "title": "3D BAG",
        "category": "base_registers",
        "description": "3D building models with LOD support from 3DBAG project (api.3dbag.nl)",
        "keywords": ["3d", "gebouwen", "bag", "lod", "cityjson"],
        "format": "cityjson",  # Uses CityJSON 2.0 format (not GeoJSON)
        "special": "external_host",  # Flag: this is NOT a PDOK service
    },
}

# Load services from config with fallback to legacy hardcoded services
# This allows users to customize services via YAML config files
from giskit.config import load_services

PDOK_SERVICES = load_services("pdok", fallback=LEGACY_PDOK_SERVICES)


class PDOKProvider(Provider):
    """PDOK data provider for Netherlands spatial data.

    .. deprecated:: 0.2.0
        PDOKProvider is deprecated. Use OGCProvider("pdok") instead.
        PDOKProvider will be removed in version 1.0.0.

        Migration guide:
            Old way:
                from giskit.providers.pdok import PDOKProvider
                provider = PDOKProvider()

            New way:
                from giskit.providers.ogc import OGCProvider
                provider = OGCProvider("pdok")
    """

    def __init__(self, name: str = "pdok", **kwargs: Any):
        """Initialize PDOK provider.

        Args:
            name: Provider name (default: "pdok")
            **kwargs: Additional configuration

        .. deprecated:: 0.2.0
            Use OGCProvider("pdok") instead. PDOKProvider will be removed in v1.0.0.
        """
        import warnings
        warnings.warn(
            "PDOKProvider is deprecated and will be removed in version 1.0.0. "
            "Use OGCProvider('pdok') instead:\n"
            "  from giskit.providers.ogc import OGCProvider\n"
            "  provider = OGCProvider('pdok')",
            DeprecationWarning,
            stacklevel=2
        )

        super().__init__(name, **kwargs)

        # Get PDOK quirks configuration
        get_quirks("pdok", "ogc-features")

        # Register OGC Features protocols for each service with quirks
        for service_name, service_config in PDOK_SERVICES.items():
            # Handle both old string format and new dict format
            if isinstance(service_config, str):
                service_url = service_config
            else:
                service_url = service_config["url"]

            # Get service-specific quirks (merges with provider quirks)
            service_quirks = get_service_quirks("pdok", "ogc-features", service_name)

            protocol = OGCFeaturesProtocol(
                base_url=service_url,
                quirks=service_quirks  # Apply service-specific quirks
            )
            self.register_protocol(f"ogc-features-{service_name}", protocol)

        # Register WFS protocols for services that don't have OGC API Features yet
        # BAG - Buildings and addresses
        bag_wfs = WFSProtocol(
            base_url="https://service.pdok.nl/lv/bag/wfs/v2_0"
        )
        self.register_protocol("wfs-bag", bag_wfs)

        # BRK - Cadastral map
        brk_wfs = WFSProtocol(
            base_url="https://service.pdok.nl/kadaster/kadastralekaart/wfs/v5_0"
        )
        self.register_protocol("wfs-brk", brk_wfs)

    async def get_metadata(self) -> dict[str, Any]:
        """Get PDOK provider metadata.

        Returns:
            Dictionary with provider information
        """
        # Count services by category
        categories: dict[str, int] = {}
        for service_config in PDOK_SERVICES.values():
            if isinstance(service_config, dict):
                category = service_config.get("category", "other")
                categories[category] = categories.get(category, 0) + 1

        return {
            "name": "PDOK",
            "description": "Publieke Dienstverlening Op de Kaart - Dutch national spatial data infrastructure",
            "homepage": "https://www.pdok.nl",
            "services": list(PDOK_SERVICES.keys()),
            "service_count": len(PDOK_SERVICES),
            "categories": categories,
            "coverage": "Netherlands",
            "attribution": "© Kadaster / PDOK",
            "license": "CC0 1.0 (public domain)",
        }

    async def download_dataset(
        self,
        dataset: Dataset,
        location: Location,
        output_path: Path,
        output_crs: str = "EPSG:4326",
        **kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """Download a PDOK dataset for a specific location.

        Args:
            dataset: Dataset specification (must have service and layers)
            location: Location specification
            output_path: Output file path (not used, returns GeoDataFrame)
            output_crs: Output CRS
            **kwargs: Additional download options

        Returns:
            GeoDataFrame with downloaded data

        Raises:
            ValueError: If service or layers not specified
            NotImplementedError: If service not supported
        """
        if not dataset.service:
            raise ValueError("PDOK dataset must specify a service")

        if dataset.service not in PDOK_SERVICES:
            raise NotImplementedError(
                f"PDOK service '{dataset.service}' not supported. "
                f"Available: {', '.join(PDOK_SERVICES.keys())}"
            )

        if not dataset.layers:
            raise ValueError("PDOK dataset must specify layers")

        # Check which protocol to use based on service type:
        # 1. WFS protocol: BAG and BRK (use WFS 2.0 at api.pdok.nl)
        # 2. OGC Features with special handling: BAG3D (external, uses CityJSON from api.3dbag.nl)
        # 3. OGC Features standard: BGT and others (use OGC API Features at api.pdok.nl)

        if dataset.service in ["bag", "brk"]:
            # BAG and BRK use WFS 2.0 protocol
            protocol_name = f"wfs-{dataset.service}"
            protocol = self.get_protocol(protocol_name)

            if protocol is None:
                raise ValueError(f"WFS protocol for {dataset.service} not found")

            # Map friendly layer names to WFS typeNames
            wfs_layers = self._map_to_wfs_layers(dataset.service, dataset.layers)

        elif dataset.service == "bag3d":
            # BAG3D is special:
            # - Hosted at api.3dbag.nl (NOT api.pdok.nl)
            # - Returns CityJSON format (NOT GeoJSON)
            # - Supports multiple LODs from same "pand" collection
            # - LOD layers (lod12, lod13, lod22) all map to "pand" collection
            # - The LOD is extracted from layer name by CityJSON parser
            protocol_name = f"ogc-features-{dataset.service}"
            protocol = self.get_protocol(protocol_name)

            if protocol is None:
                raise ValueError(f"Protocol {protocol_name} not found")

            # Keep layer names as-is - lod22, pand, etc.
            # The OGC Features protocol will map lod* to "pand" collection
            # and pass the LOD info to the CityJSON parser
            wfs_layers = dataset.layers

        else:
            # Standard OGC API Features protocol (BGT, etc.)
            protocol_name = f"ogc-features-{dataset.service}"
            protocol = self.get_protocol(protocol_name)

            if protocol is None:
                raise ValueError(f"Protocol {protocol_name} not found")

            wfs_layers = dataset.layers

        # Get bounding box from location (must be async)
        # This is a hack - we'll need to refactor to make this fully async
        # For now, assume location is already a bbox
        if location.type.value == "bbox":
            bbox = tuple(location.value)  # type: ignore
        else:
            raise NotImplementedError(
                "PDOK provider currently only supports bbox locations. "
                "Use Recipe.get_bbox_wgs84() to convert other location types."
            )

        # Transform bbox to RD if needed for WFS services
        if dataset.service in ["bag", "brk"]:
            # WFS services use RD coordinates
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)
            minx, miny = transformer.transform(bbox[0], bbox[1])
            maxx, maxy = transformer.transform(bbox[2], bbox[3])
            bbox = (minx, miny, maxx, maxy)
            # WFS services output in RD
            target_crs = "EPSG:28992"
        else:
            target_crs = output_crs

        # Download features
        async with protocol:
            gdf = await protocol.get_features(
                bbox=bbox,  # type: ignore
                layers=wfs_layers,
                crs=target_crs,
                **kwargs,
            )

        # Reproject to output CRS if needed
        if not gdf.empty and target_crs != output_crs:
            gdf = gdf.to_crs(output_crs)

        return gdf

    def _map_to_wfs_layers(self, service: str, layers: list[str]) -> list[str]:
        """Map friendly layer names to WFS typeNames.

        Args:
            service: Service name (e.g., 'bag', 'brk')
            layers: Friendly layer names (e.g., ['pand', 'verblijfsobject'])

        Returns:
            WFS typeNames (e.g., ['bag:pand', 'bag:verblijfsobject'])
        """
        if service == "bag":
            # BAG WFS layer mapping
            mapping = {
                "pand": "bag:pand",
                "verblijfsobject": "bag:verblijfsobject",
                "ligplaats": "bag:ligplaats",
                "standplaats": "bag:standplaats",
                "woonplaats": "bag:woonplaats",
            }
        elif service == "brk":
            # BRK WFS layer mapping
            mapping = {
                "perceel": "kadastralekaart:Perceel",
                "kadastrale_grens": "kadastralekaart:KadastraleGrens",
                "bebouwing": "kadastralekaart:Bebouwing",
                "nummeraanduiding": "kadastralekaart:Nummeraanduidingreeks",
                "openbare_ruimte": "kadastralekaart:OpenbareRuimteNaam",
            }
        else:
            # No mapping needed
            return layers

        return [mapping.get(layer, layer) for layer in layers]

    def get_supported_services(self) -> list[str]:
        """Get list of supported PDOK services.

        Returns:
            List of service names
        """
        return list(PDOK_SERVICES.keys())

    def get_supported_protocols(self) -> list[str]:
        """Get list of supported protocols.

        Returns:
            List of protocol names
        """
        return ["ogc-features", "wfs"]  # WFS support could be added later

    def get_services_by_category(self, category: str) -> list[str]:
        """Get list of services in a specific category.

        Args:
            category: Category name (e.g., 'base_registers', 'topography', 'statistics')

        Returns:
            List of service names in this category
        """
        services = []
        for service_name, service_config in PDOK_SERVICES.items():
            if isinstance(service_config, dict):
                if service_config.get("category") == category:
                    services.append(service_name)
        return services

    def get_service_info(self, service: str) -> dict[str, Any]:
        """Get detailed information about a specific service.

        Args:
            service: Service name

        Returns:
            Dictionary with service metadata

        Raises:
            ValueError: If service not found
        """
        if service not in PDOK_SERVICES:
            raise ValueError(
                f"Service '{service}' not found. "
                f"Available: {', '.join(PDOK_SERVICES.keys())}"
            )

        service_config = PDOK_SERVICES[service]
        if isinstance(service_config, str):
            # Old format - just URL
            return {
                "name": service,
                "url": service_config,
                "title": service.upper(),
                "category": "unknown",
                "description": "",
                "keywords": [],
            }
        else:
            # New format - full metadata
            return {
                "name": service,
                **service_config
            }

    def list_categories(self) -> list[str]:
        """Get list of all service categories.

        Returns:
            List of category names
        """
        categories = set()
        for service_config in PDOK_SERVICES.values():
            if isinstance(service_config, dict):
                category = service_config.get("category", "other")
                categories.add(category)
        return sorted(categories)


# Register PDOK provider globally
register_provider("pdok", PDOKProvider)
