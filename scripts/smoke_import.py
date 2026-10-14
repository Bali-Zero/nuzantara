"""G3 step 2a — real import check for the carried unit-1 code.

Imports every carried module and fails if any import raises, or if any backend
module outside the carried set gets loaded (proves the closure is complete).
Run from the repo root: python scripts/smoke_import.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CARRIED = """
backend.app.core.config backend.app.core.database backend.app.utils.tracing
backend.core.bm25_vectorizer backend.core.collection_registry backend.core.embeddings
backend.core.exceptions backend.core.legal.chunker backend.core.legal.constants
backend.core.legal.hierarchical_indexer backend.core.legal.quality_validators
backend.core.legal.structure_parser backend.core.pg_json_codec backend.core.qdrant_db
backend.services.llm_clients.pricing backend.services.observability
backend.services.observability.llm_cost_recorder
backend.services.observability.tracking_decorator
backend.services.search.citation_service
""".split()

PACKAGES = {
    "backend", "backend.app", "backend.app.core", "backend.app.utils", "backend.core",
    "backend.core.legal", "backend.services", "backend.services.llm_clients",
    "backend.services.search",
}


def main() -> int:
    failed = 0
    for name in CARRIED:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 — report every failure
            failed += 1
            print(f"GAGAL {name}: {type(exc).__name__}: {exc}")
    allowed = set(CARRIED) | PACKAGES
    leaked = sorted(m for m in sys.modules if m.startswith("backend") and m not in allowed)
    tk = "ya" if "tiktoken" in sys.modules else "tidak"
    print(f"import: {len(CARRIED) - failed}/{len(CARRIED)} modul OK; "
          f"modul backend di luar daftar: {len(leaked)} {leaked if leaked else ''}; tiktoken termuat: {tk}")
    return 1 if failed or leaked else 0


if __name__ == "__main__":
    raise SystemExit(main())
