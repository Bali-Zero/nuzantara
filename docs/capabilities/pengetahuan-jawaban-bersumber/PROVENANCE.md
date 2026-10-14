# PROVENANCE — pengetahuan → jawaban bersumber

**Gerbang:** G3 langkah 1 (salin apa adanya; perilaku belum diubah) · **Ditulis:** Atlas (Claude), 14 Okt 2026
**Sumber:** Bali-Zero/Teman2 commit `ad3278690d` (origin/main 14 Okt 2026), prefiks `apps/backend-rag/`
**Bukti salinan:** setiap berkas "dibawa" diverifikasi `shasum -a 256 -c` terhadap `docs/capabilities/pengetahuan-jawaban-bersumber/verbatim.sha256` (hash dihitung dari `git show ad3278690d:<path>`).

## 1. Dibawa apa adanya (21 berkas, 6.889 baris)

| Berkas | Baris | Status |
|---|---|---|
| `backend/__init__.py` | 3 | dibawa apa adanya |
| `backend/app/__init__.py` | 3 | dibawa apa adanya |
| `backend/app/core/database.py` | 51 | dibawa apa adanya |
| `backend/app/utils/tracing.py` | 135 | dibawa apa adanya |
| `backend/core/__init__.py` | 1 | dibawa apa adanya |
| `backend/core/bm25_vectorizer.py` | 368 | dibawa apa adanya |
| `backend/core/collection_registry.py` | 102 | dibawa apa adanya |
| `backend/core/embeddings.py` | 615 | dibawa apa adanya |
| `backend/core/exceptions.py` | 591 | dibawa apa adanya |
| `backend/core/legal/chunker.py` | 410 | dibawa apa adanya |
| `backend/core/legal/constants.py` | 360 | dibawa apa adanya |
| `backend/core/legal/hierarchical_indexer.py` | 590 | dibawa apa adanya |
| `backend/core/legal/quality_validators.py` | 247 | dibawa apa adanya |
| `backend/core/legal/structure_parser.py` | 398 | dibawa apa adanya |
| `backend/core/pg_json_codec.py` | 81 | dibawa apa adanya |
| `backend/core/qdrant_db.py` | 1554 | dibawa apa adanya |
| `backend/services/llm_clients/pricing.py` | 467 | dibawa apa adanya |
| `backend/services/observability/__init__.py` | 25 | dibawa apa adanya |
| `backend/services/observability/llm_cost_recorder.py` | 364 | dibawa apa adanya |
| `backend/services/observability/tracking_decorator.py` | 123 | dibawa apa adanya |
| `backend/services/search/citation_service.py` | 401 | dibawa apa adanya |

## 2. Ditulis ulang di showroom (7 berkas)

| Berkas | Alasan |
|---|---|
| `backend/app/core/config.py` (41 baris) | Asli 1.392 baris memuat email staf + nomor telepon (prinsip §3.3). Shim membaca 9 atribut yang dipakai berkas dibawa; nama env + default sama dengan Teman2, kecuali `qdrant_timeout` = 10 s (Teman2 tidak punya atribut ini → qdrant_db memakai 30 s; kontrak §8.2) |
| `backend/app/core/__init__.py`, `backend/app/utils/__init__.py`, `backend/core/legal/__init__.py`, `backend/services/__init__.py`, `backend/services/search/__init__.py`, `backend/services/llm_clients/__init__.py` (kosong) | Di Teman2 berkas ini meng-import ulang modul lain (contoh: `llm_clients/__init__.py` → gemini_service + openrouter_client); `backend/services/__init__.py` saja menarik ±300 berkas saat dieksekusi Python. Diukur: berkas dibawa hanya menarget tiga paket — `backend.services.observability` (meng-import nama dari `__init__` → `__init__` itu dibawa apa adanya), `backend.services.llm_clients` dan `backend.app` (keduanya hanya untuk submodul `pricing` / `metrics`, jalan dengan `__init__` kosong) |

## 3. Sengaja di luar (lihat DEPENDENCIES §3)

`backend.app.metrics` (selalu di dalam `try`: qdrant_db.py:563, :584; llm_cost_recorder.py:250) · SearchService + orkestrator · data KBLI · dependensi Dockerfile cell-core / research-os-core / crm_cell.

## 4. Koreksi terhadap DEPENDENCIES (G2) — ditemukan saat G3

1. **`backend/services/llm_clients/pricing.py` (467 baris, stdlib saja) wajib dibawa.** `tracking_decorator.py:60` meng-import-nya tanpa `try` setiap kali fungsi berdekorator `@llm_cost_tracked` dipanggil — termasuk `embeddings.py:401`. Alat penutupan G2 tidak melihatnya karena bentuk `from paket import submodul`.
2. `config.py` pindah dari "dibawa" ke "ditulis ulang" (§2).
3. Efek samping baru dicatat: `llm_cost_recorder` menulis JSONL ke `LLM_COST_JSONL_ROOT` (default Teman2 `/data`). Showroom: `./.showroom-data`, di-`.gitignore`.
4. Konstanta ambang abstain (U3): `EvidenceScoreConstants.ABSTAIN_THRESHOLD = 0.15` di Teman2 `backend/app/core/constants.py:96` @ ad3278690d — dipakai adaptor di G3 langkah 2.

## 5. Belum dibuktikan

Hanya `python3 -m py_compile` (sintaks) yang dijalankan di langkah ini. Import nyata butuh paket pihak ketiga (qdrant-client, asyncpg, openai, …) — itu G3 langkah 2 / G4. Di cloud: `py_compile` lulus di Python 3.8.20 dan 3.13 (28 berkas). Catatan untuk G4: beberapa berkas memakai anotasi `X | None` saat runtime → kemungkinan butuh Python ≥ 3.10 untuk import nyata; ukur versi Python di Mac. Mock ≠ integrasi ≠ observasi langsung.
