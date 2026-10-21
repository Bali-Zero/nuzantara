# PROVENANCE — pengetahuan → jawaban bersumber

**Gerbang:** G3 (salin apa adanya; perilaku belum diubah) → G4 persiapan · **Ditulis:** AI assistant, disahkan maintainer, 14 Okt 2026
**Sumber:** snapshot platform internal 14 Okt 2026, prefiks `apps/backend-rag/` — commit sumber persis dicatat di catatan asal internal `SR-U1-2026-10-14` (tidak dipublikasikan, aturan publikasi README)
**Bukti salinan:** setiap berkas "dibawa" diverifikasi `shasum -a 256 -c` terhadap `docs/capabilities/pengetahuan-jawaban-bersumber/verbatim.sha256` (hash dihitung dari isi berkas di snapshot sumber). Kode dibawa apa adanya tetap memuat pengenal upstream-nya (termasuk nama koleksi); lihat carve-out di README.

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
| `backend/app/core/config.py` (41 baris) | Asli 1.392 baris memuat email staf + nomor telepon (prinsip nol data pribadi). Shim membaca 9 atribut yang dipakai berkas dibawa; nama env + default sama dengan upstream, kecuali `qdrant_timeout` = 10 s (upstream tidak punya atribut ini → qdrant_db memakai 30 s; kontrak §8.2) |
| `backend/app/core/__init__.py`, `backend/app/utils/__init__.py`, `backend/core/legal/__init__.py`, `backend/services/__init__.py`, `backend/services/search/__init__.py`, `backend/services/llm_clients/__init__.py` (kosong) | Di upstream berkas ini meng-import ulang modul lain (contoh: `llm_clients/__init__.py` → klien LLM lain); `backend/services/__init__.py` saja menarik ±300 berkas saat dieksekusi Python. Diukur: berkas dibawa hanya menarget tiga paket — `backend.services.observability` (meng-import nama dari `__init__` → `__init__` itu dibawa apa adanya), `backend.services.llm_clients` dan `backend.app` (keduanya hanya untuk submodul `pricing` / `metrics`, jalan dengan `__init__` kosong) |

## 3. Sengaja di luar (lihat DEPENDENCIES §3)

`backend.app.metrics` (selalu di dalam `try` di `qdrant_db.py` dan `llm_cost_recorder.py`) · SearchService + orkestrator · data KBLI · paket tambahan image produksi (`cell-core` / `research-os-core` / `crm_cell`).

## 4. Koreksi terhadap DEPENDENCIES (G2) — ditemukan saat G3

1. **`backend/services/llm_clients/pricing.py` (467 baris, stdlib saja) wajib dibawa.** `tracking_decorator.py` meng-import-nya tanpa `try` setiap kali fungsi berdekorator `@llm_cost_tracked` dipanggil — termasuk dari `embeddings.py`. Alat penutupan G2 tidak melihatnya karena bentuk `from paket import submodul`.
2. `config.py` pindah dari "dibawa" ke "ditulis ulang" (§2).
3. Efek samping baru dicatat: `llm_cost_recorder` menulis JSONL ke `LLM_COST_JSONL_ROOT` (default upstream `/data`). Showroom: `./.showroom-data`, di-`.gitignore`.
4. Konstanta ambang abstain (U3): `EvidenceScoreConstants.ABSTAIN_THRESHOLD = 0.15` di `app/core/constants.py` upstream — dipakai adaptor di G3 langkah 2 (lihat koreksi di §7).

## 5. Belum dibuktikan pada langkah salin

Hanya `python3 -m py_compile` (sintaks) yang dijalankan di langkah ini. Import nyata butuh paket pihak ketiga — itu G3 langkah 2 / G4. Di lingkungan CI cloud: `py_compile` lulus di Python 3.8 dan 3.13 (28 berkas). Beberapa berkas memakai anotasi `X | None` saat runtime → butuh Python ≥ 3.10 untuk import nyata. Mock ≠ integrasi ≠ observasi langsung.

## 6. G3 langkah 2a — import nyata (14 Okt 2026)

- `requirements.txt`: 4 paket, versi = lockfile upstream (asyncpg 0.31.0, httpx 0.28.1, openai 2.53.0, tiktoken 0.14.0). `opentelemetry` (`tracing.py`) dan `sentence_transformers` (`embeddings.py`) dijaga `try`/lazy → sengaja tidak dipasang. `qdrant-client` tidak diperlukan: `core/qdrant_db.py` memakai httpx.
- `scripts/smoke_import.py`: import 19 modul dibawa + gagal bila ada modul `backend.*` lain ikut termuat.
- **Efek samping saat import (temuan):** `embeddings.py` memanggil `tiktoken.get_encoding("cl100k_base")` di level modul → unduh ±1,7 MB dari CDN tiktoken saat pertama kali. Kegagalan jaringan **bukan** `ImportError` → tidak tertangkap oleh `except ImportError` di sebelahnya → `embeddings`, `legal.chunker`, `legal.hierarchical_indexer` gagal di-import tanpa jaringan (diukur: 16/19). Showroom: `TIKTOKEN_CACHE_DIR=./.showroom-data/tiktoken` → unduh sekali, berikutnya offline. Perilaku upstream tidak diubah; dicatat untuk G4 (clone bersih butuh jaringan satu kali) dan sebagai kandidat perbaikan upstream (pending review).
- Cloud, Python 3.14, tanpa tiktoken (jalur `except ImportError`): 19/19 OK, 0 modul bocor. Kontrol dengan tiktoken + jaringan: mesin maintainer.
- **Koreksi 14 Okt (sebelum review):** smoke versi pertama hanya meng-import; ia tidak melihat bahwa `core/qdrant_db.py` membangun `httpx.AsyncClient(http2=True)` secara malas → tanpa paket `h2`, **setiap** panggilan Qdrant gagal `ImportError`. Diukur: `ImportError: Using http2=True, but the 'h2' package is not installed`. Ditambah `h2==4.4.1`, `hpack==4.2.0`, `hyperframe==6.1.0` (pin lockfile upstream), dan smoke kini juga membangun klien Qdrant + OpenAI (tanpa request jaringan). Import malas pihak ketiga lain di berkas dibawa: hanya `opentelemetry` (dijaga) dan `sentence_transformers` (hanya provider non-openai).

## 7. G3 langkah 2b — adaptor tipis + korpus sintetis + uji A1–A3 (14 Okt 2026)

**Kode baru showroom (bukan dibawa):** `showroom/pipeline.py` (`ingest`, `answer`), `tests/` (fakes + uji penerimaan), `corpus/` (3 Peraturan Desa **fiktif**, 10 Pasal), `requirements-dev.txt` (pytest 9.1.1).

**Temuan pada kode dibawa yang membentuk adaptor:**
1. `QdrantClient.search` menelan **semua** error setelah 3× retry dan mengembalikan hasil kosong (tanpa kunci `scores`); error 4xx (mis. koleksi tidak ada) juga dibalas kosong. Tanpa penjaga, "vector store mati" terlihat seperti "tidak ada bukti". Adaptor: probe `get_stats()` dulu, lalu dict tanpa `scores` = `unavailable`.
2. Connect timeout 10 s per percobaan × retry → bisa melewati batas kontrak. Adaptor membatasi seluruh panggilan dengan `asyncio.wait_for(10 s)`.
3. `CitationService.extract_sources_from_rag` hanya menghasilkan judul/url/skor; adaptor menambah `document_id`, `pasal`, `quote` (kontrak §3).

**Koreksi keputusan U3 (DEPENDENCIES §5.3) — kesalahan analisis awal:** ambang 0.15 upstream berlaku untuk *evidence_score gabungan* (kualitas sumber 0–0.4 + relevansi 0–0.6, di modul reasoning upstream), bukan cosine mentah. Diukur di mock: 0.15 pada cosine mentah meloloskan 2 dari 4 pertanyaan di luar korpus. Keputusan maintainer 14 Okt: ambang cosine terpisah `SHOWROOM_MIN_SCORE`, sementara **0.35** (tengah celah mock: di korpus ≥ 0.527, di luar ≤ 0.200), **wajib dikalibrasi ulang dengan embedding OpenAI nyata di G4** sebelum A2 dianggap lulus.

**Tingkat bukti: MOCK, bukan integrasi.** Qdrant palsu di dalam proses (`httpx.MockTransport`; kode `QdrantClient` asli tetap jalan sampai lapisan HTTP) + embedding leksikal deterministik. Uji A3 "tidak terjangkau" memakai koneksi TCP nyata ke port tertutup.

**Hasil (cloud, Python 3.14):** 11/11 uji lulus. Mutasi: menghapus probe `get_stats` → 1 uji merah; menghapus cek `scores` → 1 uji merah. Peringatan `DATABASE_URL not configured` dari indexer = perilaku yang diputuskan (DEPENDENCIES §5.2).

## 8. Persiapan G4 — README setup, Qdrant lokal, uji integrasi, kalibrasi, receipt (14 Okt 2026)

- **Diukur di mesin pengembangan maintainer:** CPU Intel tanpa AVX2, macOS 12, tanpa Docker. Binary resmi Qdrant v1.19.2 `x86_64-apple-darwin` jalan: koleksi 1536-dim, 200 titik, search teratas benar, log 0 error.
- **Kode baru:** `scripts/qdrant_local.sh` (start/stop/status, 127.0.0.1, data di `.showroom-data/`, memastikan path storage benar-benar dipakai), `tests/integration/test_real_qdrant.py` (dilewati kecuali `SHOWROOM_INTEGRATION=1`; menolak menghapus koleksi di host selain localhost), `scripts/calibrate.py`, `scripts/receipt.py` (receipt terikat commit; tidak sah bila tree kotor atau ada uji gagal), README dengan blok setup bertanda.
- **Cloud, Qdrant 1.19.2 nyata + embedding leksikal:** 14/14 lulus; tanpa flag 11 lulus + 3 dilewati; Qdrant dimatikan → uji A1/A2 integrasi merah (kontrol negatif). Kalibrasi leksikal: di korpus ≥ 0.527, luar ≤ 0.200, celah 0.327 — **bukan** kalibrasi akhir.
- **G4 dari clone bersih (16 Okt 2026, mesin maintainer):** setup = blok README apa adanya; smoke 19/19 + klien malas 2/2; receipt `mock-only` VALID (11 lulus / 3 dilewati) dan receipt `lexical` VALID (14/14, Qdrant 1.19.2).
- **Belum:** mode `openai` menunggu API key khusus showroom (rahasia; dipasang oleh owner di `.env` lokal, tidak pernah di repo). A1/A2 kontrak baru tertutup oleh receipt `embeddings_mode=openai`.
