#!/usr/bin/env python3
"""Push the card, licence, provenance, raw files, Parquet, scripts and docs.

uv run python src/publish.py             # dry run: list the files and their sizes (the default; nothing is sent)
uv run python src/publish.py --push      # one commit; prints the sha and writes docs/revision.json (NOT to be run without approval)
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/gsi-inundation-estimate-kita-inbanuma-jp-2026-10"


def collect() -> dict[str, Path]:
    """path in the repo -> local file. The card is the repo's README.md."""
    card = (DATA / "README.md").read_text(encoding="utf-8")
    if "license: other" not in card or "license_name:" not in card:
        raise SystemExit("the card does not declare license: other with a license_name")
    summ = json.loads((ROOT / "docs" / "summary.json").read_text())
    ver = json.loads((ROOT / "docs" / "verification.json").read_text())
    if ver["mismatches"]:
        raise SystemExit(f"verification has mismatches: {ver['mismatches']}")
    if "出典：国土地理院ウェブサイト" not in card or "加工して作成" not in card:
        raise SystemExit("the card lacks the credit or the processing notice")
    files: dict[str, Path] = {"README.md": DATA / "README.md", "LICENSE": DATA / "LICENSE", "provenance.yaml": DATA / "provenance.yaml"}  # fmt: skip
    for p in sorted((DATA / "parquet").glob("*.parquet")):
        files[f"parquet/{p.name}"] = p
    raw = ROOT / summ["raw"]
    if not (raw / "MANIFEST.json").is_file():
        raise SystemExit("missing MANIFEST.json")
    for p in sorted(raw.rglob("*")):
        if p.is_file():
            files[p.relative_to(ROOT).as_posix()] = p
    for p in sorted((ROOT / "docs").glob("*")):
        if p.is_file() and p.name != "revision.json":
            files[f"docs/{p.name}"] = p
    for sub in ("scripts", "src"):
        for p in sorted((ROOT / sub).glob("*.py")):
            files[f"{sub}/{p.name}"] = p
    n = summ["rows"]
    pq = [k for k in files if k.endswith(".parquet")]
    if len(pq) != 1 or f"{n} rows" not in card:
        raise SystemExit("the card does not state the row count, or there is not exactly one Parquet")
    return files


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true", help="upload; needs the person's approval")
    a = ap.parse_args()
    files = collect()
    total = sum(p.stat().st_size for p in files.values())
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes")
    for k, v in files.items():
        print(f"  {v.stat().st_size:>12,}  {k}")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    ops = [CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(v)) for k, v in files.items()]
    c = api.create_commit(a.repo, ops, repo_type="dataset", commit_message="Add GSI inundation estimate of Kita-Inbanuma, 4 versions (Typhoon No. 25, 2026)")
    rev = {"repo": a.repo, "revision": c.oid, "pushed": datetime.now(UTC).isoformat(timespec="seconds"),
           "sha256": {k: sha256(v) for k, v in files.items()}}  # fmt: skip
    (ROOT / "docs" / "revision.json").write_text(json.dumps(rev, indent=1) + "\n")
    print(f"pushed {a.repo} revision {c.oid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
