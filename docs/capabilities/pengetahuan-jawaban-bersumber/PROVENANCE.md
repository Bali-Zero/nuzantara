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

## 6. G3 langkah 2a — import nyata (14 Okt 2026)

- `requirements.txt`: 4 paket, versi = `requirements.lock.txt` Teman2 @ ad3278690d (asyncpg 0.31.0, httpx 0.28.1, openai 2.53.0, tiktoken 0.14.0). `opentelemetry` (tracing.py:15) dan `sentence_transformers` (embeddings.py:296) dijaga `try`/lazy → sengaja tidak dipasang. `qdrant-client` tidak diperlukan: `core/qdrant_db.py` memakai httpx.
- `scripts/smoke_import.py`: import 19 modul dibawa + gagal bila ada modul `backend.*` lain ikut termuat.
- **Efek samping saat import (temuan):** `embeddings.py:42` memanggil `tiktoken.get_encoding("cl100k_base")` di level modul → unduh ±1,7 MB dari `openaipublic.blob.core.windows.net` saat pertama kali. Kegagalan jaringan **bukan** `ImportError` → tidak tertangkap oleh `except ImportError` di `:43` → `embeddings`, `legal.chunker`, `legal.hierarchical_indexer` gagal di-import tanpa jaringan (diukur di cloud: 16/19). Showroom: `TIKTOKEN_CACHE_DIR=./.showroom-data/tiktoken` → unduh sekali, berikutnya offline. Perilaku Teman2 tidak diubah; dicatat untuk G4 (clone bersih butuh jaringan satu kali) dan sebagai kandidat perbaikan di Teman2.
- Cloud, Python 3.14.6, tanpa tiktoken (jalur `except ImportError`): 19/19 OK, 0 modul bocor. Kontrol dengan tiktoken + jaringan: Mac Subhi (proxy cloud menolak host tiktoken, 403).
- **Koreksi 14 Okt (sebelum review):** smoke versi pertama hanya meng-import; ia tidak melihat `core/qdrant_db.py:334` yang membangun `httpx.AsyncClient(http2=True)` secara malas → tanpa paket `h2`, **setiap** panggilan Qdrant gagal `ImportError`. Diukur di cloud: `ImportError: Using http2=True, but the 'h2' package is not installed`. Ditambah `h2==4.4.1`, `hpack==4.2.0`, `hyperframe==6.1.0` (pin lock Teman2), dan smoke kini juga membangun klien Qdrant + OpenAI (tanpa request jaringan). Import malas pihak ketiga lain di berkas dibawa: hanya `opentelemetry` (dijaga) dan `sentence_transformers` (hanya provider non-openai).

## 7. G3 langkah 2b — adaptor tipis + korpus sintetis + uji A1–A3 (14 Okt 2026)

**Kode baru showroom (bukan dibawa):** `showroom/pipeline.py` (`ingest`, `answer`), `tests/` (fakes + uji penerimaan), `corpus/` (3 Peraturan Desa **fiktif**, 10 Pasal), `requirements-dev.txt` (pytest 9.1.1).

**Temuan pada kode dibawa (Teman2 ad3278690d) yang membentuk adaptor:**
1. `QdrantClient.search` menelan **semua** error setelah 3× retry dan mengembalikan hasil kosong (tanpa kunci `scores`); error 4xx (mis. koleksi tidak ada) juga dibalas kosong. Tanpa penjaga, "vector store mati" terlihat seperti "tidak ada bukti". Adaptor: probe `get_stats()` dulu, lalu dict tanpa `scores` = `unavailable`.
2. Connect timeout 10 s per percobaan × retry → bisa melewati batas kontrak. Adaptor membatasi seluruh panggilan dengan `asyncio.wait_for(10 s)`.
3. `CitationService.extract_sources_from_rag` hanya menghasilkan judul/url/skor; adaptor menambah `document_id`, `pasal`, `quote` (kontrak §3).

**Koreksi keputusan U3 (DEPENDENCIES §5.3) — kesalahan Atlas:** ambang 0.15 Teman2 berlaku untuk *evidence_score gabungan* (`reasoning_utils.py:341`: kualitas sumber 0–0.4 + relevansi 0–0.6), bukan cosine mentah. Diukur di mock: 0.15 pada cosine mentah meloloskan 2 dari 4 pertanyaan di luar korpus. Keputusan Subhi 14 Okt: ambang cosine terpisah `SHOWROOM_MIN_SCORE`, sementara **0.35** (tengah celah mock: di korpus ≥ 0.527, di luar ≤ 0.200), **wajib dikalibrasi ulang dengan embedding OpenAI nyata di G4** sebelum A2 dianggap lulus.

**Tingkat bukti: MOCK, bukan integrasi.** Qdrant palsu di dalam proses (`httpx.MockTransport`; kode `QdrantClient` asli tetap jalan sampai lapisan HTTP) + embedding leksikal deterministik. Uji A3 "tidak terjangkau" memakai koneksi TCP nyata ke port tertutup.

**Hasil (cloud, Python 3.14.6):** 11/11 uji lulus. Mutasi: menghapus probe `get_stats` → 1 uji merah; menghapus cek `scores` → 1 uji merah. Peringatan `DATABASE_URL not configured` dari indexer = perilaku yang diputuskan (DEPENDENCIES §5.2).

## 8. Persiapan G4 — README setup, Qdrant lokal, uji integrasi, kalibrasi, receipt (14 Okt 2026)

- **Diukur di MacBook operator:** i5-3210M (Ivy Bridge, AVX tanpa AVX2), macOS 12.7.6, tanpa Docker. Binary resmi Qdrant v1.19.2 `x86_64-apple-darwin` jalan: koleksi 1536-dim, 200 titik, search teratas benar, log 0 error.
- **Kode baru:** `scripts/qdrant_local.sh` (start/stop/status, 127.0.0.1, data di `.showroom-data/`, memastikan path storage benar-benar dipakai), `tests/integration/test_real_qdrant.py` (dilewati kecuali `SHOWROOM_INTEGRATION=1`; menolak menghapus koleksi di host selain localhost), `scripts/calibrate.py`, `scripts/receipt.py` (receipt terikat commit; tidak sah bila tree kotor atau ada uji gagal), README dengan blok setup bertanda.
- **Cloud, Qdrant 1.19.2 nyata + embedding leksikal:** 14/14 lulus; tanpa flag 11 lulus + 3 dilewati; Qdrant dimatikan → uji A1/A2 integrasi merah (kontrol negatif). Kalibrasi leksikal: di korpus ≥ 0.527, luar ≤ 0.200, celah 0.327 — **bukan** kalibrasi akhir.
- **Belum:** mode `openai` menunggu API key khusus showroom dari Antonello (rahasia = wewenang Antonello). A1/A2 kontrak baru tertutup oleh receipt `embeddings_mode=openai`.
