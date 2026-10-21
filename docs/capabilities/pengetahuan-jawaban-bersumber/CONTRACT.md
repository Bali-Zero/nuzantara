# CONTRACT — pengetahuan → jawaban bersumber

**Unit:** `pengetahuan-jawaban-bersumber` · **Gerbang:** G1 · **Status:** SAH — disahkan maintainer, 14 Okt 2026 (§8 terisi)
**Sumber:** instruksi showroom §4.1 + pengukuran read-only pada snapshot platform internal 14 Okt 2026 (catatan asal internal `SR-U1-2026-10-14`; detail lokasi kode tidak dipublikasikan sesuai aturan publikasi README)

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

- Menulis vektor + payload hanya ke koleksi **`showroom_legal_synthetic`** (§8.4) — bukan koleksi produksi mana pun.
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

## 7. Titik masuk di platform internal (klaim kode, snapshot 14 Okt 2026)

Modul disebut dengan nama saja; lokasi persis ada di catatan asal internal.

| Peran | Modul / simbol | Catatan untuk G2 |
|---|---|---|
| Pengindeksan legal | `HierarchicalIndexer.index_legal_document(document_text, document_id, metadata, qdrant_client)` | Butuh `LegalStructureParser`, `QdrantClient`, `EmbeddingsGenerator`; DB pool opsional — tanpa `DATABASE_URL` parent doc **tidak disimpan, hanya warning** → di showroom harus jadi keputusan eksplisit |
| Jalur ingest legal | `LegalIngestionService.ingest_legal_document` | Default koleksinya adalah koleksi produksi — showroom wajib override |
| Embedding | `EmbeddingsGenerator.generate_embeddings` · dimensi 1536 | Provider dari settings (`openai` / `sentence-transformers`) |
| Pencarian | `SearchService.search(query, user_level, limit, …) -> dict` | **Temuan:** blok penangkap error Qdrant/HTTP mengembalikan `results=[]` + `"error": "Search service temporarily unavailable"` — fail-soft, tidak raise. Kontrak A3 memakai field `error` ini; respons akhir wajib meneruskannya, tidak boleh menelan |
| Kutipan | `CitationService` (`extract_sources_from_rag`, `validate_citations_in_response`) | Kandidat pembentuk `sources[]` |
| Abstain | `AbstainPolicy` · `build_abstain_policy(query)` | Ambang per domain; untuk A2 showroom satu ambang tetap, nilainya dicatat di DEPENDENCIES |
| Orkestrasi | `get_orchestrator` · `LLMGateway` | **Di luar unit pertama** (keputusan §8.1: jalur minimum). Dicatat di DEPENDENCIES sebagai 'sengaja di luar' |

Tes platform internal yang menyentuh modul ini: 50 berkas (kontrol: total tes backend 2.175 berkas). Yang langsung relevan: uji identitas chunk legal, uji layanan ingest legal, uji `CitationService`, uji pengerasan `AbstainPolicy`.

Jalur ingest **umum** (`IngestionService.ingest_book`) tidak dipakai unit ini sampai perbaikan upstream pada jalur itu merged (pending review).

## 8. Keputusan pengesahan (maintainer, 14 Okt 2026)

1. Jalur unit pertama: **jalur minimum** — indexer → search → citation; tanpa orkestrator dan LLM gateway. Orkestrator menjadi kandidat unit berikutnya (G6).
2. Batas waktu A3: **10 detik** (connect timeout + 1 retry).
3. Dokumen tanpa struktur Pasal: **ditolak dengan alasan** (fail-closed); `status=unavailable` tidak dipakai untuk kasus ini — pakai error validasi masukan yang terbaca.
4. Nama koleksi showroom: **`showroom_legal_synthetic`**.

Kontrak ini sah. Perubahan berikutnya hanya lewat PR di repo ini dengan catatan alasan.
