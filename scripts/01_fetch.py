#!/usr/bin/env python3
"""Fetch the source page, the terms page, and every 北印旛沼 version (GeoJSON ZIP + PDF) listed on the page.

    uv run python scripts/01_fetch.py            # writes raw/<UTC date>/ and MANIFEST.json

The list of versions is read from the page itself (every shinsui_rinkaku_kita-inbanuma_*.zip link and
its PDF), so versions added to the page are picked up. One request at a time, 2 s apart.
"""

import hashlib
import json
import re
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import fetch

PAGE = "https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html"
TERMS = "https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html"
ZIP_RE = re.compile(r'href="(https://www1\.gsi\.go\.jp/geowww/saigai/[^"]*/shinsui_rinkaku_kita-inbanuma_(\d{8})\.zip)"')


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    now = datetime.now(UTC)
    out = ROOT / "raw" / now.strftime("%Y-%m-%d")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched_at_utc": now.isoformat(timespec="seconds"), "files": []}

    def save(url: str, rel: str, extra: dict | None = None) -> bytes:
        body, hdr = fetch.get(url)
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        manifest["files"].append({"path": f"raw/{out.name}/{rel}", "url": url, "bytes": len(body), "sha256": sha(body),
                                  "last_modified": hdr.get("Last-Modified"), "etag": hdr.get("ETag"), **(extra or {})})  # fmt: skip
        print("saved", rel, len(body))
        return body

    page = save(PAGE, "pages/R8_taihuu25gou.html")
    save(TERMS, "pages/kikakuchousei40182.html")
    text = page.decode("utf-8")
    versions = sorted(set(ZIP_RE.findall(text)), key=lambda t: t[1])
    print("versions on the page:", [d for _, d in versions])
    for zurl, date in versions:
        save(zurl, f"{date}/shinsui_rinkaku_kita-inbanuma_{date}.zip", {"kind": "geojson_zip", "file_date": date})
        zp = out / date / f"shinsui_rinkaku_kita-inbanuma_{date}.zip"
        with zipfile.ZipFile(zp) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                data = z.read(info)
                name = Path(info.filename).name
                (out / date / name).write_bytes(data)
                manifest["files"].append({"path": f"raw/{out.name}/{date}/{name}", "from_zip": zp.name, "zip_member": info.filename,
                                          "bytes": len(data), "sha256": sha(data), "kind": "geojson_extracted", "file_date": date})  # fmt: skip
                print("  extracted", name, len(data))
        purl = zurl.replace("shinsui_rinkaku_kita-inbanuma_", "shinsui_kita-inbanuma_").replace(".zip", ".pdf")
        save(purl, f"{date}/shinsui_kita-inbanuma_{date}.pdf", {"kind": "pdf", "file_date": date})
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
