#!/usr/bin/env bash
#
# build_site_underlegger.sh - Build complete Dutch site GeoPackage from location
#
# This script creates a complete site "underlegger" (base map) equivalent to
# Sitedb's site-underlegger, containing:
#   - BAG pand (buildings)
#   - BRK perceel (cadastral parcels)
#   - BAG 3D LOD 2.2 (3D building models with roof geometry)
#   - All BGT layers (complete topography)
#   - _metadata layer with location info
#
# Usage:
#   ./build_site_underlegger.sh "ADDRESS" RADIUS [OUTPUT]
#
# Examples:
#   ./build_site_underlegger.sh "Dam 1, Amsterdam" 500
#   ./build_site_underlegger.sh "Curieweg 7a, Spijkenisse" 500 site.gpkg
#   ./build_site_underlegger.sh "155000,463000" 200  # RD coordinates
#   ./build_site_underlegger.sh "52.37,4.89" 300     # WGS84 lat,lon
#
# Requirements:
#   - Python 3.9+ with giskit installed
#   - Internet connection for PDOK data download
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECIPE_TEMPLATE="${SCRIPT_DIR}/site_underlegger.json"

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 ADDRESS RADIUS [OUTPUT]"
    echo ""
    echo "Arguments:"
    echo "  ADDRESS   Location (address or coordinates)"
    echo "            Examples:"
    echo "              - 'Dam 1, Amsterdam'"
    echo "              - '155000,463000' (RD coordinates)"
    echo "              - '52.37,4.89' (WGS84 lat,lon)"
    echo "  RADIUS    Radius in meters (e.g., 500)"
    echo "  OUTPUT    Output GeoPackage path (optional, default: site_underlegger.gpkg)"
    echo ""
    echo "Examples:"
    echo "  $0 'Dam 1, Amsterdam' 500"
    echo "  $0 'Curieweg 7a, Spijkenisse' 500 curieweg_site.gpkg"
    echo "  $0 '155000,463000' 200 mysite.gpkg"
    exit 1
fi

ADDRESS="$1"
RADIUS="$2"
OUTPUT="${3:-site_underlegger.gpkg}"

# Check if recipe template exists
if [ ! -f "$RECIPE_TEMPLATE" ]; then
    echo -e "${RED}Error: Recipe template not found: ${RECIPE_TEMPLATE}${NC}"
    echo "Please ensure site_underlegger.json is in the same directory as this script."
    exit 1
fi

# Create output directory if needed
OUTPUT_DIR="$(dirname "$OUTPUT")"
if [ "$OUTPUT_DIR" != "." ] && [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    echo -e "${GREEN}✓${NC} Created output directory: $OUTPUT_DIR"
fi

# Generate slug for temporary recipe filename
SLUG=$(echo "$ADDRESS" | tr '[:upper:]' '[:lower:]' | sed -e 's/[^a-z0-9]/-/g' -e 's/--*/-/g' -e 's/^-//' -e 's/-$//' | cut -c1-50)
TEMP_RECIPE="/tmp/giskit_${SLUG}_$$.json"

# Print header
echo ""
echo -e "${BOLD}${CYAN}================================================================================${NC}"
echo -e "${BOLD}${CYAN} GISKit Site Underlegger Builder${NC}"
echo -e "${BOLD}${CYAN}================================================================================${NC}"
echo ""
echo -e "${BOLD}Configuration:${NC}"
echo -e "  Location:  ${GREEN}$ADDRESS${NC}"
echo -e "  Radius:    ${GREEN}${RADIUS}m${NC}"
echo -e "  Output:    ${GREEN}$OUTPUT${NC}"
echo ""
echo -e "${BOLD}Datasets:${NC}"
echo "  • BAG pand (buildings)"
echo "  • BRK perceel (cadastral parcels)"
echo "  • BAG 3D LOD 2.2 (3D building models with roof geometry)"
echo "  • BGT complete (46 topographic layers)"
echo ""

# Create temporary recipe with custom location and output
echo -e "${CYAN}📝 Generating recipe...${NC}"
jq --arg address "$ADDRESS" \
   --arg radius "$RADIUS" \
   --arg output "$(basename "$OUTPUT")" \
   '.location.value = $address | 
    .location.radius = ($radius | tonumber) |
    .name = ("Site Underlegger - " + $address) |
    .description = ("Complete site base map for " + $address + " (radius: " + $radius + "m)") |
    .output.path = $output' \
   "$RECIPE_TEMPLATE" > "$TEMP_RECIPE"

echo -e "${GREEN}✓${NC} Recipe generated: $TEMP_RECIPE"
echo ""

# Execute recipe with giskit
echo -e "${BOLD}${CYAN}📥 Downloading data...${NC}"
echo -e "${YELLOW}This may take several minutes depending on the area size and number of features.${NC}"
echo ""

# Check if giskit CLI is available
if ! command -v giskit &> /dev/null; then
    echo -e "${YELLOW}Warning: giskit CLI not found. Trying with Python module...${NC}"
    GISKIT_CMD="python -m giskit.cli.main"
else
    GISKIT_CMD="giskit"
fi

# Execute recipe
# Change to output directory so recipe saves there
OUTPUT_DIR_ABS="$(cd "$(dirname "$OUTPUT")" && pwd)"
OUTPUT_FILENAME="$(basename "$OUTPUT")"

cd "$OUTPUT_DIR_ABS"
if $GISKIT_CMD run "$TEMP_RECIPE"; then
    # Move back to original directory
    cd - > /dev/null
    
    # Check if file was actually created (not just dry run)
    if [ ! -f "$OUTPUT" ]; then
        echo ""
        echo -e "${BOLD}${RED}================================================================================${NC}"
        echo -e "${BOLD}${RED} ✗ No Output Created${NC}"
        echo -e "${BOLD}${RED}================================================================================${NC}"
        echo ""
        echo -e "${RED}The recipe ran but no output file was created.${NC}"
        echo -e "${RED}This usually means the recipe was run in dry-run mode or no features were found.${NC}"
        echo ""
        echo -e "${YELLOW}Temporary recipe kept for debugging: $TEMP_RECIPE${NC}"
        echo ""
        exit 1
    fi
    echo ""
    echo -e "${BOLD}${GREEN}================================================================================${NC}"
    echo -e "${BOLD}${GREEN} ✓ Site Underlegger Complete!${NC}"
    echo -e "${BOLD}${GREEN}================================================================================${NC}"
    echo ""
    echo -e "${BOLD}Output:${NC}"
    echo -e "  File: ${GREEN}$OUTPUT${NC}"
    
    # Show file size if possible
    if command -v du &> /dev/null; then
        FILESIZE=$(du -h "$OUTPUT" | cut -f1)
        echo -e "  Size: ${GREEN}${FILESIZE}${NC}"
    fi
    
    echo ""
    echo -e "${BOLD}Contents:${NC}"
    echo "  • BAG pand (buildings)"
    echo "  • BRK perceel (cadastral parcels)" 
    echo "  • BAG 3D LOD 2.2 (3D building models)"
    echo "  • BGT layers (complete topography)"
    echo "  • _metadata layer (location, bbox, timestamp)"
    echo ""
    echo -e "${BOLD}Next steps:${NC}"
    echo "  1. View in QGIS:"
    echo -e "     ${CYAN}qgis $OUTPUT${NC}"
    echo ""
    echo "  2. Inspect with Python:"
    echo -e "     ${CYAN}python${NC}"
    echo -e "     ${CYAN}>>> import geopandas as gpd${NC}"
    echo -e "     ${CYAN}>>> gpd.list_layers('$OUTPUT')${NC}"
    echo -e "     ${CYAN}>>> gdf = gpd.read_file('$OUTPUT', layer='bgt_wegdeel')${NC}"
    echo ""
    echo "  3. Export to IFC:"
    echo -e "     ${CYAN}giskit export ifc $OUTPUT --output site.ifc${NC}"
    echo ""
    
    # Clean up temp recipe
    rm -f "$TEMP_RECIPE"
    
    exit 0
else
    echo ""
    echo -e "${BOLD}${RED}================================================================================${NC}"
    echo -e "${BOLD}${RED} ✗ Download Failed${NC}"
    echo -e "${BOLD}${RED}================================================================================${NC}"
    echo ""
    echo -e "${RED}The recipe execution failed. Please check:${NC}"
    echo "  1. Your internet connection"
    echo "  2. The location is valid (address exists or coordinates are in Netherlands)"
    echo "  3. PDOK services are available"
    echo ""
    echo -e "${YELLOW}Temporary recipe kept for debugging: $TEMP_RECIPE${NC}"
    echo ""
    
    exit 1
fi
