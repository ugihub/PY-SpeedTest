# ⚡ PY-SpeedTest

**Network Quality of Service Tester berbasis Socket Programming**

Aplikasi desktop untuk mengukur kualitas jaringan internet (download, upload, ping, jitter) dengan antarmuka modern dan fitur AI analysis menggunakan Mistral AI.

> **Tugas Besar - Jaringan Komputer**
> - Nama: Ugi Sugiman Rahmatullah
> - NPM: 714240016
> - Kelas: D4 Teknik Informatika 2B

---

## 📸 Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🚀 **Speed Test** | Pengujian download & upload menggunakan multi-threaded socket programming |
| 📡 **Ping & Jitter** | Mengukur latency dan variasi latency menggunakan TCP socket |
| 📈 **Visualisasi** | Grafik history speed & latency dengan Matplotlib |
| 🤖 **AI Analysis** | Analisis otomatis hasil tes menggunakan Mistral AI (RAG) |
| 💬 **Network Chatbot** | Chatbot AI untuk bertanya seputar jaringan dan hasil speedtest |
| 📊 **History** | Penyimpanan history tes ke CSV lokal dan Supabase cloud |
| 🌐 **Auto Server** | Pemilihan server otomatis berdasarkan latency terendah |
| 🎨 **Modern UI** | Antarmuka CustomTkinter dengan Grey/Blue Ocean theme |

---

## 🗂️ Struktur File

```
TB/
├── pyspeedtest.pyw   # UI utama (Modern CustomTkinter)
├── rag_manager.py           # Mistral AI RAG Analyzer (AI analysis & chatbot)
├── supabase_manager.py      # Database manager (Supabase + pgvector)
├── requirements.txt         # Daftar dependencies Python
├── speed_test_history.csv   # History hasil tes (auto-generated)
└── Export .EXE/
    ├── pyinstaller_spec.spec    # Konfigurasi PyInstaller untuk build EXE
    └── pyi_rth_speedtest.py     # Runtime hook fix untuk PyInstaller
```

---

## 🔧 Teknologi yang Digunakan

| Kategori | Teknologi |
|----------|-----------|
| **Bahasa** | Python 3.13 |
| **GUI** | CustomTkinter, Tkinter |
| **Grafik** | Matplotlib (TkAgg backend) |
| **Networking** | Socket Programming (TCP), speedtest-cli |
| **AI/LLM** | Mistral AI API (chat & embedding) |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Build** | PyInstaller |

---

## ⚙️ Cara Instalasi & Menjalankan

### Opsi 1: Jalankan dari Source Code

1. **Clone / download project**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Konfigurasi Mistral API dan SUPABASE**
   ```bash
   mistral_key = "YOUR_API_KEY"
   supabase_url = "YOUR_SUPA_URL"
   supabase_key = "YOUR_SUPA_KEY"
   ```

4. **Jalankan aplikasi**
   ```bash
   python pyspeedtest.pyw
   ```

### Opsi 2: Jalankan EXE (Tanpa Install Python)

langsung download file .exe dari **Releases**

### Build EXE dari Source

```bash
pyinstaller pyinstaller_spec.spec --clean --noconfirm
```
Hasil build akan tersedia di folder `dist/`.

---

## 🏗️ Arsitektur Aplikasi

```
┌──────────────────────────────────────────────┐
│           pyspeedtest_modern.pyw              │
│         (Modern UI - CustomTkinter)           │
│                                               │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Charts  │  │Speed Test│  │ AI Analysis  │  │
│  │(History)│  │ Control  │  │   Panel      │  │
│  └─────────┘  └──────────┘  └─────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │    Modals: History | Chatbot            │  │
│  └─────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────┘
                   │ import
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│pyspeedtest│ │   rag    │ │   supabase   │
│   .pyw   │ │manager.py│ │ manager.py   │
│          │ │          │ │              │
│ Network  │ │ Mistral  │ │  Supabase    │
│ Tester   │ │ AI RAG   │ │  Database    │
│ (Socket) │ │ Analyzer │ │  + pgvector  │
└──────────┘ └──────────┘ └──────────────┘
```

---

## 📡 Detail Teknis - Socket Programming

### Pengujian Latency (Ping)
- Menggunakan **TCP Socket** untuk mengukur round-trip time
- 10 kali pengukuran, diambil rata-rata
- Jitter dihitung dari variasi antar latency

### Pengujian Download
- **Multi-threaded** (12 koneksi paralel)
- Download dari server speedtest terdekat
- Durasi tes: 15 detik
- Real-time progress callback

### Pengujian Upload
- Menggunakan **speedtest-cli** untuk akurasi
- Fallback ke TCP socket upload jika gagal
- Multi-threaded connection

### Pemilihan Server
- Scanning beberapa server speedtest Indonesia
- Dipilih berdasarkan latency terendah

---

## 🤖 Sistem AI (RAG)

Aplikasi menggunakan **Retrieval-Augmented Generation (RAG)** dengan:

- **Mistral AI** — Model LLM untuk analisis dan chatbot
- **Mistral Embeddings** — Konversi teks ke vektor (1024 dimensi)
- **Supabase pgvector** — Penyimpanan dan pencarian vektor similarity
- **Konteks historis** — AI membandingkan hasil tes saat ini dengan history sebelumnya

### Fitur AI:
1. **Quick Summary** — Ringkasan otomatis setelah setiap tes
2. **Full Analysis** — Analisis mendalam performa jaringan
3. **Network Chatbot** — Tanya jawab tentang jaringan dan history tes

---

## 📋 Dependencies

```
speedtest-cli          # Core speed testing
customtkinter>=5.0.0   # Modern UI framework
matplotlib>=3.5.0      # Charts & visualization
mistralai>=1.0.0       # AI analysis (Mistral API)
supabase>=2.0.0        # Cloud database
pillow>=10.0.0         # Image processing
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical operations
pyinstaller>=6.0.0     # Build to EXE
```

---

## 📝 Lisensi

Project ini dibuat untuk keperluan Tugas Besar mata kuliah Jaringan Komputer.
