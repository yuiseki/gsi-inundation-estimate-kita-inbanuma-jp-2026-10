"""Conversion helpers: read GSI contour GeoJSON files into rows, count and measure them."""

import json
from pathlib import Path

import numpy as np
import pyproj
import shapely
from shapely.geometry import shape

AREA_CRS = "EPSG:6677"
_TO_AREA = pyproj.Transformer.from_crs("EPSG:4326", AREA_CRS, always_xy=True)


def read_features(path: Path) -> tuple[dict, list[dict]]:
    """Return (the whole GeoJSON document without features, the features unchanged)."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("type") != "FeatureCollection":
        raise ValueError(f"{path}: not a FeatureCollection")
    feats = doc.get("features", [])
    meta = {k: v for k, v in doc.items() if k != "features"}
    return meta, feats


def declared_crs(meta: dict) -> str | None:
    """The CRS the file declares (GeoJSON 'crs' member), None when it declares nothing."""
    crs = meta.get("crs")
    return None if crs is None else crs.get("properties", {}).get("name")


def area_km2(geom) -> float:
    """Area in square km on EPSG:6677; geometry is not repaired. Invalid geometry gives the area as computed."""
    return shapely.transform(geom, lambda c: np.column_stack(_TO_AREA.transform(c[:, 0], c[:, 1]))).area / 1e6


def summarize(feats: list[dict]) -> dict:
    geoms = [shape(f["geometry"]) for f in feats if f.get("geometry")]
    types = sorted({g.geom_type for g in geoms})
    invalid = int(sum(not g.is_valid for g in geoms))
    bounds = shapely.total_bounds(geoms).tolist() if geoms else None
    return {"features": len(feats), "geometry_types": types, "invalid": invalid, "bounds": bounds,
            "area_km2": sum(area_km2(g) for g in geoms)}  # fmt: skip


# --- page parsing and row building -------------------------------------------------------------
import re

_VER_RE = re.compile(
    r"「北印旛沼」\s*令和(\d+)年(\d+)月(\d+)日(\d+)時時点（(?:(\d+)月)?(\d+)日公開）"
)
_FILE_RE = re.compile(r"shinsui_rinkaku_kita-inbanuma_(\d{8})\.zip")


def parse_page_versions(html: str) -> list[dict]:
    """Versions listed on the page, in page order: label, version_time (ISO +09:00), published (ISO date), zip url.

    The page gives the year only as the Reiwa year of the version time; 'published' takes that year,
    and the next year when the published month is earlier than the version month.
    """
    body = re.sub(r"<[^>]+>", "", html)
    labels = list(_VER_RE.finditer(body))
    zips = re.findall(r'href="(https://www1\.gsi\.go\.jp/geowww/saigai/[^"]*/shinsui_rinkaku_kita-inbanuma_\d{8}\.zip)"', html)
    if len(labels) != len(zips):
        raise ValueError(f"{len(labels)} version labels but {len(zips)} zip links")
    out = []
    for m, z in zip(labels, zips):
        ry, mo, d, h, pm, pd = m.groups()
        y = 2018 + int(ry)
        pmo = int(pm) if pm else int(mo)
        py = y + (1 if pmo < int(mo) else 0)
        out.append({"label": m.group(0), "version_time": f"{y:04d}-{int(mo):02d}-{int(d):02d}T{int(h):02d}:00:00+09:00",
                    "published": f"{py:04d}-{pmo:02d}-{int(pd):02d}", "zip_url": z,
                    "file_date": _FILE_RE.search(z).group(1)})  # fmt: skip
    return out


def rows_from_features(feats: list[dict], base: dict) -> list[dict]:
    """One row per feature: the base columns, every original property as its own column, the original
    properties as JSON (types preserved), and the geometry object unchanged."""
    rows = []
    for i, f in enumerate(feats):
        props = f.get("properties") or {}
        row = dict(base)
        row["feature_index"] = i
        row["properties_json"] = json.dumps(props, ensure_ascii=False)
        for k, v in props.items():
            row[k] = None if v is None else str(v)
        row["geometry_obj"] = f["geometry"]
        rows.append(row)
    return rows
