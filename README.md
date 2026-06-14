# LaTeX AI Editor

Sebuah aplikasi editor LaTeX berbasis lokal yang dibantu AI untuk bikin ringkasan atau catatan belajar secara otomatis. Aplikasi ini bisa baca berbagai macam sumber materi belajar kamu (PDF, gambar, video YouTube, artikel web) dan ngerangkumnya jadi dokumen LaTeX yang rapi dan siap dikompilasi jadi PDF.

## Fitur Utama

- Topic-based Knowledge Base: Kamu bisa bikin banyak topik terpisah. Tiap topik punya data sumber, dokumen LaTeX, dan PDF-nya masing-masing.
- Mistral OCR: Upload file PDF atau gambar, teksnya bakal diekstrak pakai API Mistral OCR. Sudah diset supaya bisa pakai 7 API key secara bergantian (round-robin) biar gak cepat limit.
- YouTube Caption Extractor: Tinggal paste link YouTube, aplikasi bakal otomatis ngambil transkrip videonya lengkap dengan timestamp.
- Web Fetch API: Paste link artikel atau website, konten teks utamanya bakal diambil otomatis (tanpa lewat LLM, murni web fetch).
- LaTeX Generator: Semua teks yang dikumpulin dari sumber-sumber tadi bakal dirangkum sama AI (via 9Router) jadi kode LaTeX beneran. Tersedia preset style seperti "Summary", "Study Notes", atau kamu bisa custom sendiri.
- Interactive PDF Viewer: Hasil kompilasi PDF bisa dilihat langsung di aplikasi. Kamu bisa coret-coret, highlight, tambah teks, atau garis bawah langsung di atas PDF-nya.
- Targeted Revision: Kurang puas sama hasil generate AI? Tandai area di PDF pakai tool "Select to Revise", copy request-nya, lalu suruh AI untuk nge-revisi HANYA bagian itu tanpa ngerusak sisa dokumen yang udah bener.
- Download Annotated PDF: Hasil PDF yang udah dicoret-coret bisa langsung didownload.

## Cara Install dan Persiapan

1. Pastikan Python sudah terinstall di komputermu (minimal Python 3.10 ke atas).
2. Pastikan kamu juga sudah punya pdflatex (dari MiKTeX atau TeX Live) dan sudah terdaftar di PATH system kamu biar aplikasinya bisa nge-compile LaTeX ke PDF.
3. Install semua library yang dibutuhin:
   pip install -r requirements.txt
4. Setup konfigurasi API:
   - Buka file config.json di folder utama.
   - Isi "mistral_keys" dengan API key Mistral OCR kamu (bisa sampai 7 key).
   - Isi "router" dengan base URL, API key, dan nama model dari 9Router untuk proses LLM-nya.

## Cara Menjalankan

Kamu bisa langsung jalanin file run.bat dengan cara double-click, atau lewat terminal dengan command:

py -m streamlit run src/app.py

Aplikasi bakal otomatis terbuka di browser kamu di alamat http://localhost:8501.

## Struktur Folder

- src/: Berisi semua source code Python (app.py, UI, services, dll) dan file HTML untuk viewer PDF.
- data/: Folder ini bakal muncul otomatis buat nyimpan data topik (topics.json) dan file hasil kompilasi (folder pdfs/).
- config.json: File buat nyimpen semua kunci rahasia dan settingan server.
- requirements.txt: Daftar library Python.