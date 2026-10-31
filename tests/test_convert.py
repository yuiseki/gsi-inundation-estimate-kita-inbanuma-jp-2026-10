import json

import pytest
from shapely.geometry import box, shape

from convert import area_km2, declared_crs, read_features, summarize


def fc(features, crs=None):
    d = {"type": "FeatureCollection", "features": features}
    if crs:
        d["crs"] = {"type": "name", "properties": {"name": crs}}
    return d


SQ = {"type": "Feature", "properties": {"a": 1}, "geometry": {"type": "Polygon", "coordinates": [[[140.2, 35.7], [140.21, 35.7], [140.21, 35.71], [140.2, 35.71], [140.2, 35.7]]]}}


def test_read_features(tmp_path):
    p = tmp_path / "a.geojson"
    p.write_text(json.dumps(fc([SQ], "urn:ogc:def:crs:OGC:1.3:CRS84")))
    meta, feats = read_features(p)
    assert len(feats) == 1 and declared_crs(meta) == "urn:ogc:def:crs:OGC:1.3:CRS84"


def test_not_featurecollection(tmp_path):
    p = tmp_path / "a.geojson"
    p.write_text(json.dumps({"type": "Feature"}))
    with pytest.raises(ValueError):
        read_features(p)


def test_area_about_one_km2():
    # 0.01 deg x 0.01 deg at 35.7N is about 0.9 x 1.1 km
    assert 0.9 < area_km2(shape(SQ["geometry"])) < 1.1


def test_summarize_counts_invalid_without_repair():
    bow = {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}}
    s = summarize([SQ, bow])
    assert s["features"] == 2 and s["invalid"] == 1 and s["geometry_types"] == ["Polygon"]
    assert box(*s["bounds"]).area > 0


from convert import parse_page_versions, rows_from_features

HTML = ('令和8年台風25号による浸水推定図「北印旛沼」　令和8年10月1日16時時点（10月2日公開）<a href="https://www1.gsi.go.jp/geowww/saigai/x/shinsui_rinkaku_kita-inbanuma_20261001.zip">z</a>'
        '令和8年台風第25号による浸水推定図「北印旛沼」　令和8年9月22日14時時点（9月24日公開）<a href="https://www1.gsi.go.jp/geowww/saigai/x/shinsui_rinkaku_kita-inbanuma_20260922.zip">z</a>')


def test_parse_page_versions():
    v = parse_page_versions(HTML)
    assert [x["version_time"] for x in v] == ["2026-10-01T16:00:00+09:00", "2026-09-22T14:00:00+09:00"]
    assert [x["published"] for x in v] == ["2026-10-02", "2026-09-24"]
    assert v[0]["file_date"] == "20261001"


def test_parse_page_versions_mismatch():
    with pytest.raises(ValueError):
        parse_page_versions(HTML.replace("shinsui_rinkaku_kita-inbanuma_20260922.zip", "x.zip"))


def test_rows_keep_properties():
    f = {"type": "Feature", "properties": {"FID": 0, "_color": "#fff"}, "geometry": SQ["geometry"]}
    r = rows_from_features([f], {"version_time": "t"})[0]
    assert json.loads(r["properties_json"]) == {"FID": 0, "_color": "#fff"}
    assert r["FID"] == "0" and r["_color"] == "#fff" and r["geometry_obj"] == SQ["geometry"]
