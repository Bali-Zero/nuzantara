"""CONTRACT §6 acceptance A1–A3 + §8.3 rejection, at MOCK level (see tests/fakes.py)."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from backend.core.qdrant_db import QdrantClient
from showroom import pipeline
from tests.fakes import BrokenEmbeddings, FakeQdrantServer, LexicalEmbeddings

ROOT = Path(__file__).resolve().parent.parent
CORPUS = sorted((ROOT / "corpus").glob("*.txt"))


def run(coro):
    return asyncio.run(coro)


async def _indexed(fail_search: bool = False) -> tuple[QdrantClient, FakeQdrantServer]:
    server = FakeQdrantServer(fail_search=fail_search)
    qc = QdrantClient(qdrant_url="http://fake-qdrant:6333", collection_name=pipeline.COLLECTION)
    server.attach(qc)
    await qc.create_collection(vector_size=1536)
    for path in CORPUS:
        res = await pipeline.ingest(path.read_text(), path.stem, qdrant=qc, embeddings=LexicalEmbeddings())
        assert res["chunks_upserted"] == res["chunks_indexed"] > 0, res
    return qc, server


def test_corpus_has_three_synthetic_documents():
    assert len(CORPUS) == 3
    for path in CORPUS:
        assert "DOKUMEN FIKTIF" in path.read_text()


def test_a1_supported_answer_cites_correct_document_and_pasal():
    async def go():
        qc, _ = await _indexed()
        out = await pipeline.answer("Berapa iuran air bersih per bulan untuk rumah tangga?",
                                    qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out
    out = run(go())
    assert out["status"] == "supported", out
    top = out["sources"][0]
    assert top["document_id"] == "perdes-sintetis-01-air-bersih"
    assert str(top["pasal"]) == "2"
    source_text = (ROOT / "corpus" / f"{top['document_id']}.txt").read_text()
    assert top["quote"].strip() and top["quote"].strip()[:60] in source_text
    assert "tujuh ribu rupiah" in out["answer"]


def test_a2_unsupported_question_abstains_without_sources():
    async def go():
        qc, _ = await _indexed()
        out = await pipeline.answer("Siapa juara piala dunia sepak bola tahun lalu?",
                                    qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out
    out = run(go())
    assert out == {"answer": pipeline.ABSTAIN_ANSWER, "sources": [], "status": "unsupported"}


def test_a3_vector_store_unreachable_is_unavailable_within_timeout():
    async def go():
        qc = QdrantClient(qdrant_url="http://127.0.0.1:9", collection_name=pipeline.COLLECTION)
        t0 = time.monotonic()
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out, time.monotonic() - t0
    out, elapsed = run(go())
    assert out["status"] == "unavailable" and out["error"], out
    assert out["sources"] == [] and out["answer"] is None
    assert elapsed < pipeline.TIMEOUT_S, elapsed


def test_a3_missing_collection_is_unavailable_not_unsupported():
    async def go():
        server = FakeQdrantServer()
        qc = QdrantClient(qdrant_url="http://fake-qdrant:6333", collection_name=pipeline.COLLECTION)
        server.attach(qc)
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out
    out = run(go())
    assert out["status"] == "unavailable", out


def test_a3_embedding_failure_is_unavailable_and_leaks_no_key():
    async def go():
        qc, _ = await _indexed()
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=BrokenEmbeddings())
        await qc.close()
        return out
    out = run(go())
    assert out["status"] == "unavailable"
    assert "sk-" not in str(out)


def test_a3_hanging_service_is_cut_at_timeout(monkeypatch):
    monkeypatch.setattr(pipeline, "TIMEOUT_S", 0.5)

    class Hanging(LexicalEmbeddings):
        async def generate_query_embedding(self, query):
            await asyncio.sleep(5)

    async def go():
        qc, _ = await _indexed()
        t0 = time.monotonic()
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=Hanging())
        await qc.close()
        return out, time.monotonic() - t0
    out, elapsed = run(go())
    assert out["status"] == "unavailable" and "batas waktu" in out["error"]
    assert elapsed < 2


def test_document_without_pasal_is_rejected_with_reason():
    text = (ROOT / "tests" / "data" / "tanpa-pasal.txt").read_text()
    with pytest.raises(pipeline.InputRejected, match="struktur Pasal"):
        run(pipeline.ingest(text, "tanpa-pasal", qdrant=None, embeddings=None))


IN_CORPUS = [
    "Berapa iuran air bersih per bulan untuk rumah tangga?",
    "Kapan pasar desa dibuka?",
    "Siapa yang wajib ikut ronda malam?",
    "Berapa lapak yang boleh ditempati satu pedagang?",
]
OUT_OF_CORPUS = [
    "Siapa juara piala dunia sepak bola tahun lalu?",
    "Bagaimana cara membuat visa kerja?",
    "Berapa harga beras di pasar kota?",
    "Apa syarat menikah di kantor urusan agama?",
]


def test_threshold_separates_in_and_out_of_corpus_mock_calibration():
    """MOCK calibration of SHOWROOM_MIN_SCORE: every in-corpus question supported, every
    out-of-corpus question abstains. Must be re-run with real embeddings in G4."""
    async def go():
        qc, _ = await _indexed()
        e = LexicalEmbeddings()
        ins = [await pipeline.answer(q, qdrant=qc, embeddings=e) for q in IN_CORPUS]
        outs = [await pipeline.answer(q, qdrant=qc, embeddings=e) for q in OUT_OF_CORPUS]
        await qc.close()
        return ins, outs
    ins, outs = run(go())
    assert [o["status"] for o in ins] == ["supported"] * 4
    assert [o["status"] for o in outs] == ["unsupported"] * 4


def test_old_threshold_015_on_raw_cosine_lets_off_topic_through(monkeypatch):
    """Negative control for the 14 Oct finding: 0.15 on raw cosine fails A2."""
    monkeypatch.setenv("SHOWROOM_MIN_SCORE", "0.15")
    async def go():
        qc, _ = await _indexed()
        out = await pipeline.answer(OUT_OF_CORPUS[0], qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out
    assert run(go())["status"] == "supported"


def test_a3_search_failure_after_healthy_probe_is_unavailable_not_unsupported():
    """QdrantClient.search swallows a 500 after its retries and returns a dict without
    'scores'; the pipeline must report unavailable, not 'no evidence'."""
    async def go():
        qc, server = await _indexed(fail_search=True)
        out = await pipeline.answer("Berapa iuran air?", qdrant=qc, embeddings=LexicalEmbeddings())
        await qc.close()
        return out, server.search_calls
    out, calls = run(go())
    assert out["status"] == "unavailable", out
    assert calls >= 2  # the carried client really retried before giving up
