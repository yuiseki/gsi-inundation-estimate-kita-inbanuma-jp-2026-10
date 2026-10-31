#!/usr/bin/env python3
"""AFTER publication only: read the repository back from the Hub at the recorded revision and compare it with the local copy
(checksums of every file, the Parquet schema, cells, and the column non-null counts).

    uv run python scripts/06_verify_hub.py   # needs docs/revision.json from src/publish.py --push

Not run before publication.
"""

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from publish import collect, sha256


def main() -> int:
    rev = json.loads((ROOT / "docs" / "revision.json").read_text())
    repo, sha = rev["repo"], rev["revision"]
    cache = ROOT / "hub_readback"
    local = collect()
    listed = set(HfApi().list_repo_files(repo, repo_type="dataset", revision=sha))
    bad = [f"not on the Hub: {k}" for k in rev["sha256"] if k not in listed]
    for name, want in rev["sha256"].items():
        p = Path(hf_hub_download(repo, name, repo_type="dataset", revision=sha, local_dir=cache))
        if sha256(p) != want:
            bad.append(f"checksum {name}")
        if name in local and sha256(local[name]) != want and name != "docs/revision.json":
            bad.append(f"local copy changed since the push: {name}")
    tables = {}
    for name in rev["sha256"]:
        if name.endswith(".parquet"):
            hub, mine = pq.read_table(cache / name), pq.read_table(local[name])
            if not hub.schema.equals(mine.schema, check_metadata=True):
                bad.append(f"schema {name}")
            if not hub.equals(mine):
                bad.append(f"cells {name}")
            tables[name] = {"rows": hub.num_rows, "non_null": {c: hub.num_rows - hub[c].null_count for c in hub.column_names}}
    try:
        from datasets import load_dataset  # noqa: F401  (optional: the card's config loads)
    except ImportError:
        pass
    out = {"repo": repo, "revision": sha, "files_checked": len(rev["sha256"]), "files_on_hub": len(listed), "tables": tables, "problems": bad}
    (ROOT / "docs" / "verify_hub.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(bad) if bad else f"OK: the repository at {sha} equals the local copy")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
