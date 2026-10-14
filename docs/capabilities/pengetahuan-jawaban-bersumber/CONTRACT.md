# CONTRACT — pengetahuan → jawaban bersumber

**Unit:** `pengetahuan-jawaban-bersumber` · **Gerbang:** G1 · **Status:** SAH — disahkan Subhi 14 Okt 2026 (§8 terisi)
**Tujuan di repo baru:** `docs/capabilities/pengetahuan-jawaban-bersumber/CONTRACT.md` (Bali-Zero/nuzantara, main `cb2ecf00b7` per ls-remote 14 Okt 09:03 WITA)
**Ditulis:** Atlas (Claude), 14 Okt 2026 · **Sumber:** INSTRUKSI SHOWROOM v1 §4.1 + pengukuran read-only Teman2 `origin/main` 84535dfcb8 (14 Okt 09:03 WITA, sparse clone cloud — bukan checkout Subhi)

## 1. Satu kalimat

Dokumen **sintetis** masuk pengindeksan; sebuah pertanyaan memicu pencarian; kutipan terpilih; respons menampilkan sumber yang bisa ditelusuri kembali ke dokumen itu.

## 2. Masukan

| # | Masukan | Bentuk | Batas |
|---|---|---|---|
| I1 | Korpus contoh | ≥ 3 dokumen teks sintetis berstruktur legal Indonesia (BAB → Pasal → Ayat), dibuat khusus untuk showroom | Nol dokumen produksi, nol data klien, nol nama nyata |
| I2 | Pertanyaan | string bahasa Indonesia atau Inggris, ≤ 500 karakter | — |
| I3 | Konfigurasi | URL vector store + kredensial embedding, **lewat env**, tidak pernah di repo | Model embedding `text-embedding-3-small` (1536) — FROZEN |

## 3. Keluaran

Satu objek respons dengan tiga bagian wajib:

1. `answer` — teks jawaban, **atau** penanda abstain;
2. `sources[]` — daftar rujukan; setiap rujukan memuat `document_id`, `chunk_id`/`pasal`, dan potongan teks yang dikutip; setiap `document_id` harus ada di korpus I1 (bisa ditelusuri);
3. `status` — satu dari `supported` · `unsupported` · `unavailable`.

Invarian: `status=supported` ⇒ `sources` tidak kosong; `status≠supported` ⇒ `answer` bukan kalimat yang mengklaim fakta.

## 4. Efek samping yang boleh

- Menulis vektor + payload hanya ke koleksi **`showroom_legal_synthetic`** (§8.4) — bukan `legal_unified` atau koleksi produksi mana pun.
- Menulis log tanpa isi dokumen, tanpa kredensial, tanpa PII.
- Tidak boleh: menulis DB produksi, menyentuh koleksi produksi, memanggil layanan luar selain embedding + vector store yang dikonfigurasi.

## 5. Kondisi gagal yang dipahami

| Kondisi | Perilaku wajib | Bukan |
|---|---|---|
| Vector store tidak terjangkau | `status=unavailable` + pesan error terbaca di respons; proses selesai ≤ 10 s (§8.2) | hang, respons kosong diam-diam, jawaban lancar |
| Embedding gagal (kunci salah/kuota) | sama seperti di atas; error dari penyedia **tidak** dibocorkan utuh (tanpa kunci/token) | retry tanpa batas |
| Tidak ada bukti relevan | `status=unsupported`, `answer` = kalimat abstain tetap, `sources=[]` | kalimat lancar tanpa sumber |
| Dokumen masukan tanpa struktur Pasal | ditolak dengan alasan yang terbaca (§8.3) | gagal diam-diam |

## 6. Tiga kondisi penerimaan (G4 harus lulus dari clone bersih)

| # | Nama | Masukan | Hasil yang diterima |
|---|---|---|---|
| A1 | **Didukung** | Pertanyaan yang jawabannya ada di Pasal tertentu dokumen sintetis | `status=supported`; ≥ 1 `sources[]` menunjuk `document_id` + `pasal` yang benar; kutipan muncul di dokumen asal (uji: substring) |
| A2 | **Tidak didukung** | Pertanyaan tentang topik yang tidak ada di korpus (mis. cuaca, nama orang fiktif lain) | `status=unsupported`; `sources=[]`; `answer` = penanda abstain, bukan kalimat fakta |
| A3 | **Layanan tidak tersedia** | Vector store dimatikan / URL salah; embedding dengan kunci kosong | `status=unavailable`; ada `error` terbaca; durasi < batas waktu; proses keluar bersih (exit code ≠ hang) |

Penilaian pada sifat stabil: bukti relevan, rujukan sah, struktur respons, perilaku saat gagal. Kesamaan kata hanya di uji terkendali, bukan kriteria tunggal.

## 7. Titik masuk terukur di Teman2 (klaim K, `origin/main` 84535dfcb8, 14 Okt)

| Peran | Lokasi terukur | Catatan untuk G2 |
|---|---|---|
| Pengindeksan legal | `core/legal/hierarchical_indexer.py:56` `HierarchicalIndexer` · `:94` `index_legal_document(document_text, document_id, metadata, qdrant_client)` | Butuh `LegalStructureParser`, `QdrantClient`, `EmbeddingsGenerator`; DB pool opsional — tanpa `DATABASE_URL` parent doc **tidak disimpan, hanya warning** (`:77-93`) → di showroom harus jadi keputusan eksplisit |
| Jalur ingest legal | `services/ingestion/legal_ingestion_service.py:296` `LegalIngestionService` · `:455` `ingest_legal_document` | Default koleksi `legal_unified` (`:302`) — showroom wajib override |
| Embedding | `core/embeddings.py:208` `EmbeddingsGenerator` · `:326` `generate_embeddings` · dimensi 1536 (`:263`) | Provider dari settings (`openai` / `sentence-transformers`) |
| Pencarian | `services/search/search_service.py:84` `SearchService` · `:576` `search(query, user_level, limit, …) -> dict` | **Temuan:** `:756-775` menangkap error Qdrant/HTTP dan mengembalikan `results=[]` + `"error": "Search service temporarily unavailable"` — fail-soft, tidak raise. Kontrak A3 memakai field `error` ini; respons akhir wajib meneruskannya, tidak boleh menelan |
| Kutipan | `services/search/citation_service.py:19` `CitationService` (`extract_sources_from_rag :87`, `validate_citations_in_response :208`) | Kandidat pembentuk `sources[]` |
| Abstain | `services/rag/agentic/_abstain_policy.py:57` `AbstainPolicy` · `:103` `build_abstain_policy(query)` | Ambang per domain; untuk A2 showroom satu ambang tetap, nilainya dicatat di DEPENDENCIES |
| Orkestrasi | `app/deps/orchestrator.py:71` `get_orchestrator` · `services/rag/agentic/llm_gateway.py:208` `LLMGateway` | **Di luar unit pertama** (keputusan §8.1: jalur minimum). Dicatat di DEPENDENCIES sebagai 'sengaja di luar' |

Tes Teman2 yang menyentuh modul ini: 50 berkas (kontrol: total tes backend 2.175 berkas). Yang langsung relevan: `tests/unit/core/legal/test_chunk_identity_collisions.py`, `tests/unit/services/ingestion/test_legal_ingestion_service.py`, `tests/services/search/test_citation_service.py`, `tests/services/rag/agentic/test_abstain_policy_hardening.py`.

Jalur ingest **umum** (`ingestion_service.py`, E34) tidak dipakai unit ini sampai PR 8070 merged (DAI-8/13: siap merge, menunggu Antonello).

## 8. Keputusan pengesahan (Subhi, 14 Okt 2026)

1. Jalur unit pertama: **jalur minimum** — indexer → search → citation; tanpa orkestrator dan LLM gateway. Orkestrator menjadi kandidat unit berikutnya (G6).
2. Batas waktu A3: **10 detik** (connect timeout + 1 retry).
3. Dokumen tanpa struktur Pasal: **ditolak dengan alasan** (fail-closed); `status=unavailable` tidak dipakai untuk kasus ini — pakai error validasi masukan yang terbaca.
4. Nama koleksi showroom: **`showroom_legal_synthetic`**.

Kontrak ini sah. Perubahan berikutnya hanya lewat PR di repo ini dengan catatan alasan.
