#!/usr/bin/env python3
"""Test script to validate BAG3D transform handling across pages."""

import asyncio

import httpx

from giskit.protocols.cityjson import cityjson_to_geodataframe


async def test_bag3d_transform():
    """Test that each page's transform is correctly applied to features."""

    # Small bbox in Spijkenisse (Curieweg area)
    bbox = (76355, 428893, 76755, 429293)  # 400m x 400m in RD

    # Convert RD to WGS84 for API
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)
    minx, miny = transformer.transform(bbox[0], bbox[1])
    maxx, maxy = transformer.transform(bbox[2], bbox[3])
    wgs84_bbox = (minx, miny, maxx, maxy)

    url = "https://api.3dbag.nl/collections/pand/items"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Fetch first 2 pages to compare transforms
        params = {
            "bbox": f"{wgs84_bbox[0]},{wgs84_bbox[1]},{wgs84_bbox[2]},{wgs84_bbox[3]}",
            "limit": 10,
        }

        print("Fetching first page...")
        response1 = await client.get(url, params=params)
        response1.raise_for_status()
        page1 = response1.json()

        # Extract transform from page 1
        transform1 = None
        if "metadata" in page1 and isinstance(page1["metadata"], dict):
            transform1 = page1["metadata"].get("transform")

        print(f"Page 1 transform: {transform1}")
        print(f"Page 1 features: {len(page1.get('features', []))}")

        # Convert page 1 to GeoDataFrame
        gdf1 = cityjson_to_geodataframe(page1, lod="2.2")
        if not gdf1.empty:
            print(f"Page 1 GDF: {len(gdf1)} buildings")
            print(f"  Sample coords: {gdf1.iloc[0].geometry.centroid}")

        # Get next page if available
        next_url = None
        for link in page1.get("links", []):
            if link.get("rel") == "next":
                next_url = link.get("href")
                break

        if next_url:
            print("\nFetching second page...")
            response2 = await client.get(next_url)
            response2.raise_for_status()
            page2 = response2.json()

            # Extract transform from page 2
            transform2 = None
            if "metadata" in page2 and isinstance(page2["metadata"], dict):
                transform2 = page2["metadata"].get("transform")

            print(f"Page 2 transform: {transform2}")
            print(f"Page 2 features: {len(page2.get('features', []))}")

            # Convert page 2 to GeoDataFrame
            gdf2 = cityjson_to_geodataframe(page2, lod="2.2")
            if not gdf2.empty:
                print(f"Page 2 GDF: {len(gdf2)} buildings")
                print(f"  Sample coords: {gdf2.iloc[0].geometry.centroid}")

            # Compare transforms
            if transform1 != transform2:
                print("\n⚠️  WARNING: Transforms differ between pages!")
                print("  This is expected and handled correctly by cityjson_to_geodataframe()")
            else:
                print("\n✓ Transforms are identical (or both None)")

            # Verify coordinates are in valid RD range
            if not gdf1.empty and not gdf2.empty:
                all_coords = list(gdf1.geometry.centroid) + list(gdf2.geometry.centroid)
                x_coords = [p.x for p in all_coords]
                y_coords = [p.y for p in all_coords]

                print("\nCoordinate ranges:")
                print(f"  X: {min(x_coords):.0f} - {max(x_coords):.0f}")
                print(f"  Y: {min(y_coords):.0f} - {max(y_coords):.0f}")

                # RD valid range: X ~0-300000, Y ~300000-625000
                if min(x_coords) < 0 or max(x_coords) > 300000:
                    print("  ❌ X coordinates out of valid RD range!")
                elif min(y_coords) < 300000 or max(y_coords) > 625000:
                    print("  ❌ Y coordinates out of valid RD range!")
                else:
                    print("  ✓ All coordinates in valid RD range")
        else:
            print("\nNo next page available (small dataset)")


if __name__ == "__main__":
    asyncio.run(test_bag3d_transform())
