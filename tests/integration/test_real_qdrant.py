"""Unit-1 acceptance against a REAL Qdrant (G4). Skipped unless SHOWROOM_INTEGRATION=1.

Evidence level depends on SHOWROOM_EMBEDDINGS:
* ``lexical`` (default) — real Qdrant + deterministic lexical embeddings. Proves the
  carried QdrantClient/HierarchicalIndexer against a real server; NOT semantic quality.
* ``openai`` — real Qdrant + real ``text-embedding-3-small`` (needs OPENAI_API_KEY).
  This is the only mode that may close CONTRACT §6 A1/A2 and calibrate SHOWROOM_MIN_SCORE.
The collection ``showroom_legal_synthetic`` is dropped and rebuilt on every run, on the
local Qdrant named by QDRANT_URL only (refuses non-localhost URLs).
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest

from showroom import pipeline

pytestmark = pytest.mark.skipif(
    os.environ.get("SHOWROOM_INTEGRATION") != "1", reason="set SHOWROOM_INTEGRATION=1 (needs local Qdrant)"
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = sorted((ROOT / "corpus").glob("*.txt"))
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
MODE = os.environ.get("SHOWROOM_EMBEDDINGS", "lexical")


def _embeddings():
    if MODE == "openai":
        from backend.core.embeddings import EmbeddingsGenerator

        return EmbeddingsGenerator(provider="openai")
    from tests.fakes import LexicalEmbeddings

    return LexicalEmbeddings()


async def _fresh_index():
    from backend.core.qdrant_db import QdrantClient

    host = urlparse(QDRANT_URL).hostname
    assert host in ("127.0.0.1", "localhost"), f"refusing to drop a collection on {host}"
    async with httpx.AsyncClient(base_url=QDRANT_URL, timeout=10) as raw:
        await raw.delete(f"/collections/{pipeline.COLLECTION}")
    qc = QdrantClient(qdrant_url=QDRANT_URL, collection_name=pipeline.COLLECTION)
    assert await qc.create_collection(vector_size=1536), "create_collection failed"
    emb = _embeddings()
    for path in CORPUS:
        res = await pipeline.ingest(path.read_text(), path.stem, qdrant=qc, embeddings=emb)
        assert res["chunks_upserted"] == res["chunks_indexed"] > 0, res
    stats = await qc.get_stats()
    assert stats.get("total_documents") == 10, stats  # 10 Pasal in the synthetic corpus
    return qc, emb


def test_real_qdrant_a1_a2_and_point_count():
    from tests.test_acceptance import IN_CORPUS, OUT_OF_CORPUS

    async def go():
        qc, emb = await _fresh_index()
        a1 = await pipeline.answer(IN_CORPUS[0], qdrant=qc, embeddings=emb)
        ins = [await pipeline.answer(q, qdrant=qc, embeddings=emb) for q in IN_CORPUS]
        outs = [await pipeline.answer(q, qdrant=qc, embeddings=emb) for q in OUT_OF_CORPUS]
        await qc.close()
        return a1, ins, outs

    a1, ins, outs = asyncio.run(go())
    assert a1["status"] == "supported", a1
    assert a1["sources"][0]["document_id"] == "perdes-sintetis-01-air-bersih"
    assert str(a1["sources"][0]["pasal"]) == "2"
    assert [o["status"] for o in ins] == ["supported"] * len(ins)
    assert [o["status"] for o in outs] == ["unsupported"] * len(outs)


def test_real_qdrant_a3_wrong_port_is_unavailable_within_timeout():
    from backend.core.qdrant_db import QdrantClient

    async def go():
        qc = QdrantClient(qdrant_url="http://127.0.0.1:9", collection_name=pipeline.COLLECTION)
        t0 = time.monotonic()
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=_embeddings())
        await qc.close()
        return out, time.monotonic() - t0

    out, elapsed = asyncio.run(go())
    assert out["status"] == "unavailable" and elapsed < pipeline.TIMEOUT_S, (out, elapsed)


def test_real_qdrant_a3_missing_collection_is_unavailable():
    from backend.core.qdrant_db import QdrantClient

    async def go():
        qc = QdrantClient(qdrant_url=QDRANT_URL, collection_name="showroom_does_not_exist")
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=_embeddings())
        await qc.close()
        return out

    assert asyncio.run(go())["status"] == "unavailable"
