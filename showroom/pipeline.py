"""Thin pipeline for unit 1: synthetic legal text -> index -> search -> sourced answer.

NEW showroom code (DEPENDENCIES §5.1). It composes carried Teman2 modules and adds
only what CONTRACT.md requires on top of them:

* ``ingest``  — reject input without Pasal structure (CONTRACT §8.3), then index with
  the carried ``HierarchicalIndexer`` (dense only, no chunker, no DB: DEPENDENCIES §5.2).
* ``answer``  — return ``{answer, sources, status[, error]}``.

Why the guards exist (measured on the carried code, Teman2 ad3278690d):
* ``QdrantClient.search`` swallows every error after 3 retries and returns an empty
  result (qdrant_db.py search -> except Exception -> empty dict without ``scores``), and
  returns an empty result on 4xx such as a missing collection. Without a probe, "vector
  store down" would look like "no evidence". So ``answer`` first calls ``get_stats()``
  (which carries an ``error`` key) and treats a result without ``scores`` as unavailable.
* Retries use a 10 s connect timeout each, so the whole call is bounded by
  ``asyncio.wait_for`` (CONTRACT §8.2).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from backend.core.legal.hierarchical_indexer import HierarchicalIndexer
from backend.core.legal.structure_parser import LegalStructureParser
from backend.services.search.citation_service import CitationService

COLLECTION = "showroom_legal_synthetic"  # CONTRACT §8.4
# Minimum RAW cosine similarity for a hit to count as evidence (decision 14 Oct 2026, replaces
# DEPENDENCIES §5.3). Teman2's 0.15 (constants.py:96) gates a COMPOSITE evidence_score
# (reasoning_utils.py:341: source quality 0-0.4 + relevance 0-0.6), not raw cosine, so it is
# not reused here. 0.35 is provisional (midpoint of the mock gap 0.200-0.527) and MUST be
# recalibrated with real OpenAI embeddings in G4 before A2 counts as passed.
DEFAULT_MIN_SCORE = 0.35


def min_score() -> float:
    return float(os.environ.get("SHOWROOM_MIN_SCORE") or DEFAULT_MIN_SCORE)

TIMEOUT_S = 10.0  # CONTRACT §8.2
ABSTAIN_ANSWER = "Tidak ada sumber di korpus yang mendukung jawaban untuk pertanyaan ini."
MAX_QUESTION_CHARS = 500  # CONTRACT §2 I2


class InputRejected(ValueError):
    """Input does not satisfy CONTRACT §2 / §8.3 (readable reason in the message)."""


def has_pasal_structure(text: str) -> bool:
    structure = LegalStructureParser().parse(text)
    in_bab = sum(len(b.get("pasal", [])) for b in structure.get("batang_tubuh") or [])
    return bool(in_bab or structure.get("pasal_list"))


async def ingest(document_text: str, document_id: str, *, qdrant: Any, embeddings: Any) -> dict:
    """Index one synthetic document. Raises InputRejected when it has no Pasal."""
    if not has_pasal_structure(document_text):
        raise InputRejected(f"{document_id}: dokumen tidak punya struktur Pasal; ditolak (CONTRACT §8.3)")
    indexer = HierarchicalIndexer(
        structure_parser=LegalStructureParser(),
        qdrant_client=qdrant,
        embeddings=embeddings,
        chunker=None,
        sparse_vectorizer=None,
    )
    title = next((line.strip() for line in document_text.splitlines() if line.strip()), document_id)
    return await indexer.index_legal_document(
        document_text=document_text,
        document_id=document_id,
        metadata={"title": title, "category": "synthetic"},
    )


def _unavailable(reason: str) -> dict:
    return {"answer": None, "sources": [], "status": "unavailable", "error": reason}


async def _answer(question: str, qdrant: Any, embeddings: Any, limit: int) -> dict:
    stats = await qdrant.get_stats()
    if "error" in stats:
        return _unavailable(f"vector store tidak tersedia ({stats['error'][:120]})")
    if not stats.get("total_documents"):
        return _unavailable(f"koleksi {qdrant.collection_name} kosong atau belum diindeks")
    try:
        vector = await embeddings.generate_query_embedding(question)
    except Exception as exc:  # noqa: BLE001 — provider errors must not leak keys or hang
        return _unavailable(f"embedding gagal ({type(exc).__name__})")
    result = await qdrant.search(vector, limit=limit)
    threshold = min_score()
    if "scores" not in result:
        return _unavailable("pencarian vector store gagal setelah retry")
    hits = [
        {"text": text, "metadata": meta, "score": score}
        for text, meta, score in zip(result["documents"], result["metadatas"], result["scores"])
        if score >= threshold
    ]
    if not hits:
        return {"answer": ABSTAIN_ANSWER, "sources": [], "status": "unsupported"}
    sources = CitationService().extract_sources_from_rag(hits)
    for source, hit in zip(sources, hits):
        meta = hit["metadata"]
        source["document_id"] = meta.get("document_id")
        source["pasal"] = meta.get("pasal_number") or meta.get("chunk_key")
        source["quote"] = hit["text"]
    top = sources[0]
    answer = f"Menurut {top['title']}, Pasal {top['pasal']}: {top['quote']}"
    return {"answer": answer, "sources": sources, "status": "supported"}


async def answer(question: str, *, qdrant: Any, embeddings: Any, limit: int = 3) -> dict:
    """CONTRACT §3 response. Never raises for service failures; bounded by TIMEOUT_S."""
    if not question.strip() or len(question) > MAX_QUESTION_CHARS:
        raise InputRejected(f"pertanyaan kosong atau lebih dari {MAX_QUESTION_CHARS} karakter")
    try:
        return await asyncio.wait_for(_answer(question, qdrant, embeddings, limit), TIMEOUT_S)
    except TimeoutError:
        return _unavailable(f"melewati batas waktu {TIMEOUT_S:.0f} s")
