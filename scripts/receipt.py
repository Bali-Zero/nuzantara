"""Write a local-CI receipt bound to the exact commit (SHOWROOM L2).

Runs the test suite and records commit, cleanliness, platform, Python, Qdrant version,
embedding mode, counts and stated limitations in .showroom-data/receipts/<sha>-<mode>.json.
A receipt from a dirty tree is marked invalid. Exit code = pytest exit code.
Run: python scripts/receipt.py            (mock suite only)
     SHOWROOM_INTEGRATION=1 python scripts/receipt.py   (adds real-Qdrant tests)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def qdrant_version() -> str | None:
    if os.environ.get("SHOWROOM_INTEGRATION") != "1":
        return None
    try:
        import httpx

        return httpx.get(os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"), timeout=3).json().get("version")
    except Exception as exc:  # noqa: BLE001
        return f"unreachable: {type(exc).__name__}"


def main() -> int:
    out_dir = ROOT / ".showroom-data" / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    junit = out_dir / "last-junit.xml"
    rc = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", f"--junitxml={junit}"], cwd=ROOT).returncode
    suite = ET.parse(junit).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    counts = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    sha, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    mode = os.environ.get("SHOWROOM_EMBEDDINGS", "lexical") if os.environ.get("SHOWROOM_INTEGRATION") == "1" else "mock-only"
    receipt = {
        "commit": sha, "branch": git("branch", "--show-current"), "tree_clean": not dirty,
        "valid": (not dirty) and rc == 0,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version()},
        "qdrant_version": qdrant_version(), "embeddings_mode": mode, "min_score": os.environ.get("SHOWROOM_MIN_SCORE", "default 0.35"),
        "pytest_exit": rc, "counts": counts,
        "limitations": [
            "lexical/mock embeddings prove wiring and failure handling, not semantic quality",
            "CONTRACT A1/A2 are closed only by a receipt with embeddings_mode=openai",
        ],
    }
    dest = out_dir / f"{sha[:10]}-{mode}.json"
    dest.write_text(json.dumps(receipt, indent=2))
    print(f"receipt: {dest.relative_to(ROOT)} · valid={receipt['valid']} · {counts} · mode={mode}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
