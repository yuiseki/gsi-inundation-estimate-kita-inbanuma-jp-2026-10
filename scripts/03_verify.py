#!/usr/bin/env python3
"""Independent check: GDAL (ogrinfo / ogr2ogr, reading the ZIPs directly) against the GeoParquet (geopandas, pyarrow, DuckDB).

    uv run python scripts/03_verify.py   # exit 1 on any mismatch; writes docs/verification.json
"""

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb
import geopandas as gpd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
GDAL = Path("/home/yuiseki/anaconda3/bin")
PARQ = ROOT / "data" / "parquet" / "inundation_kita_inbanuma.parquet"
TOL_AREA = 1e-6  # relative
TOL_BBOX = 1e-9


def run(*a) -> str:
    return subprocess.run([str(GDAL / a[0]), *a[1:]], check=True, capture_output=True, text=True).stdout


def gdal_side(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as z:  # only to learn the member name; GDAL reads the data
        (member,) = [n for n in z.namelist() if n.endswith(".geojson")]
    vsi = f"/vsizip/{zip_path}/{member}"
    # the datasource lists layers; the layer name is the member name without extension
    layer = re.search(r"\d+: (\S+) \(", run("ogrinfo", "-ro", vsi)).group(1)
    info = run("ogrinfo", "-ro", "-so", "-al", vsi)
    n = int(re.search(r"Feature Count: (\d+)", info).group(1))
    gtype = re.search(r"Geometry: (.+)", info).group(1).strip()
    ext = [float(x) for x in re.findall(r"-?\d+\.\d+", re.search(r"Extent: (.+)", info).group(1))]
    epsg = re.search(r'ID\["EPSG",(\d+)\]\]\s*\n', info).group(1)
    sql = f'SELECT ST_Area(ST_Transform(geometry,6677)) AS a, ST_IsValid(geometry) AS v FROM "{layer}"'
    out = run("ogrinfo", "-ro", "-dialect", "SQLite", "-sql", sql.replace("geometry", "GEOMETRY"), vsi)
    areas = [float(x) for x in re.findall(r"a \(Real\) = (\S+)", out)]
    valid = [int(x) for x in re.findall(r"v \(Integer\) = (\d)", out)]
    return {"layer": layer, "features": n, "geometry_type": gtype, "bbox": [ext[0], ext[1], ext[2], ext[3]], "epsg": epsg,
            "area_km2": sum(areas) / 1e6, "invalid": valid.count(0)}  # fmt: skip


def main() -> int:
    summary = json.loads((ROOT / "docs" / "summary.json").read_text())
    raw = ROOT / summary["raw"]
    gdf = gpd.read_parquet(PARQ)
    meta = json.loads(pq.read_schema(PARQ).metadata[b"geo"])
    col = meta["columns"]["geometry"]
    crs_id = col["crs"]["id"]
    print("geoparquet crs:", crs_id, "| rows:", len(gdf), "| geometry_types:", col["geometry_types"])
    con = duckdb.connect()
    duck_n = con.execute(f"select count(*) from read_parquet('{PARQ}')").fetchone()[0]
    result, bad = {}, []
    for d, s in summary["versions"].items():
        g = gdal_side(raw / d / f"shinsui_rinkaku_kita-inbanuma_{d}.zip")
        sub = gdf[gdf["source_file"].str.contains(d)]
        area_py = sub.to_crs(6677).area.sum() / 1e6
        b = list(sub.total_bounds)
        checks = {k: bool(v) for k, v in {
            "features_gdal_eq_json": g["features"] == s["features"],
            "rows_eq_features": len(sub) == g["features"],
            "type": g["geometry_type"].replace(" ", "") == "MultiPolygon" and set(sub.geom_type) == {"MultiPolygon"},
            "epsg4326": g["epsg"] == "4326" and crs_id == {"authority": "EPSG", "code": 4326},
            "bbox": max(abs(x - y) for x, y in zip(b, g["bbox"])) < 5e-6,  # ogrinfo prints 6 decimals
            "area": abs(area_py - g["area_km2"]) / g["area_km2"] < TOL_AREA,
            "invalid": g["invalid"] == int((~sub.geometry.is_valid).sum()) == s["invalid"],
        }.items()}
        result[d] = {"gdal": g, "parquet": {"rows": len(sub), "bbox": b, "area_km2": area_py,
                                            "invalid": int((~sub.geometry.is_valid).sum())}, "checks": checks}  # fmt: skip
        bad += [f"{d}:{k}" for k, v in checks.items() if not v]
        print(d, "gdal", g["features"], round(g["area_km2"], 6), "| parquet", len(sub), round(area_py, 6), "|", "OK" if all(checks.values()) else "NG")
    total_ok = duck_n == len(gdf) == sum(r["parquet"]["rows"] for r in result.values())
    print("duckdb rows:", duck_n, "| total rows match:", total_ok)
    (ROOT / "docs" / "verification.json").write_text(json.dumps({"duckdb_rows": duck_n, "versions": result, "mismatches": bad}, indent=1) + "\n")
    if bad or not total_ok:
        print("MISMATCH", bad)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
