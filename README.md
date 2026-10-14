# nuzantara-showroom

Repo showroom privat Bali Zero. Kemampuan dari Teman2 dipindahkan satu per satu.
Aturan: tanpa rahasia, kredensial, atau data klien. Hanya materi contoh sintetis.

## Kemampuan 1 — pengetahuan → jawaban bersumber

Kontrak, dependensi, dan asal-usul kode: `docs/capabilities/pengetahuan-jawaban-bersumber/`
(`CONTRACT.md`, `DEPENDENCIES.md`, `PROVENANCE.md`). Korpus: `corpus/` (3 Peraturan Desa **fiktif**).

### Prasyarat

- Python ≥ 3.10 (diukur: 3.14.6 di macOS 12.7.6 Intel), `git`, `curl`.
- Tanpa Docker: Qdrant resmi dijalankan sebagai binary lokal oleh `scripts/qdrant_local.sh`
  (127.0.0.1 saja, data di `.showroom-data/`).
- Jaringan saat setup pertama: PyPI, rilis Qdrant di GitHub, dan unduhan encoding tiktoken.
- `OPENAI_API_KEY` hanya untuk mode `openai` (kalibrasi dan penutupan A1/A2). Isi di `.env`, jangan di-commit.

### Setup dari clone bersih

Blok di antara penanda di bawah ini dijalankan apa adanya oleh pemeriksaan G4, jadi README adalah sumber setup.

<!-- setup:start -->
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -q -r requirements-dev.txt
[ -e .env ] || cp .env.example .env
export TIKTOKEN_CACHE_DIR="$PWD/.showroom-data/tiktoken"
.venv/bin/python scripts/smoke_import.py
scripts/qdrant_local.sh start
```
<!-- setup:end -->

### Menjalankan

| Tujuan | Perintah | Bukti yang dihasilkan |
|---|---|---|
| Uji mock (tanpa layanan) | `.venv/bin/python scripts/receipt.py` | receipt `mock-only` |
| Uji Qdrant nyata, embedding leksikal | `SHOWROOM_INTEGRATION=1 .venv/bin/python scripts/receipt.py` | receipt `lexical` |
| Uji penuh, embedding OpenAI nyata | `set -a; . ./.env; set +a; SHOWROOM_INTEGRATION=1 SHOWROOM_EMBEDDINGS=openai .venv/bin/python scripts/receipt.py` | receipt `openai` (menutup A1/A2) |
| Kalibrasi ambang | `SHOWROOM_EMBEDDINGS=openai .venv/bin/python scripts/calibrate.py` | `.showroom-data/calibration-*.json` |
| Matikan Qdrant | `scripts/qdrant_local.sh stop` | — |

Receipt (`.showroom-data/receipts/<commit>-<mode>.json`) hanya sah bila tree bersih dan semua uji lulus.
Mock ≠ integrasi ≠ observasi langsung: baca `limitations` di setiap receipt.
