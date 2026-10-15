"""G3 step 2a — real import + lazy-construction check for the carried unit-1 code.

1. Imports every carried module; fails if any import raises, or if any backend
   module outside the carried set gets loaded (proves the closure is complete).
2. Builds the lazily-created clients that need extra packages at call time:
   the Qdrant HTTP client (http2 -> h2) and the OpenAI embeddings client.
   No network call is made: nothing is sent to Qdrant or OpenAI.
Run from the repo root: python scripts/smoke_import.py
"""

from __future__ import annotations

import asyncio
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


async def lazy_clients() -> list[str]:
    errors: list[str] = []
    from backend.core.qdrant_db import QdrantClient

    qc = QdrantClient(qdrant_url="http://127.0.0.1:1", collection_name="showroom_legal_synthetic")
    try:
        await qc._get_client()  # builds httpx.AsyncClient(http2=True); no request is sent
    except Exception as exc:  # noqa: BLE001
        errors.append(f"QdrantClient._get_client: {type(exc).__name__}: {exc}")
    finally:
        await qc.close()
    try:
        from backend.core.embeddings import EmbeddingsGenerator

        EmbeddingsGenerator(provider="openai", api_key="sk-showroom-smoke-not-a-key")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"EmbeddingsGenerator(openai): {type(exc).__name__}: {exc}")
    return errors


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
    lazy = asyncio.run(lazy_clients()) if not failed else ["dilewati: import gagal"]
    for line in lazy:
        print(f"GAGAL {line}")
    print(f"klien malas: {2 - len(lazy)}/2 OK (Qdrant http2, OpenAI)")
    return 1 if failed or leaked or lazy else 0


if __name__ == "__main__":
    raise SystemExit(main())
