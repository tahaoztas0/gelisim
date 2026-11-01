"""Best-effort CityGML checks; not a replacement for OGC schema validation."""
from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET

GML_NS = "http://www.opengis.net/gml"
GML_ID = f"{{{GML_NS}}}id"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def finding(level: str, code: str, message: str, feature: str = "") -> dict:
    return {"severity": level, "code": code, "message": message, "feature": feature}


def _coordinates(ring: ET.Element, default_dimension: int):
    dimensions = [int(value) for node in ring.iter() for key, value in node.attrib.items()
                  if local_name(key) == "srsDimension" and value.isdigit()]
    dim = dimensions[0] if dimensions else default_dimension
    if dim not in (2, 3):
        raise ValueError("Only 2D or 3D coordinate dimensions are supported")
    coords = []
    poslists = [node for node in ring if local_name(node.tag) == "posList"]
    positions = [node for node in ring if local_name(node.tag) == "pos"]
    legacy = [node for node in ring if local_name(node.tag) == "coordinates"]
    if poslists:
        for node in poslists:
            values = (node.text or "").split()
            if not values or len(values) % dim:
                raise ValueError("posList must contain complete coordinate tuples")
            coords.extend(tuple(float(x) for x in values[i:i + dim]) for i in range(0, len(values), dim))
    elif positions:
        for node in positions:
            values = (node.text or "").split()
            if len(values) != dim:
                raise ValueError("pos must match coordinate dimension")
            coords.append(tuple(float(x) for x in values))
    elif legacy:
        for node in legacy:
            for token in (node.text or "").split():
                values = token.split(",")
                if len(values) != dim:
                    raise ValueError("legacy coordinates must match coordinate dimension")
                coords.append(tuple(float(x) for x in values))
    else:
        raise ValueError("LinearRing has no supported inline coordinates")
    if not all(math.isfinite(value) for point in coords for value in point):
        raise ValueError("Coordinates must be finite numbers")
    return coords


def _planarity_deviation(points: list[tuple[float, ...]]) -> float:
    if not points or len(points[0]) != 3:
        return 0.0
    a = points[0]
    normal = None
    for i in range(1, len(points) - 1):
        u = [points[i][j] - a[j] for j in range(3)]
        v = [points[i + 1][j] - a[j] for j in range(3)]
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        magnitude = math.sqrt(sum(x*x for x in n))
        if magnitude > 1e-12:
            normal = tuple(x/magnitude for x in n)
            break
    if normal is None:
        return 0.0
    return max(abs(sum((p[j]-a[j])*normal[j] for j in range(3))) for p in points)


def audit_text(text: str, *, dimension: int = 3, tolerance: float = 0.01) -> dict:
    if dimension not in (2, 3):
        raise ValueError("dimension must be 2 or 3")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    result = {"buildings": 0, "polygons": 0, "rings": 0, "findings": []}
    notes = result["findings"]
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        notes.append(finding("error", "INVALID_XML", str(exc)))
        return result
    ids: set[str] = set()
    for node in root.iter():
        name = local_name(node.tag)
        identifier = node.attrib.get(GML_ID)
        if identifier:
            if identifier in ids:
                notes.append(finding("error", "DUPLICATE_ID", f"Duplicate gml:id: {identifier}", identifier))
            ids.add(identifier)
        if name in ("Building", "BuildingPart"):
            result["buildings"] += 1
        if name == "Polygon" and node.tag.startswith("{"+GML_NS+"}"):
            result["polygons"] += 1
        if name == "LinearRing" and node.tag.startswith("{"+GML_NS+"}"):
            result["rings"] += 1
            label = identifier or f"ring-{result['rings']}"
            try:
                points = _coordinates(node, dimension)
            except (ValueError, OverflowError) as exc:
                notes.append(finding("error", "INVALID_COORDINATES", str(exc), label))
                continue
            if len(points) < 4:
                notes.append(finding("error", "TOO_FEW_POINTS", "Ring requires at least four coordinate tuples", label))
                continue
            if points[0] != points[-1]:
                notes.append(finding("error", "UNCLOSED_RING", "First and last coordinates must match", label))
            distinct = set(points[:-1] if points[0] == points[-1] else points)
            if len(distinct) < 3:
                notes.append(finding("error", "DEGENERATE_RING", "Ring has fewer than three distinct vertices", label))
            if len(points[0]) == 3 and _planarity_deviation(points) > tolerance:
                notes.append(finding("warning", "NON_PLANAR_RING", "Ring deviates from a plane beyond tolerance", label))
    if result["buildings"] == 0:
        notes.append(finding("warning", "NO_BUILDINGS", "No Building or BuildingPart element was found"))
    if result["rings"] == 0:
        notes.append(finding("warning", "NO_RINGS", "No supported GML LinearRing was found"))
    return result


def audit_file(path: str | Path, *, dimension: int = 3, tolerance: float = 0.01) -> dict:
    source = Path(path)
    result = audit_text(source.read_text(encoding="utf-8-sig"), dimension=dimension, tolerance=tolerance)
    result["file"] = str(source)
    return result
