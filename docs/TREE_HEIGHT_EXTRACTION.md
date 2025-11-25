# 3D Tree Height Extraction - WebApp Implementation Guide

**Target:** TypeScript/JavaScript webapp
**Purpose:** Calculate 3D tree heights by combining BGT tree locations with AHN elevation data

---

## Concept Overview

### Data Sources

1. **BGT `vegetatieobject_punt`** - 2D tree point locations
   - API: `https://api.pdok.nl/lv/bgt/ogc/v1_0/collections/vegetatieobject_punt`
   - Format: GeoJSON (EPSG:28992)
   - Contains: Tree locations (x, y), no height

2. **AHN DSM** (Digital Surface Model) - Surface height including trees
   - API: `https://service.pdok.nl/rws/ahn/wcs/v1_0`
   - Coverage: `dsm_05m` (0.5m resolution)
   - Format: GeoTIFF
   - Values: Absolute NAP height (meters) of highest point

3. **AHN DTM** (Digital Terrain Model) - Bare ground height
   - API: `https://service.pdok.nl/rws/ahn/wcs/v1_0`
   - Coverage: `dtm_05m` (0.5m resolution)
   - Format: GeoTIFF
   - Values: Absolute NAP height (meters) of ground level

### Calculation

```
Tree Height (m) = DSM (m NAP) - DTM (m NAP)
```

**Key Points:**
- ✅ DSM and DTM are in **absolute NAP coordinates** (Normaal Amsterdams Peil)
- ✅ Ground level is **NOT zero** (e.g., Amsterdam center is ~+0.5m NAP)
- ✅ Tree height is **relative** to local ground level
- ✅ Subtract DTM from DSM to get height above ground

---

## TypeScript Implementation

### Step 1: Fetch Tree Locations from BGT

```typescript
interface TreeLocation {
  id: string;
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [x, y] in EPSG:28992
  };
  properties: {
    plus_type: string; // 'boom' for trees
    bronhouder: string;
    lokaal_id: string;
  };
}

async function getBGTTreeLocations(
  bbox: [number, number, number, number] // [minx, miny, maxx, maxy] in EPSG:28992
): Promise<TreeLocation[]> {
  const url = new URL('https://api.pdok.nl/lv/bgt/ogc/v1_0/collections/vegetatieobject_punt/items');

  url.searchParams.set('bbox', bbox.join(','));
  url.searchParams.set('f', 'json');
  url.searchParams.set('limit', '1000');

  const response = await fetch(url.toString());
  const data = await response.json();

  // Filter for trees only (BGT also has hedges, etc.)
  const trees = data.features.filter(
    (f: any) => f.properties.plus_type === 'boom'
  );

  console.log(`Found ${trees.length} trees in area`);
  return trees;
}
```

### Step 2: Download AHN Elevation Rasters

**Note:** WCS returns GeoTIFF binary data. You'll need a library like [geotiff.js](https://geotiffjs.github.io/) to parse it in the browser.

```typescript
import { fromArrayBuffer } from 'geotiff';

interface RasterData {
  data: Float32Array;
  width: number;
  height: number;
  bbox: [number, number, number, number];
  resolution: number;
}

async function downloadAHNRaster(
  bbox: [number, number, number, number],
  coverage: 'dsm_05m' | 'dtm_05m',
  resolution: number = 0.5
): Promise<RasterData> {
  const [minx, miny, maxx, maxy] = bbox;

  // Calculate grid dimensions
  const widthM = maxx - minx;
  const heightM = maxy - miny;
  const widthPx = Math.floor(widthM / resolution);
  const heightPx = Math.floor(heightM / resolution);

  // Build WCS GetCoverage request
  const url = new URL('https://service.pdok.nl/rws/ahn/wcs/v1_0');
  url.searchParams.set('service', 'WCS');
  url.searchParams.set('version', '1.0.0');
  url.searchParams.set('request', 'GetCoverage');
  url.searchParams.set('coverage', coverage);
  url.searchParams.set('crs', 'EPSG:28992');
  url.searchParams.set('bbox', `${minx},${miny},${maxx},${maxy}`);
  url.searchParams.set('width', widthPx.toString());
  url.searchParams.set('height', heightPx.toString());
  url.searchParams.set('format', 'image/tiff');

  console.log(`Downloading ${coverage}: ${widthPx}x${heightPx} pixels...`);

  const response = await fetch(url.toString());
  const arrayBuffer = await response.arrayBuffer();

  // Parse GeoTIFF using geotiff.js
  const tiff = await fromArrayBuffer(arrayBuffer);
  const image = await tiff.getImage();
  const rasterData = await image.readRasters();

  return {
    data: rasterData[0] as Float32Array, // First band
    width: widthPx,
    height: heightPx,
    bbox,
    resolution,
  };
}
```

### Step 3: Sample Raster Values at Tree Locations

```typescript
/**
 * Sample raster value at a specific coordinate.
 *
 * @param raster - Raster data (DSM or DTM)
 * @param x - X coordinate in EPSG:28992
 * @param y - Y coordinate in EPSG:28992
 * @returns Height value in meters (NAP)
 */
function sampleRasterAtPoint(
  raster: RasterData,
  x: number,
  y: number
): number | null {
  const [minx, miny, maxx, maxy] = raster.bbox;

  // Check if point is within raster bounds
  if (x < minx || x > maxx || y < miny || y > maxy) {
    return null;
  }

  // Convert coordinate to pixel position
  // Note: Raster Y axis is inverted (top-down)
  const pixelX = Math.floor((x - minx) / raster.resolution);
  const pixelY = Math.floor((maxy - y) / raster.resolution); // Inverted Y

  // Check pixel bounds
  if (pixelX < 0 || pixelX >= raster.width || pixelY < 0 || pixelY >= raster.height) {
    return null;
  }

  // Get raster value at pixel position
  const index = pixelY * raster.width + pixelX;
  const value = raster.data[index];

  // Check for NoData value (typically -9999 or NaN)
  if (value === -9999 || isNaN(value)) {
    return null;
  }

  return value;
}
```

### Step 4: Calculate Tree Heights

```typescript
interface Tree3D extends TreeLocation {
  properties: TreeLocation['properties'] & {
    dsm_nap: number;      // Surface height (m NAP)
    dtm_nap: number;      // Ground height (m NAP)
    tree_height_m: number; // Tree height (m above ground)
  };
}

async function calculateTreeHeights(
  bbox: [number, number, number, number]
): Promise<Tree3D[]> {
  console.log('Step 1: Fetching tree locations...');
  const trees = await getBGTTreeLocations(bbox);

  if (trees.length === 0) {
    console.warn('No trees found in area');
    return [];
  }

  console.log('Step 2: Downloading DSM (surface height)...');
  const dsm = await downloadAHNRaster(bbox, 'dsm_05m');

  console.log('Step 3: Downloading DTM (ground height)...');
  const dtm = await downloadAHNRaster(bbox, 'dtm_05m');

  console.log('Step 4: Sampling heights at tree locations...');
  const trees3D: Tree3D[] = [];

  for (const tree of trees) {
    const [x, y] = tree.geometry.coordinates;

    // Sample both DSM and DTM at tree location
    const dsmValue = sampleRasterAtPoint(dsm, x, y);
    const dtmValue = sampleRasterAtPoint(dtm, x, y);

    // Skip if either value is missing
    if (dsmValue === null || dtmValue === null) {
      console.warn(`Skipping tree ${tree.id}: no elevation data`);
      continue;
    }

    // Calculate tree height
    const treeHeight = dsmValue - dtmValue;

    // Sanity check: tree height should be positive and reasonable
    if (treeHeight < 0 || treeHeight > 50) {
      console.warn(`Suspicious tree height: ${treeHeight.toFixed(2)}m at (${x}, ${y})`);
    }

    trees3D.push({
      ...tree,
      properties: {
        ...tree.properties,
        dsm_nap: dsmValue,
        dtm_nap: dtmValue,
        tree_height_m: treeHeight,
      },
    });
  }

  // Log statistics
  const heights = trees3D.map(t => t.properties.tree_height_m);
  console.log('Tree height statistics:');
  console.log(`  Count: ${heights.length}`);
  console.log(`  Min: ${Math.min(...heights).toFixed(2)}m`);
  console.log(`  Max: ${Math.max(...heights).toFixed(2)}m`);
  console.log(`  Mean: ${(heights.reduce((a, b) => a + b, 0) / heights.length).toFixed(2)}m`);

  return trees3D;
}
```

### Step 5: Visualize in 3D Viewer

```typescript
import * as THREE from 'three';

/**
 * Create 3D tree meshes for visualization.
 * Simple cylinder (trunk) + sphere (crown) representation.
 */
function createTreeMeshes(trees: Tree3D[]): THREE.Group {
  const group = new THREE.Group();

  // Materials
  const trunkMaterial = new THREE.MeshLambertMaterial({ color: 0x8B4513 }); // Brown
  const crownMaterial = new THREE.MeshLambertMaterial({ color: 0x228B22 }); // Green

  for (const tree of trees) {
    const [x, y] = tree.geometry.coordinates;
    const groundHeight = tree.properties.dtm_nap;
    const treeHeight = tree.properties.tree_height_m;

    // Skip very small trees
    if (treeHeight < 1) continue;

    // Create trunk (cylinder)
    const trunkHeight = treeHeight * 0.4; // 40% trunk, 60% crown
    const trunkRadius = Math.max(0.3, treeHeight * 0.05);
    const trunkGeometry = new THREE.CylinderGeometry(
      trunkRadius,
      trunkRadius,
      trunkHeight,
      8
    );
    const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
    trunk.position.set(x, groundHeight + trunkHeight / 2, y);

    // Create crown (sphere)
    const crownRadius = Math.max(1, treeHeight * 0.3);
    const crownGeometry = new THREE.SphereGeometry(crownRadius, 8, 8);
    const crown = new THREE.Mesh(crownGeometry, crownMaterial);
    crown.position.set(x, groundHeight + trunkHeight + crownRadius, y);

    // Add to group
    group.add(trunk);
    group.add(crown);
  }

  console.log(`Created ${group.children.length / 2} tree meshes`);
  return group;
}
```

---

## Performance Optimization

### 1. **Client-Side Caching**

```typescript
// Cache AHN rasters per tile to avoid re-downloading
const rasterCache = new Map<string, RasterData>();

function getCacheKey(bbox: number[], coverage: string): string {
  return `${coverage}_${bbox.join('_')}`;
}

async function getCachedRaster(
  bbox: [number, number, number, number],
  coverage: 'dsm_05m' | 'dtm_05m'
): Promise<RasterData> {
  const key = getCacheKey(bbox, coverage);

  if (rasterCache.has(key)) {
    console.log(`Using cached ${coverage}`);
    return rasterCache.get(key)!;
  }

  const raster = await downloadAHNRaster(bbox, coverage);
  rasterCache.set(key, raster);
  return raster;
}
```

### 2. **Tile-Based Loading**

For large areas, split into tiles:

```typescript
function splitBboxIntoTiles(
  bbox: [number, number, number, number],
  tileSize: number = 1000 // 1km tiles
): Array<[number, number, number, number]> {
  const [minx, miny, maxx, maxy] = bbox;
  const tiles: Array<[number, number, number, number]> = [];

  for (let x = minx; x < maxx; x += tileSize) {
    for (let y = miny; y < maxy; y += tileSize) {
      tiles.push([
        x,
        y,
        Math.min(x + tileSize, maxx),
        Math.min(y + tileSize, maxy),
      ]);
    }
  }

  return tiles;
}

async function calculateTreeHeightsTiled(
  bbox: [number, number, number, number]
): Promise<Tree3D[]> {
  const tiles = splitBboxIntoTiles(bbox, 1000);
  const allTrees: Tree3D[] = [];

  for (const tile of tiles) {
    console.log(`Processing tile ${tile.join(', ')}`);
    const trees = await calculateTreeHeights(tile);
    allTrees.push(...trees);
  }

  return allTrees;
}
```

### 3. **Level of Detail (LOD)**

Simplify tree models based on distance:

```typescript
function getTreeLOD(distanceToCamera: number): 'high' | 'medium' | 'low' {
  if (distanceToCamera < 100) return 'high';   // Detailed model
  if (distanceToCamera < 500) return 'medium'; // Simple cylinder + sphere
  return 'low';                                // Billboard sprite
}
```

---

## Backend Alternative (Recommended for Production)

For better performance, consider pre-processing on the server:

### Python Backend Endpoint

```python
# FastAPI endpoint example
@app.get("/api/trees/3d")
async def get_trees_3d(
    bbox: str,  # "minx,miny,maxx,maxy"
    resolution: float = 0.5
):
    """Calculate 3D tree heights for bbox."""
    minx, miny, maxx, maxy = map(float, bbox.split(','))

    # Get BGT trees
    trees = await get_bgt_trees(bbox=(minx, miny, maxx, maxy))

    # Download AHN rasters
    dsm = await download_ahn_raster(bbox, 'dsm_05m', resolution)
    dtm = await download_ahn_raster(bbox, 'dtm_05m', resolution)

    # Calculate heights
    for tree in trees:
        x, y = tree.geometry.coordinates
        tree.dsm_nap = sample_raster(dsm, x, y)
        tree.dtm_nap = sample_raster(dtm, x, y)
        tree.tree_height_m = tree.dsm_nap - tree.dtm_nap

    return {
        "type": "FeatureCollection",
        "features": trees
    }
```

**Benefits:**
- ✅ No large GeoTIFF downloads in browser
- ✅ Server-side caching
- ✅ Pre-computed results
- ✅ Better error handling

---

## Example Usage in Webapp

```typescript
// Initialize viewer
const viewer = new ThreeJSViewer(canvas);

// Load 3D trees for current viewport
async function loadTreesForViewport() {
  const bbox = viewer.getViewportBbox(); // [minx, miny, maxx, maxy]

  console.log('Loading 3D trees...');
  const trees3D = await calculateTreeHeights(bbox);

  // Create 3D meshes
  const treeMeshes = createTreeMeshes(trees3D);
  viewer.scene.add(treeMeshes);

  console.log(`Loaded ${trees3D.length} trees`);
}

// Load on viewport change
viewer.on('viewportChanged', () => {
  loadTreesForViewport();
});
```

---

## Testing Locations

Good test areas with many trees:

| Location | Bbox (EPSG:28992) | Description |
|----------|-------------------|-------------|
| **Vondelpark, Amsterdam** | `120000,486000,121000,487000` | Large park with many trees |
| **Kralingse Bos, Rotterdam** | `92000,435000,94000,437000` | Forest area |
| **Park Sonsbeek, Arnhem** | `188000,442000,190000,444000` | Historic park |

**Note:** BGT tree coverage varies by municipality. Some areas may have better tree data than others.

---

## Limitations & Considerations

### Data Quality

1. **BGT Coverage**
   - Not all municipalities have detailed tree data
   - `vegetatieobject_punt` may be incomplete
   - Tree locations may be outdated

2. **AHN Resolution**
   - 0.5m resolution may miss small trees
   - Very dense tree clusters may merge in DSM
   - AHN4 data from 2020-2022

3. **Height Accuracy**
   - ±10-20cm typical accuracy
   - Issues near buildings (DSM includes building edges)
   - Seasonal variation (AHN captured in leaf-on vs leaf-off)

### Alternative: Municipal Tree Registries

Many municipalities maintain detailed tree databases:

- **Amsterdam:** `data.amsterdam.nl` - Bomenbestand (tree species, diameter, age)
- **Rotterdam:** `data.rotterdam.nl` - BOR trees
- **Utrecht:** `data.utrecht.nl` - Tree registry

These often have better metadata but require separate integration per city.

---

## Dependencies

```json
{
  "dependencies": {
    "geotiff": "^2.0.7",
    "three": "^0.160.0",
    "@types/three": "^0.160.0"
  }
}
```

---

## Summary

**Process:**
1. Fetch 2D tree locations from BGT
2. Download DSM (surface) and DTM (ground) rasters from AHN
3. Sample raster values at each tree location
4. Calculate: `tree_height = DSM - DTM`
5. Visualize as 3D meshes in viewer

**Key Insight:**
> AHN elevation data is in **absolute NAP coordinates**. Always subtract DTM from DSM to get relative heights above ground.

**Recommended Approach:**
- For **prototyping**: Client-side calculation (as documented above)
- For **production**: Backend API endpoint with caching

---

**Last Updated:** November 25, 2025
**Author:** GISKit Documentation Team
