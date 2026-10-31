#!/usr/bin/env python3
"""Build data/parquet/inundation_kita_inbanuma.parquet (GeoParquet, EPSG:4326) from raw/<date>/ and write docs/summary.json.

    uv run python scripts/02_build.py [raw/<date>]
"""

import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from convert import declared_crs, parse_page_versions, read_features, rows_from_features, summarize


def main() -> None:
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((ROOT / "raw").glob("20*"))[-1]
    manifest = json.loads((raw / "MANIFEST.json").read_text())
    html = (raw / "pages" / "R8_taihuu25gou.html").read_text(encoding="utf-8")
    versions = parse_page_versions(html)
    rows, summary = [], {}
    for v in sorted(versions, key=lambda v: v["version_time"]):
        d = v["file_date"]
        gj = [m for m in manifest["files"] if m.get("kind") == "geojson_extracted" and m["path"].endswith(".geojson") and m["file_date"] == d]
        assert len(gj) == 1, (d, gj)
        zipm = next(m for m in manifest["files"] if m.get("kind") == "geojson_zip" and m["file_date"] == d)
        pdfm = next(m for m in manifest["files"] if m.get("kind") == "pdf" and m["file_date"] == d)
        path = ROOT / gj[0]["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == gj[0]["sha256"]
        meta, feats = read_features(path)
        base = {"version_time": v["version_time"], "published": v["published"], "source_url": v["zip_url"],
                "source_file": zipm["path"].split("/", 2)[2], "geojson_member": gj[0]["zip_member"],
                "geojson_sha256": gj[0]["sha256"], "pdf_url": pdfm["url"], "pdf_sha256": pdfm["sha256"]}  # fmt: skip
        rows += rows_from_features(feats, base)
        s = summarize(feats)
        s.update(version_time=v["version_time"], published=v["published"], file_date=d, declared_crs=declared_crs(meta),
                 geojson_members_features=len(feats))  # fmt: skip
        summary[d] = s
    df = pd.DataFrame(rows)
    geom = [shape(g) for g in df.pop("geometry_obj")]
    gdf = gpd.GeoDataFrame(df, geometry=geom, crs="EPSG:4326")
    gdf["version_time"] = pd.to_datetime(gdf["version_time"])  # tz-aware +09:00
    gdf["published"] = pd.to_datetime(gdf["published"]).dt.date
    out = ROOT / "data" / "parquet"
    out.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(out / "inundation_kita_inbanuma.parquet", index=False, compression="zstd", write_covering_bbox=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "summary.json").write_text(json.dumps({"raw": str(raw.relative_to(ROOT)), "rows": len(gdf), "versions": summary}, indent=1, ensure_ascii=False) + "\n")
    print(len(gdf), "rows;", {d: s["features"] for d, s in summary.items()})


if __name__ == "__main__":
    main()
