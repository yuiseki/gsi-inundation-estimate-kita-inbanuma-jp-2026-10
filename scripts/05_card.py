#!/usr/bin/env python3
"""Write data/README.md, data/LICENSE and data/provenance.yaml. Every number comes from docs/summary.json,
docs/verification.json, the parquet and raw/<date>/MANIFEST.json.

    uv run python scripts/05_card.py
"""

import json
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
summ = json.loads((ROOT / "docs" / "summary.json").read_text())
ver = json.loads((ROOT / "docs" / "verification.json").read_text())
assert not ver["mismatches"]
raw = ROOT / summ["raw"]
man = json.loads((raw / "MANIFEST.json").read_text())
fetched = man["fetched_at_utc"]
g = gpd.read_parquet(DATA / "parquet" / "inundation_kita_inbanuma.parquet").sort_values("version_time")
pq_bytes = (DATA / "parquet" / "inundation_kita_inbanuma.parquet").stat().st_size
by = {m["path"].split("/")[-1]: m for m in man["files"]}
V = summ["versions"]
poly = {d: len(r.geometry.geoms) for d, (_, r) in zip(sorted(V), g.iterrows())}
holes = {d: sum(len(p.interiors) for p in r.geometry.geoms) for d, (_, r) in zip(sorted(V), g.iterrows())}

rows = []
for d in sorted(V):
    s, vv = V[d], ver["versions"][d]
    b = s["bounds"]
    rows.append(f"| {s['version_time']} | {s['published']} | `{d}` | {s['features']} | MultiPolygon | {poly[d]} | {holes[d]} | {s['invalid']} | {vv['gdal']['area_km2']:.3f} | {b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f}, {b[3]:.4f} |")
table = "\n".join(rows)
order = sorted(V)
areas = [V[d]["area_km2"] for d in order]
change = " -> ".join(f"{a:.3f}" for a in areas)
vrows = "\n".join(
    f"| `{d}` | {ver['versions'][d]['gdal']['features']} | {ver['versions'][d]['parquet']['rows']} | {ver['versions'][d]['gdal']['area_km2']:.6f} | {ver['versions'][d]['parquet']['area_km2']:.6f} | {ver['versions'][d]['gdal']['invalid']} |"
    for d in order
)
filerows = "\n".join(
    f"| `raw/{raw.name}/{d}/{n}` | {by[n]['bytes']:,} | `{by[n]['sha256']}` |"
    for d in order
    for n in (f"shinsui_kita-inbanuma_{d}.pdf",)
)

card = f"""---
license: other
license_name: gsi-content-terms-of-use-pdl-1.0
license_link: https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html
language:
- ja
tags:
- japan
- flood
- inundation
- typhoon
- gsi
- disaster
- geoparquet
- chiba
size_categories:
- n<1K
pretty_name: GSI inundation estimate, Kita-Inbanuma, Typhoon No. 25 of Reiwa 8 (4 versions, outlines)
configs:
- config_name: default
  data_files: parquet/inundation_kita_inbanuma.parquet
---

# gsi-inundation-estimate-kita-inbanuma-jp-2026-10

The outlines of the inundation extent estimated by the Geospatial Information Authority of Japan (GSI, 国土地理院) for
北印旛沼 (Kita-Inbanuma) after Typhoon No. 25 of Reiwa 8 (令和8年台風第25号), in the four versions GSI has published
(basis times 2026-09-22 14:00, 2026-09-24 14:00, 2026-09-25 11:00 and 2026-10-01 16:00, +09:00), as one GeoParquet of
{summ['rows']} rows (one MultiPolygon per version), with the original files kept unchanged.

**Credit.** 出典：国土地理院ウェブサイト <https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html>
(「令和8年台風25号による浸水推定図「北印旛沼」」の浸水範囲の輪郭線GeoJSON).
**Processed.** The Parquet was made from these GeoJSON files by yuiseki (columns added, properties kept as they were, geometry not
changed): 「令和8年台風25号による浸水推定図「北印旛沼」」（国土地理院）をもとに yuiseki が GeoParquet に加工して作成.
This is not a publication of GSI, and nothing here is to be shown as if GSI had made it.

## Source

- Page: <https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html> (令和8年（2026年）台風第25号に関する情報), read on {fetched[:10]}
  (fetch started {fetched} UTC). The page lists 1 product, 浸水推定図, with {len(V)} versions of 北印旛沼; all {len(V)} were fetched. The page
  saved is `raw/{raw.name}/pages/R8_taihuu25gou.html`.
- Files: <https://www1.gsi.go.jp/geowww/saigai/20260922_typhoon25/> `shinsui_rinkaku_kita-inbanuma_<YYYYMMDD>.zip` (GeoJSON, ZIP) and
  `shinsui_kita-inbanuma_<YYYYMMDD>.pdf` (PDF of the map). The date in a file name is not always the basis date: see the table.
- Fetch: `scripts/01_fetch.py`, one request at a time, 2 seconds apart, {len(man['files'])} entries in `raw/{raw.name}/MANIFEST.json`
  (url, bytes, sha256, Last-Modified when served). Only www.gsi.go.jp and www1.gsi.go.jp were asked. These hosts need TLS legacy
  renegotiation, which the script turns on for its own connections only.
- Kept unchanged in `raw/{raw.name}/`: the 2 pages, the 4 ZIPs, the GeoJSON, the two text files in each ZIP (the terms and the 免責事項)
  taken out of the ZIPs, and the 4 PDFs. The PDFs are published here because the terms allow it; their sha256 is in the MANIFEST and below.

## Versions

| basis time (+09:00) | published | file date | features | geometry | polygons | interior rings | invalid | area, km2 (EPSG:6677) | bbox (lon/lat, EPSG:4326) |
|---|---|---|---|---|---|---|---|---|---|
{table}

"published" is the date in the page's own words (e.g. 「令和8年10月1日16時時点（10月2日公開）」); the page gives no year for it, and the year of the
basis time is used. The 2026-09-22 14:00 version was published on 2026-09-24, the same day as the 2026-09-24 14:00 version.

Areas of the outline, the sum over the polygons, projected to EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX) with GDAL
(`ST_Transform`, `ST_Area`), in the order of the basis time: {change} km2 (smaller each time). The number of polygons in that order is
{', '.join(str(poly[d]) for d in order)}; the west edge of the bounding box is at longitude
{', '.join(f"{V[d]['bounds'][0]:.4f}" for d in order)}. These are facts about the files; what they mean is not in this card.

## Columns

One row per feature of the original GeoJSON (each file has {V[order[0]]['features']} feature).

| column | type | meaning |
|---|---|---|
| `version_time` | timestamp, +09:00 | the basis time stated on the page (時点) |
| `published` | date | the publication date stated on the page (公開) |
| `source_url` | string | URL of the ZIP |
| `source_file` | string | the ZIP, relative to `raw/{raw.name}/` |
| `geojson_member` | string | the GeoJSON inside the ZIP (the name differs: `輪郭線_.geojson` in the first version, `輪郭線.geojson` in the others) |
| `geojson_sha256` | string | sha256 of that GeoJSON as served |
| `pdf_url`, `pdf_sha256` | string | the PDF map of the same version |
| `feature_index` | int | position of the feature in the file |
| `properties_json` | string | the original `properties` of the feature as JSON, types as in the file |
| `FID`, `_color`, `_opacity`, `_weight`, `_fillColor`, `_fillOpacity` | string | the original properties as strings; empty when the file does not have it (see below) |
| `geometry` | WKB (GeoParquet) | MultiPolygon, EPSG:4326, as in the file |

The properties differ between the files: 2026-09-22 has only `FID` (the integer 0); 2026-09-24 and 2026-09-25 have the style properties
(`_color` ... `_fillOpacity`) and no `FID`; 2026-10-01 has `FID` (the string "0") and the style properties. `properties_json` keeps the
types. The style properties are display settings of the file, not measurements.

## Coordinate reference system

The GeoJSON files do not declare a CRS (no `crs` member). GDAL reads them as WGS 84 (EPSG:4326), as GeoJSON does by default, and the
coordinates are in the range of longitude 140.2 and latitude 35.8 (Inba, Chiba), which agrees. The GeoParquet declares EPSG:4326
(checked in `docs/verification.json`). Areas are computed in EPSG:6677; the Parquet itself is not projected.

## What was done, and what was not

- Done: the four GeoJSON files were read as they are; their coordinates were written to GeoParquet (zstd, with a bbox column) and
  the columns above were added. The coordinates in the Parquet are equal, number by number, to the coordinates in the GeoJSON (checked).
- Not done: no correction, no repair of geometry, no simplification, no reprojection, no clipping, no filling of gaps, no merging of the
  versions. Invalid geometries: {sum(s['invalid'] for s in V.values())} in total (counted, not repaired).
- The area in the table is computed here, not given by GSI.

## Verification

`scripts/03_verify.py` reads the same ZIPs with GDAL (`ogrinfo` on `/vsizip/`) and the Parquet with geopandas, pyarrow and DuckDB.
DuckDB counts {ver['duckdb_rows']} rows. Every check passed (feature count = rows, geometry type, EPSG:4326, bounding box within 5e-6
degrees, area within a relative 1e-6, invalid count).

| file date | features by GDAL | rows in Parquet | area by GDAL, km2 | area by geopandas, km2 | invalid by GDAL |
|---|---|---|---|---|---|
{vrows}

The figure `docs/inundation_kita_inbanuma_4versions.png` draws the four versions side by side.

## Known problems, as GSI states them

On the page, under 1.浸水推定図: 「この地図は、国土地理院が、標高データ及び国土交通省災害対策用ヘリコプターによる撮影画像を用いて、浸水範囲を推定し、浸水の深さを色の濃淡で表現したものです。利用した画像の撮影時点における情報であるため、最大浸水範囲を示したものではありません。また、実際には、未着色範囲でも浸水している可能性や、着色範囲でも浸水していない可能性があります。」

In the 免責事項.txt of every ZIP (for the 10-01 version; the other versions name their own shooting time): 「このデータは、国土地理院が、標高データ及び国土交通省災害対策用ヘリコプターによる10月1日16時頃の撮影画像を用いて推定した浸水範囲の輪郭線データです。ファイル形式はGeoJSON形式です。利用した画像の撮影時点における情報であるため、最大浸水範囲を示したものではありません。また、実際には、輪郭線の外側でも浸水している可能性や、輪郭線の内側でも浸水していない可能性があります。」

In short: it is the state at the time of the images, not the maximum extent; water may be outside the outline, and not everywhere inside it.
The map GSI draws has depths as shades; the outline files here do not carry depth. The PDFs show the map as GSI drew it.

Other points found while building this:

- The page does not state the year of the publication dates; it is taken from the basis time (see above).
- The first version's GeoJSON is written with 15 decimals and the others with 6; this is how they were served.

## Licence

GSI's content terms (国土地理院コンテンツ利用規約, <https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html>, amended 2025-11-20,
saved as `raw/{raw.name}/pages/kikakuchousei40182.html`) apply the Public Data License 1.0 (PDL1.0). PDL1.0 is described by the Digital Agency as compatible with CC BY 4.0; that statement is not on
the pages saved in this fetch and was not re-checked here. The page of the typhoon says: 「以下の提供情報は出典を明示いただくだけで転載も含めご自由にお使いいただけます」 and
「国土地理院コンテンツ利用規約に従い、出典を明示いただくだけで、転載も含めご自由にお使いいただけます。」
Hence `license: other` with the terms named. Credit GSI, say that the data was processed, and do not present it as made by GSI. See `LICENSE`. The code in `src/` and `scripts/` is MIT.

## PDFs (published here)

| file | bytes | sha256 |
|---|---|---|
{filerows}

## Files

```
README.md  LICENSE  provenance.yaml        (this card, the terms, the provenance; local copies are in data/)
parquet/inundation_kita_inbanuma.parquet   ({pq_bytes:,} bytes)
raw/{raw.name}/   pages, the 4 ZIPs, their contents, the 4 PDFs, MANIFEST.json
docs/             summary.json, verification.json, the PNG
scripts/ src/   (MIT, see the repository LICENSE notes in data/LICENSE)
```

Rebuild: `uv run python scripts/01_fetch.py && uv run python scripts/02_build.py && uv run python scripts/03_verify.py`.
"""
(DATA / "README.md").write_text(card, encoding="utf-8")

(DATA / "LICENSE").write_text(f"""GSI Content Terms of Use (国土地理院コンテンツ利用規約), applying the Public Data License version 1.0 (公共データ利用規約 第1.0版, PDL1.0),
which is described as compatible with Creative Commons Attribution 4.0 International (CC BY 4.0) (not re-checked in this fetch).
https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html
https://www.digital.go.jp/resources/open_data/public_data_license_v1.0
https://creativecommons.org/licenses/by/4.0/legalcode

Everything under this directory comes from the 浸水推定図「北印旛沼」 (令和8年台風第25号) published by the Geospatial Information Authority of
Japan (GSI, 国土地理院) at https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html, read on {fetched[:10]}.

The terms, amended on 2025-11-20 and saved in raw/{raw.name}/pages/kikakuchousei40182.html, say: 「本サイトのコンテンツには特段の記載が無い限り
公共データ利用規約（第1.0 版）（PDL1.0）が適用されています。」 They require the source to be credited (「出典：国土地理院ウェブサイト （当該ページのURL）」), require
edited or processed content to say so separately from the credit, and forbid presenting edited content as if GSI had made it
(「編集・加工した情報を、あたかも国土地理院が作成したかのような態様で公表・利用してはいけません。」).
The typhoon page says: 「以下の提供情報は出典を明示いただくだけで転載も含めご自由にお使いいただけます」 and
「国土地理院コンテンツ利用規約に従い、出典を明示いただくだけで、転載も含めご自由にお使いいただけます。」

Credit: 出典：国土地理院ウェブサイト https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html
Processed: 「令和8年台風25号による浸水推定図「北印旛沼」」（国土地理院）をもとに yuiseki が GeoParquet に加工して作成

GSI's notice for these data: the estimate is the state at the time of the images, not the maximum extent; water may be outside the outline
and may not be inside it everywhere (see the card and each 免責事項.txt in raw/).
The source code in src/ and scripts/ is MIT licensed (see the GitHub repository).
""", encoding="utf-8")

(DATA / "provenance.yaml").write_text(f"""source: 国土地理院 浸水推定図「北印旛沼」(令和8年台風第25号)
url: https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html
files_url: https://www1.gsi.go.jp/geowww/saigai/20260922_typhoon25/
terms: https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html
license: 国土地理院コンテンツ利用規約 (公共データ利用規約 第1.0版, CC BY 4.0 互換)
fetched_at_utc: "{fetched}"
raw: raw/{raw.name}/ (MANIFEST.json has url, bytes, sha256)
versions:
""" + "".join(f"""  - file_date: "{d}"
    version_time: "{V[d]['version_time']}"
    published: "{V[d]['published']}"
    features: {V[d]['features']}
    area_km2_epsg6677: {ver['versions'][d]['gdal']['area_km2']:.6f}
    geojson_sha256: {g[g.source_file.str.contains(d)].geojson_sha256.iloc[0]}
    zip_sha256: {by[f'shinsui_rinkaku_kita-inbanuma_{d}.zip']['sha256']}
""" for d in order) + f"""rows: {summ['rows']}
processing: read GeoJSON as served, wrote GeoParquet (EPSG:4326), added columns; no correction, repair, simplification or reprojection
""", encoding="utf-8")
print("written")
