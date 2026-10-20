"""Calibrate SHOWROOM_MIN_SCORE on a REAL local Qdrant (G4).

Indexes the synthetic corpus, prints the top raw cosine score for every in-corpus and
out-of-corpus question, and proposes the midpoint of the gap. Exits 1 if the two sets
overlap (no threshold can separate them). Writes .showroom-data/calibration-<sha>-<mode>.json.
Run: SHOWROOM_INTEGRATION=1 SHOWROOM_EMBEDDINGS=openai python scripts/calibrate.py
Only the ``openai`` mode may set the real threshold; ``lexical`` only checks the wiring.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SHOWROOM_INTEGRATION", "1")

from tests.integration.test_real_qdrant import MODE, _fresh_index  # noqa: E402
from tests.test_acceptance import IN_CORPUS, OUT_OF_CORPUS  # noqa: E402


async def top_scores(questions, qc, emb):
    rows = []
    for q in questions:
        res = await qc.search(await emb.generate_query_embedding(q), limit=1)
        meta = res["metadatas"][0] if res.get("metadatas") else {}
        rows.append({"q": q, "score": res["scores"][0] if res.get("scores") else 0.0,
                     "document_id": meta.get("document_id"), "pasal": meta.get("pasal_number")})
    return rows


async def main() -> int:
    qc, emb = await _fresh_index()
    ins, outs = await top_scores(IN_CORPUS, qc, emb), await top_scores(OUT_OF_CORPUS, qc, emb)
    await qc.close()
    lo_in, hi_out = min(r["score"] for r in ins), max(r["score"] for r in outs)
    for label, rows in (("DI KORPUS", ins), ("LUAR KORPUS", outs)):
        for r in rows:
            print(f"{label:12} {r['score']:.3f} -> {r['document_id']} P{r['pasal']} | {r['q']}")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    proposal = round((lo_in + hi_out) / 2, 3) if lo_in > hi_out else None
    out = {"commit": sha, "mode": MODE, "min_in_corpus": lo_in, "max_out_of_corpus": hi_out,
           "gap": round(lo_in - hi_out, 3), "proposed_min_score": proposal, "in": ins, "out": outs}
    dest = ROOT / ".showroom-data" / f"calibration-{sha[:10]}-{MODE}.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"mode={MODE} min_in={lo_in:.3f} max_out={hi_out:.3f} gap={lo_in - hi_out:.3f} "
          f"usulan SHOWROOM_MIN_SCORE={proposal} -> {dest.relative_to(ROOT)}")
    return 0 if proposal is not None else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
