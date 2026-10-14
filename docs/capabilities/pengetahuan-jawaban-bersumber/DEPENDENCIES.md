# DEPENDENCIES — pengetahuan → jawaban bersumber

**Unit:** `pengetahuan-jawaban-bersumber` · **Gerbang:** G2 · **Status:** SAH — disahkan Subhi 14 Okt 2026 (§5 terisi)
**Kontrak:** `CONTRACT.md` (SAH 14 Okt, main 856ebbc) · jalur minimum indexer → search → citation (§8.1)
**Diukur:** Teman2 `origin/main` ad3278690d, 14 Okt 2026 — Dockerfile + settings dari paste Subhi (`OK: G2 jalur minimum terukur @ ad3278690d`); import + penutupan transitif dari sparse clone cloud di commit yang sama (bukan checkout Subhi). Metode penutupan: ikuti setiap `from|import backend…` secara rekursif, termasuk import di dalam fungsi.

## 1. Ukuran penutupan import (berkas / baris)

| Titik masuk | Penutupan penuh | Tanpa `backend.app.metrics` |
|---|---|---|
| `core/legal/hierarchical_indexer.py` | 70 / 23.934 | **19 / 7.421** |
| `services/search/search_service.py` | 65 / 21.929 | **64 / 20.256** |
| `core/qdrant_db.py` | 65 / 21.929 | **5 / 3.774** |
| `core/embeddings.py` | 10 / 2.801 | 10 / 2.801 |
| `services/search/citation_service.py` | 1 / 401 | 1 / 401 |

`backend.app.metrics` sendiri menarik 65 berkas, tetapi selalu diimpor di dalam `try` (qdrant_db.py:563, :584; search_service.py:45) → opsional. Di showroom: **sengaja di luar**, import gagal ditelan oleh `try` yang sudah ada.

## 2. Dibawa (19 berkas, 7.421 baris — penutupan indexer tanpa metrics)

| Berkas | Baris | Peran |
|---|---|---|
| `core/legal/hierarchical_indexer.py` | 590 | pengindeksan BAB → Pasal |
| `core/legal/structure_parser.py` | 398 | parser struktur |
| `core/legal/chunker.py` | 410 | chunk per Pasal |
| `core/legal/quality_validators.py` | 247 | mutu dokumen |
| `core/legal/constants.py` | 360 | pola regex legal |
| `core/embeddings.py` | 615 | `EmbeddingsGenerator`, 1536 FROZEN |
| `core/bm25_vectorizer.py` | 368 | vektor sparse |
| `core/qdrant_db.py` | 1.554 | klien vector store |
| `core/collection_registry.py` | 102 | registri koleksi — `showroom_legal_synthetic` didaftarkan di sini |
| `core/exceptions.py` | 591 | tipe error |
| `core/pg_json_codec.py` | 81 | codec asyncpg |
| `app/core/config.py` | 1.392 | settings (baca env) |
| `app/core/database.py` | 51 | pool DB |
| `app/utils/tracing.py` | 135 | tracing |
| `app/__init__.py` | 3 | paket |
| `services/observability/__init__.py` | 25 | paket |
| `services/observability/llm_cost_recorder.py` | 364 | dicatat embeddings |
| `services/observability/tracking_decorator.py` | 123 | dekorator |
| `services/llm_clients/__init__.py` | 12 | paket |

Ditambah `services/search/citation_service.py` (401, nol import internal) → **20 berkas, 7.822 baris**.

Settings yang dibaca 3 modul inti (paste Subhi): `bm*` 6×, `qdrant_url` 3×, `enable_bm*` 2×, `database_url` 2×, `reranker_backend` 1×, `enable_reranker` 1×. Showroom menyediakan `.env.example` tanpa nilai.

## 3. Sengaja di luar

| Komponen | Alasan |
|---|---|
| `backend.app.metrics` (65 berkas) | opsional lewat `try`; observabilitas produksi, bukan perilaku |
| Orkestrator + `LLMGateway` | kontrak §8.1 |
| Dependensi Dockerfile `packages/cell-core` (:36), `packages/research-os-core` (:41), `apps/crm-cell/crm_cell` (:230) | penutupan 20 berkas unit ini: **0 baris** menyebut `cell_core`/`research_os_core`/`crm_cell` (cloud, ad3278690d; kontrol positif: `cell_core` ada di 16 berkas backend). Angka 0 di paste Subhi tidak dipakai — itu run dengan `B` kosong. Dependensi produk untuk unit lain, bukan unit ini |
| Data KBLI di image (Dockerfile :244–247) | HARD STOP KBLI; unit memakai korpus sintetis |
| Node 22 + `install-claude-code.sh` (Dockerfile :158–159, :205) | alat agen (harness), bukan produk |
| `IngestionService.ingest_book` (E34) | menunggu PR 8070 merged |

## 4. Pernah belum terpecahkan — kini diputuskan (§5)

**U1 · SearchService terlalu berat untuk jalur minimum.** Penutupannya 64 berkas / 20.256 baris walau tanpa metrics: `services/routing` (9), `services/misc` (5), `app/deps` (5), `services/rag` (4), `services/ingestion` (3), plus `autonomous_agents`, `memory`, `security`, `caching`, `redis_manager` — dan **`services/kbli_pma_disclosure.py`** (wilayah HARD STOP KBLI). Itu routing, ekspansi kueri, reranker, resolusi konflik: fitur produk di luar kontrak §3.

**U2 · Parent document tanpa DB.** `hierarchical_indexer.py:77-93`: tanpa `DATABASE_URL`, parent doc (BAB utuh) tidak disimpan, hanya warning. Jalur minimum tidak butuh retrieval BAB → usul: `DATABASE_URL` tidak diset di showroom, warning didokumentasikan, A1 menilai kutipan Pasal saja.

**U3 · Ambang abstain A2.** `AbstainPolicy` per domain berada di `services/rag/agentic` (di luar jalur minimum). Usul: satu ambang skor tetap di adaptor search, nilai awal = `EvidenceScoreConstants.ABSTAIN_THRESHOLD` dari Teman2 (nilainya diukur saat G3), dicatat di PROVENANCE.

## 5. Keputusan pengesahan (Subhi, 14 Okt 2026)

1. U1 → **adaptor search tipis**: embed kueri → `qdrant_db` cari di `showroom_legal_synthetic` → `CitationService` membentuk `sources[]`; error vector store/embedding → `status=unavailable` + `error` (meniru search_service.py:756-775), ≤ 10 s. SearchService **sengaja di luar** (routing, reranker, memory, modul KBLI). Adaptor = kode baru showroom, dicatat di PROVENANCE sebagai "disimulasikan/ditulis ulang", bukan "dibawa".
2. U2 → **parent doc dimatikan**: `DATABASE_URL` tidak diset; warning indexer didokumentasikan; A1 menilai kutipan Pasal.
3. U3 → **satu ambang tetap** = `EvidenceScoreConstants.ABSTAIN_THRESHOLD` Teman2, nilainya diukur dan dicatat di PROVENANCE saat G3.

Baris "belum terpecahkan" yang mempengaruhi perilaku: **0**. G2 selesai.
