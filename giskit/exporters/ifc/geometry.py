"""IFC geometry conversion utilities.

Converts Shapely geometries to IFC geometry representations.
"""

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon


def transform_to_relative(geom, ref_x: float, ref_y: float):
    """Transform geometry from absolute RD coordinates to relative coordinates.

    Args:
        geom: Shapely geometry in absolute RD coordinates
        ref_x: Reference point X (RD)
        ref_y: Reference point Y (RD)

    Returns:
        Transformed geometry with origin at reference point
    """
    return affinity.translate(geom, xoff=-ref_x, yoff=-ref_y)


def normalize_z_to_ground(geom):
    """Normalize 3D geometry so the lowest Z coordinate is at Z=0.

    Finds the minimum Z coordinate across all vertices and shifts the entire
    geometry vertically so that the lowest point sits at ground level (Z=0).
    This is useful for BAG3D buildings that have absolute NAP elevations.

    Args:
        geom: Shapely geometry with Z coordinates (Polygon or MultiPolygon)

    Returns:
        Transformed geometry with minimum Z = 0
    """
    # Find minimum Z coordinate
    min_z = float("inf")

    if isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            coords = list(poly.exterior.coords)
            z_coords = [c[2] for c in coords if len(c) >= 3]
            if z_coords:
                min_z = min(min_z, min(z_coords))
    elif isinstance(geom, Polygon):
        coords = list(geom.exterior.coords)
        z_coords = [c[2] for c in coords if len(c) >= 3]
        if z_coords:
            min_z = min(z_coords)

    # If no Z coordinates found or already at 0, return as-is
    if min_z == float("inf") or min_z == 0.0:
        return geom

    # Translate vertically to set min_z to 0
    return affinity.translate(geom, zoff=-min_z)


def create_ifc_point(ifc_file, x: float, y: float, z: float = 0.0):
    """Create an IFC Cartesian Point.

    Args:
        ifc_file: IFC file instance
        x, y, z: Coordinates

    Returns:
        IfcCartesianPoint
    """
    return ifc_file.createIfcCartesianPoint((x, y, z))


def create_ifc_polyline(ifc_file, points: list) -> object:
    """Create an IFC Polyline from list of points.

    Args:
        ifc_file: IFC file instance
        points: List of (x, y, z) tuples

    Returns:
        IfcPolyline
    """
    ifc_points = [create_ifc_point(ifc_file, *pt) for pt in points]
    return ifc_file.createIfcPolyline(ifc_points)


def polygon_to_ifc_face(ifc_file, polygon: Polygon, z: float = 0.0) -> object:
    """Convert Shapely Polygon to IFC Face.

    Args:
        ifc_file: IFC file instance
        polygon: Shapely Polygon (2D)
        z: Z-height for extruding polygon

    Returns:
        IfcFace
    """
    # Extract exterior ring coordinates and add Z
    coords = list(polygon.exterior.coords)
    points_3d = [(x, y, z) for x, y in coords]

    # Create IfcPolyLoop from points
    ifc_points = [create_ifc_point(ifc_file, *pt) for pt in points_3d]
    poly_loop = ifc_file.createIfcPolyLoop(ifc_points)

    # Create outer face bound
    face_bounds = [ifc_file.createIfcFaceOuterBound(poly_loop, True)]

    # Handle interior rings (holes)
    for interior in polygon.interiors:
        interior_coords = list(interior.coords)
        interior_points_3d = [(x, y, z) for x, y in interior_coords]
        interior_ifc_points = [create_ifc_point(ifc_file, *pt) for pt in interior_points_3d]
        interior_poly_loop = ifc_file.createIfcPolyLoop(interior_ifc_points)
        # Interior bounds are holes, so orientation is False
        face_bounds.append(ifc_file.createIfcFaceBound(interior_poly_loop, False))

    # Create face with all bounds
    return ifc_file.createIfcFace(face_bounds)


def polygon_3d_to_ifc_face(ifc_file, polygon: Polygon) -> object:
    """Convert Shapely Polygon with Z coordinates to IFC Face.

    Args:
        ifc_file: IFC file instance
        polygon: Shapely Polygon with 3D coordinates

    Returns:
        IfcFace
    """
    # Extract coordinates (already 3D)
    coords = list(polygon.exterior.coords)

    # Create IfcPolyLoop from 3D points
    ifc_points = [create_ifc_point(ifc_file, *pt) for pt in coords]
    poly_loop = ifc_file.createIfcPolyLoop(ifc_points)

    # Create outer face bound
    face_bounds = [ifc_file.createIfcFaceOuterBound(poly_loop, True)]

    # Handle interior rings (holes)
    for interior in polygon.interiors:
        interior_coords = list(interior.coords)
        interior_ifc_points = [create_ifc_point(ifc_file, *pt) for pt in interior_coords]
        interior_poly_loop = ifc_file.createIfcPolyLoop(interior_ifc_points)
        # Interior bounds are holes, so orientation is False
        face_bounds.append(ifc_file.createIfcFaceBound(interior_poly_loop, False))

    # Create face with all bounds
    return ifc_file.createIfcFace(face_bounds)


def create_extruded_area_solid(ifc_file, polygon: Polygon, height: float, position=None) -> object:
    """Create an extruded solid from a 2D polygon.

    Args:
        ifc_file: IFC file instance
        polygon: 2D polygon footprint
        height: Extrusion height
        position: Optional IfcAxis2Placement3D for positioning

    Returns:
        IfcExtrudedAreaSolid
    """
    # Create polyline from polygon exterior
    coords = list(polygon.exterior.coords)
    points_2d = list(coords[:-1])  # Remove duplicate last point

    # Create IfcPolyline for profile
    ifc_points = [ifc_file.createIfcCartesianPoint((x, y)) for x, y in points_2d]
    polyline = ifc_file.createIfcPolyline(ifc_points)

    # Create profile - with or without voids depending on interior rings
    if len(polygon.interiors) > 0:
        # Create outer curve
        ifc_file.createIfcArbitraryClosedProfileDef("AREA", None, polyline)

        # Create inner curves (holes)
        inner_curves = []
        for interior in polygon.interiors:
            interior_coords = list(interior.coords)
            interior_points_2d = list(interior_coords[:-1])  # Remove duplicate last point
            interior_ifc_points = [
                ifc_file.createIfcCartesianPoint((x, y)) for x, y in interior_points_2d
            ]
            interior_polyline = ifc_file.createIfcPolyline(interior_ifc_points)
            inner_curves.append(interior_polyline)

        # Create profile with voids
        profile = ifc_file.createIfcArbitraryProfileDefWithVoids(
            "AREA", None, polyline, inner_curves
        )
    else:
        # Simple closed profile without holes
        profile = ifc_file.createIfcArbitraryClosedProfileDef("AREA", None, polyline)

    # Default position at origin
    if position is None:
        origin = ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0))
        position = ifc_file.createIfcAxis2Placement3D(
            origin,
            None,  # Default Z-axis
            None,  # Default X-axis
        )

    # Extrusion direction (upward)
    direction = ifc_file.createIfcDirection((0.0, 0.0, 1.0))

    # Create extruded solid
    return ifc_file.createIfcExtrudedAreaSolid(profile, position, direction, height)


def create_faceted_brep(ifc_file, faces: list) -> object:
    """Create a faceted B-rep from list of IFC faces.

    Args:
        ifc_file: IFC file instance
        faces: List of IfcFace objects

    Returns:
        IfcFacetedBrep
    """
    # Create closed shell
    closed_shell = ifc_file.createIfcClosedShell(faces)

    # Create B-rep
    return ifc_file.createIfcFacetedBrep(closed_shell)


def classify_surface(polygon: Polygon) -> str:
    """Classify a 3D polygon surface as ROOF, WALL, or FLOOR.

    Uses surface normal vector to determine orientation:
    - Vertical surfaces (|normal.z| < 0.5) = WALL
    - Horizontal surfaces (|normal.z| > 0.7) = ROOF or FLOOR based on height

    Args:
        polygon: Shapely Polygon with Z coordinates

    Returns:
        Surface type: 'ROOF', 'WALL', or 'FLOOR'
    """
    coords = list(polygon.exterior.coords)
    z_coords = [c[2] for c in coords if len(c) >= 3]

    if not z_coords:
        return "FLOOR"  # Default for 2D

    z_min = min(z_coords)
    z_max = max(z_coords)
    z_range = z_max - z_min
    z_avg = sum(z_coords) / len(z_coords)

    # Calculate surface normal using first 3 non-collinear points
    # Normal = (p1-p0) × (p2-p0)
    if len(coords) >= 3:
        p0 = coords[0] if len(coords[0]) == 3 else coords[0] + (0.0,)
        p1 = coords[1] if len(coords[1]) == 3 else coords[1] + (0.0,)
        p2 = coords[2] if len(coords[2]) == 3 else coords[2] + (0.0,)

        # Edge vectors
        v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])

        # Cross product for normal
        nx = v1[1] * v2[2] - v1[2] * v2[1]
        ny = v1[2] * v2[0] - v1[0] * v2[2]
        nz = v1[0] * v2[1] - v1[1] * v2[0]

        # Normalize
        length = (nx * nx + ny * ny + nz * nz) ** 0.5
        if length > 0:
            nz_normalized = abs(nz / length)

            # Vertical surface (normal pointing sideways)
            if nz_normalized < 0.5:
                return "WALL"

            # Horizontal surface (normal pointing up/down)
            if nz_normalized > 0.7:
                # Distinguish roof from floor by average height
                if z_avg < 1.0:
                    return "FLOOR"
                else:
                    return "ROOF"

    # Fallback: use Z range heuristic
    if z_range < 0.5:
        if z_avg < 1.0:
            return "FLOOR"
        else:
            return "ROOF"
    else:
        return "WALL"  # If in doubt and not flat, it's probably a wall


def create_shape_representation(ifc_file, context, representation_type: str, items: list) -> object:
    """Create an IFC Shape Representation.

    Args:
        ifc_file: IFC file instance
        context: IfcGeometricRepresentationContext
        representation_type: Type like 'SweptSolid', 'Brep', etc.
        items: List of representation items

    Returns:
        IfcShapeRepresentation
    """
    return ifc_file.createIfcShapeRepresentation(
        context, context.ContextIdentifier, representation_type, items
    )
