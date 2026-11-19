# PANDUAN MENJALANKAN & DEPLOY MENCARE AI

## 1. Paket yang harus disiapkan

Ekstrak file ZIP. Pastikan struktur folder memiliki:

- `streamlit_app.py` — aplikasi utama
- `risk_engine.py` — fuzzy risk-factor demo dan aturan rekomendasi
- `requirements.txt` — dependensi
- `.streamlit/config.toml` — tema
- `tests/test_risk_engine.py` — pengujian otomatis

## 2. Menjalankan pada laptop

Pasang Python 3.10 atau lebih baru. Buka Terminal, kemudian:

```bash
cd MenCare_AI_Streamlit_Prototype
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Untuk macOS, bila perintah `python` tidak ada, gunakan `python3`.

Buka alamat yang muncul di Terminal, biasanya `http://localhost:8501`.

## 3. Deploy sehingga mendapatkan link untuk juri

1. Login ke **github.com**, buat repository baru (contoh: `mencare-ai`).
2. Upload seluruh isi folder yang telah diekstrak. Jangan upload ZIP saja sebagai satu file. Pastikan `streamlit_app.py` dan `requirements.txt` berada di root repository.
3. Login di **https://share.streamlit.io/** melalui GitHub.
4. Pilih opsi pembuatan/deployment aplikasi, repository Anda, branch utama, dan isikan `streamlit_app.py` sebagai entrypoint.
5. Klik **Deploy**.
6. Salin alamat publik aplikasi **yang benar-benar muncul sesudah deployment berhasil**. Alamat inilah yang dimasukkan ke kolom **Prototype / Deployment Link**.
7. Buka alamat tersebut dari browser lain dan jalankan simulasi A–D.

Catatan: Tidak ada URL aplikasi yang aktif sebelum Anda mengunggah dan men-deploy proyek.

## 4. Demo untuk juri

- Perlihatkan landing page dan nilai tambah MenCare AI.
- Pilih `Start screening`, isi formulir tahap 1–2.
- Gunakan `Load demo case` untuk **Case B** (konsultasi fertilitas).
- Gunakan **Case C** untuk menunjukkan bahwa gejala darurat langsung memicu rekomendasi darurat.
- Gunakan **Case D** untuk memperlihatkan *oncofertility pathway*.
- Tunjukkan *fuzzy explanation*, checklist follow-up dan unduhan ringkasan.

## 5. Penting untuk aspek medis & keamanan

Aplikasi ini adalah **prototype teknologi untuk demonstrasi**, bukan alat diagnosis. Nilai fuzzy adalah aktivasi pola faktor yang dilaporkan, **bukan probabilitas infertilitas**. Aturan dan bobot masih ilustratif, belum divalidasi dokter. Jangan gunakan data pasien asli pada hosting demo publik.

Prototype ini juga **belum** terhubung ke rumah sakit, belum membukukan janji medis, belum menggunakan model MRI untuk memprediksi kesuburan, dan belum menyimpan data ke database.

Untuk penggunaan klinis diperlukan validasi bersama dokter, persetujuan etik bila relevan, penilaian keamanan data, dan izin/regulasi setempat.
