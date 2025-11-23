"""Protocol implementations for different spatial data APIs.

Protocols define how to communicate with different API standards:
- OGC API Features (WFS 3.0)
- WMS/WMTS
- OGC Coverages
- Custom APIs

Each protocol can have provider-specific quirks configured.
"""

from giskit.protocols.base import Protocol
from giskit.protocols.ogc_features import OGCFeaturesError, OGCFeaturesProtocol
from giskit.protocols.quirks import KNOWN_QUIRKS, ProtocolQuirks, get_quirks

__all__ = [
    "Protocol",
    "OGCFeaturesProtocol",
    "OGCFeaturesError",
    "ProtocolQuirks",
    "get_quirks",
    "KNOWN_QUIRKS",
]
