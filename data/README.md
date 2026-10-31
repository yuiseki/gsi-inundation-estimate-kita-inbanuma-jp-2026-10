---
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
4 rows (one MultiPolygon per version), with the original files kept unchanged.

**Credit.** 出典：国土地理院ウェブサイト <https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html>
(「令和8年台風25号による浸水推定図「北印旛沼」」の浸水範囲の輪郭線GeoJSON).
**Processed.** The Parquet was made from these GeoJSON files by yuiseki (columns added, properties kept as they were, geometry not
changed): 「令和8年台風25号による浸水推定図「北印旛沼」」（国土地理院）をもとに yuiseki が GeoParquet に加工して作成.
This is not a publication of GSI, and nothing here is to be shown as if GSI had made it.

## Source

- Page: <https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html> (令和8年（2026年）台風第25号に関する情報), read on 2026-10-31
  (fetch started 2026-10-31T07:43:11+00:00 UTC). The page lists 1 product, 浸水推定図, with 4 versions of 北印旛沼; all 4 were fetched. The page
  saved is `raw/2026-10-31/pages/R8_taihuu25gou.html`.
- Files: <https://www1.gsi.go.jp/geowww/saigai/20260922_typhoon25/> `shinsui_rinkaku_kita-inbanuma_<YYYYMMDD>.zip` (GeoJSON, ZIP) and
  `shinsui_kita-inbanuma_<YYYYMMDD>.pdf` (PDF of the map). The date in a file name is not always the basis date: see the table.
- Fetch: `scripts/01_fetch.py`, one request at a time, 2 seconds apart, 22 entries in `raw/2026-10-31/MANIFEST.json`
  (url, bytes, sha256, Last-Modified when served). Only www.gsi.go.jp and www1.gsi.go.jp were asked. These hosts need TLS legacy
  renegotiation, which the script turns on for its own connections only.
- Kept unchanged in `raw/2026-10-31/`: the 2 pages, the 4 ZIPs, the GeoJSON, the two text files in each ZIP (the terms and the 免責事項)
  taken out of the ZIPs, and the 4 PDFs. The PDFs are published here because the terms allow it; their sha256 is in the MANIFEST and below.

## Versions

| basis time (+09:00) | published | file date | features | geometry | polygons | interior rings | invalid | area, km2 (EPSG:6677) | bbox (lon/lat, EPSG:4326) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-22T14:00:00+09:00 | 2026-09-24 | `20260922` | 1 | MultiPolygon | 497 | 314 | 0 | 5.596 | 140.2376, 35.7646, 140.2771, 35.8300 |
| 2026-09-24T14:00:00+09:00 | 2026-09-24 | `20260924` | 1 | MultiPolygon | 499 | 289 | 0 | 4.939 | 140.2229, 35.7646, 140.2731, 35.8297 |
| 2026-09-25T11:00:00+09:00 | 2026-09-25 | `20260925` | 1 | MultiPolygon | 147 | 290 | 0 | 3.151 | 140.2508, 35.7747, 140.2727, 35.8257 |
| 2026-10-01T16:00:00+09:00 | 2026-10-02 | `20261001` | 1 | MultiPolygon | 286 | 262 | 0 | 1.318 | 140.2509, 35.7844, 140.2681, 35.8231 |

"published" is the date in the page's own words (e.g. 「令和8年10月1日16時時点（10月2日公開）」); the page gives no year for it, and the year of the
basis time is used. The 2026-09-22 14:00 version was published on 2026-09-24, the same day as the 2026-09-24 14:00 version.

Areas of the outline, the sum over the polygons, projected to EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX) with GDAL
(`ST_Transform`, `ST_Area`), in the order of the basis time: 5.596 -> 4.939 -> 3.151 -> 1.318 km2 (smaller each time). The number of polygons in that order is
497, 499, 147, 286; the west edge of the bounding box is at longitude
140.2376, 140.2229, 140.2508, 140.2509. These are facts about the files; what they mean is not in this card.

## Columns

One row per feature of the original GeoJSON (each file has 1 feature).

| column | type | meaning |
|---|---|---|
| `version_time` | timestamp, +09:00 | the basis time stated on the page (時点) |
| `published` | date | the publication date stated on the page (公開) |
| `source_url` | string | URL of the ZIP |
| `source_file` | string | the ZIP, relative to `raw/2026-10-31/` |
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
  versions. Invalid geometries: 0 in total (counted, not repaired).
- The area in the table is computed here, not given by GSI.

## Verification

`scripts/03_verify.py` reads the same ZIPs with GDAL (`ogrinfo` on `/vsizip/`) and the Parquet with geopandas, pyarrow and DuckDB.
DuckDB counts 4 rows. Every check passed (feature count = rows, geometry type, EPSG:4326, bounding box within 5e-6
degrees, area within a relative 1e-6, invalid count).

| file date | features by GDAL | rows in Parquet | area by GDAL, km2 | area by geopandas, km2 | invalid by GDAL |
|---|---|---|---|---|---|
| `20260922` | 1 | 1 | 5.595775 | 5.595775 | 0 |
| `20260924` | 1 | 1 | 4.939247 | 4.939247 | 0 |
| `20260925` | 1 | 1 | 3.150949 | 3.150949 | 0 |
| `20261001` | 1 | 1 | 1.317702 | 1.317702 | 0 |

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
saved as `raw/2026-10-31/pages/kikakuchousei40182.html`) apply the Public Data License 1.0 (PDL1.0). PDL1.0 is described by the Digital Agency as compatible with CC BY 4.0; that statement is not on
the pages saved in this fetch and was not re-checked here. The page of the typhoon says: 「以下の提供情報は出典を明示いただくだけで転載も含めご自由にお使いいただけます」 and
「国土地理院コンテンツ利用規約に従い、出典を明示いただくだけで、転載も含めご自由にお使いいただけます。」
Hence `license: other` with the terms named. Credit GSI, say that the data was processed, and do not present it as made by GSI. See `LICENSE`. The code in `src/` and `scripts/` is MIT.

## PDFs (published here)

| file | bytes | sha256 |
|---|---|---|
| `raw/2026-10-31/20260922/shinsui_kita-inbanuma_20260922.pdf` | 7,718,104 | `66b81cc5e9969911f6545a707ccec278369aaa63654469566abcc29a3202a7fa` |
| `raw/2026-10-31/20260924/shinsui_kita-inbanuma_20260924.pdf` | 7,636,523 | `3207645dee6197c536e2dbe0a406b3c634d93efa677aef7eb3837c71a9ec352f` |
| `raw/2026-10-31/20260925/shinsui_kita-inbanuma_20260925.pdf` | 7,521,448 | `899478d8933cf20594fbb47bc4a843a70c5325483971db93b391578b15e7dd33` |
| `raw/2026-10-31/20261001/shinsui_kita-inbanuma_20261001.pdf` | 7,500,247 | `fe11dcfba292adeb0fc48fa4f55983bd0b5b1bd911a0d38d0509510652b12dc6` |

## Files

```
README.md  LICENSE  provenance.yaml        (this card, the terms, the provenance; local copies are in data/)
parquet/inundation_kita_inbanuma.parquet   (499,086 bytes)
raw/2026-10-31/   pages, the 4 ZIPs, their contents, the 4 PDFs, MANIFEST.json
docs/             summary.json, verification.json, the PNG
scripts/ src/   (MIT, see the repository LICENSE notes in data/LICENSE)
```

Rebuild: `uv run python scripts/01_fetch.py && uv run python scripts/02_build.py && uv run python scripts/03_verify.py`.
