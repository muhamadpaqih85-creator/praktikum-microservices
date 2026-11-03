# LAPORAN PRAKTIKUM SISTEM TERDISTRIBUSI
## Modul Praktikum: Arsitektur Microservice dengan Python, MySQL, PostgreSQL, dan Nginx API Gateway

**Mata Kuliah:** Sistem Terdistribusi  
**Program Studi:** S1 Informatika  
**Nama Mahasiswa / Kelompok:** Muhamad Paqih Mubarok & Tim  
**Tahun Akademik:** 2026/2027  

---

## 1. Ringkasan Eksekutif & Tujuan Praktikum

Praktikum ini bertujuan untuk merancang, mengimplementasikan, dan menguji sistem terdistribusi berbasis **arsitektur microservice** dengan pola **Database-per-Service** dan **API Gateway Pattern**. 

Sistem terdiri atas:
1. **Mahasiswa Service**: Menggunakan Python (Flask) dan database MySQL (`mahasiswa_db`), menangani data master mahasiswa dan Kartu Rencana Studi (KRS).
2. **Mata Kuliah Service**: Menggunakan Python (Flask) dan database PostgreSQL (`matkul_db`), menangani katalog mata kuliah.
3. **Nginx API Gateway**: Bertindak sebagai reverse proxy pintu gerbang tunggal (port 8080) dengan routing berbasis path (`/mahasiswa`, `/matkul`, `/`) serta menyajikan Dashboard Web statis.
4. **Komunikasi Antar-Layanan**: Komunikasi HTTP/REST sinkron antara Mahasiswa Service dan Mata Kuliah Service saat proses validasi KRS.
5. **Orkestrasi Docker Compose**: Mengotomatisasi deployment 5 kontainer (2 database, 2 Flask app, 1 Nginx) dalam satu virtual network terisolasi.

---

## 2. Arsitektur Sistem & Diagram Alur

### 2.1 Diagram Arsitektur

```text
                     +---------------------------------------+
                     |         Pengguna / Client             |
                     |     (Web Browser / curl / Postman)    |
                     +-------------------+-------------------+
                                         |
                                         | HTTP Request (Port 8080)
                                         v
                     +---------------------------------------+
                     |          Nginx API Gateway            |
                     |  - Reverse Proxy (Reverse Routing)    |
                     |  - Host Dashboard UI (/)              |
                     +---------+-------------------+---------+
                               |                   |
            Path: /mahasiswa/* |                   | Path: /matkul/*
                               v                   v
                     +-------------------+   +-------------------+
                     | Mahasiswa Service |   |  Matkul Service   |
                     |   (Flask :5000)   |   |   (Flask :5000)   |
                     +---------+---------+   +---------+---------+
                               |       |               ^
             SQL Query / ORM   |       | HTTP (REST)   | SQL Query / ORM
                               v       +---------------+ v
                     +-------------------+   Validasi  +-------------------+
                     |     MySQL 8.0     |   kode_mk   |   PostgreSQL 16   |
                     |  (mahasiswa_db)   |             |    (matkul_db)    |
                     +-------------------+             +-------------------+
```

### 2.2 Pola Desain yang Digunakan
1. **Database-per-Service**: Setiap layanan memiliki skema dan database engine independen. Layanan Mahasiswa tidak memiliki akses jaringan maupun kredensial ke database PostgreSQL Mata Kuliah, begitu pula sebaliknya. Integritas data dijaga di level aplikasi via API.
2. **API Gateway Pattern**: Klien eksternal hanya berinteraksi dengan satu endpoint (`http://localhost:8080`). Ini menyembunyikan detail topologi jaringan internal, menyederhanakan konfigurasi CORS, dan mempermudah penerapan cross-cutting concerns (logging, SSL termination, caching).
3. **Internal Docker DNS Discovery**: Nginx dan kontainer backend berkomunikasi melalui nama service Docker (`http://mahasiswa-service:5000` dan `http://matkul-service:5000`), bukan alamat IP statis.

---

## 3. Pembagian Peran dan Kolaborasi Git

Sesuai panduan praktikum, repositori dikelola menggunakan fitur branching Git dan pull request:
- **Branch `feature/mahasiswa` (Peserta A)**:
  - Direktori `mahasiswa-service/`
  - Implementasi CRUD mahasiswa, tabel `mahasiswa` & `krs`, serta pemanggilan HTTP ke Matkul Service.
- **Branch `feature/matkul` (Peserta B)**:
  - Direktori `matkul-service/`
  - Implementasi CRUD mata kuliah, tabel `mata_kuliah`, serta inisialisasi data awal (seeding data).
- **Branch `feature/gateway` (Peserta C)**:
  - Direktori `gateway/` dan `docker-compose.yml`
  - Konfigurasi Nginx proxy pass, Web Dashboard interaktif, dan orkestrasi seluruh kontainer.
- **Branch `main`**:
  - Menggabungkan ketiga branch melalui merge commit (`--no-ff`), menjaga riwayat kontribusi setiap anggota.

---

## 4. Jawaban Pertanyaan Analisis

### Pertanyaan 1:
> **Mengapa tabel `krs` hanya menyimpan `kode_mk` tanpa foreign key ke tabel mata kuliah? Apa konsekuensinya bila mata kuliah dihapus setelah diambil mahasiswa? Usulkan solusinya.**

**Jawaban:**
1. **Alasan Teknis & Arsitektural:**  
   Dalam pola *Database-per-Service*, database `mahasiswa_db` (MySQL) dan `matkul_db` (PostgreSQL) berada pada server/kontainer fisik/logis yang terpisah. Database relasional standar **tidak mendukung foreign key lintas server atau lintas database engine yang berbeda**. Secara prinsip microservice, menambahkan dependensi langsung di level basis data akan merusak independensi (*loose coupling*), otonomi deploy, serta enkapsulasi data service. Oleh karena itu, tabel `krs` hanya menyimpan identifier referensi logis berupa string `kode_mk`.

2. **Konsekuensi Penghapusan:**  
   Jika sebuah mata kuliah dihapus di `matkul-service` setelah sebelumnya diambil oleh mahasiswa, data pada tabel `krs` akan menjadi data yatim (*orphaned data*). Ketika endpoint `GET /mahasiswa/{nim}/matkul` dipanggil, `mahasiswa-service` gagal menemukan detail mata kuliah tersebut (mengembalikan `catatan: detail matkul tidak tersedia` atau data parsial). Mahasiswa masih tercatat mengambil kode MK yang sudah tidak ada di kurikulum aktif.

3. **Usulan Solusi:**
   - **Solusi 1 (Event-Driven / Pub-Sub Architecture):**  
     Gunakan message broker (misalnya RabbitMQ, Apache Kafka, atau Redis Pub/Sub). Ketika mata kuliah dihapus di `matkul-service`, service tersebut memublikasikan event `CourseDeleted(kode_mk)`. `mahasiswa-service` mendengarkan (*subscribe*) event ini dan secara otomatis membatalkan/menghapus record KRS terkait atau menandainya sebagai *archived*.
   - **Solusi 2 (Soft Delete & Validation Callback):**  
     Terapkan pola *Soft Delete* (kolom `is_deleted` atau `status='inactive'`) pada Mata Kuliah alih-alih hard delete. Jika ingin hard delete, `matkul-service` terlebih dahulu memanggil endpoint validasi di `mahasiswa-service` (misalnya `GET /krs/count?kode_mk=...`) dan menolak penghapusan jika masih ada mahasiswa terdaftar (status 400/409).
   - **Solusi 3 (Saga Pattern):**  
     Menggunakan orchestrator atau choreography Saga untuk mengelola transaksi terdistribusi kompensasi jika terjadi pembatalan matkul di seluruh sistem.

---

### Pertanyaan 2:
> **Pada skenario 9, apa yang terjadi saat Matkul Service mati? Jelaskan istilah *coupling* dan *single point of failure* (SPOF) terkait hal ini.**

**Jawaban:**
1. **Apa yang terjadi saat Matkul Service mati:**  
   - Mahasiswa Service tidak dapat memvalidasi mata kuliah saat proses KRS baru (`POST /mahasiswa/{nim}/matkul`). Blok `try ... except requests.RequestException` menangkap kegagalan koneksi (timeout atau connection refused) dan mengembalikan respons HTTP `503 Service Unavailable` dengan pesan `{"error": "matkul-service tidak dapat dihubungi"}`.
   - Endpoint pembacaan KRS (`GET /mahasiswa/{nim}/matkul`) menerapkan mekanisme *graceful degradation*: mahasiswa tetap melihat daftar `kode_mk` yang diambil, namun atribut nama dan SKS digantikan pesan fallback `{"catatan": "detail matkul tidak tersedia"}` tanpa menyebabkan Mahasiswa Service crash.
   - CRUD Mahasiswa (`GET`, `POST`, `PUT`, `DELETE /mahasiswa`) tetap berjalan normal 100%.

2. **Keterkaitan Konsep:**
   - **Runtime / Temporal Coupling:**  
     Komunikasi sinkron via REST HTTP menciptakan ketergantungan temporal (*runtime coupling*). Agar aksi *ambil matkul* berhasil, **kedua service harus aktif dan dapat dihubungi pada saat yang bersamaan**. Jika salah satu downstream service down atau lambat, request upstream ikut tertahan (*cascading failure*).
   - **Single Point of Failure (SPOF):**  
     Bagi alur pengambilan KRS, Matkul Service menjadi titik kegagalan tunggal (*SPOF*). Meskipun database MySQL dan Mahasiswa Service sehat, fungsionalitas KRS tetap terhenti secara total. Di level infrastruktur luar, Nginx API Gateway juga berpotensi menjadi SPOF jika hanya dijalankan satu instance tanpa redundansi (misalnya tanpa Keepalived / Virtual IP atau Cloud Load Balancer).

---

### Pertanyaan 3:
> **Apa keuntungan dan kerugian memakai MySQL dan PostgreSQL pada dua service berbeda dibanding satu database bersama?**

**Jawaban:**

| Aspek | MySQL & PostgreSQL Terpisah (Database per Service) | Satu Database Bersama (*Shared Database*) |
|---|---|---|
| **Keuntungan** | 1. **Polyglot Persistence**: Tiap tim dapat memilih database yang paling sesuai dengan karakteristik bebannya (misal: PostgreSQL untuk fitur JSON/GIS canggih, MySQL untuk read-throughput tinggi).<br>2. **Isolasi Kegagalan**: Kegagalan server MySQL tidak akan mematikan service Mata Kuliah.<br>3. **Independensi Deployment & Schema**: Perubahan skema di satu tabel tidak memerlukan izin atau memengaruhi tim service lain.<br>4. **Skalabilitas**: Beban database terbagi secara fisik (horizontal scaling per database). | 1. **ACID Cross-Table**: Mudah menggunakan *Foreign Key* dan transaksi antar-tabel (JOIN langsung).<br>2. **Operasional Sederhana**: Hanya perlu memelihara, mem-backup, dan memantau 1 instance database.<br>3. **Biaya Infrastruktur Lebih Rendah**: Kebutuhan memori awal lebih sedikit. |
| **Kerugian** | 1. **Biaya Operasional**: Tim DevOps harus mengelola dua DBMS berbeda (konfigurasi, backup, patch, monitoring).<br>2. **Konsistensi Data**: Tidak ada foreign key bawaan; risiko integritas data harus ditangani di kode aplikasi.<br>3. **Konsumsi Resource**: Membutuhkan RAM/CPU lebih besar karena menjalankan dua engine database secara simultan. | 1. **High Coupling**: Service saling bergantung pada skema database; perubahan kecil bisa merusak banyak service.<br>2. **Resource Contention**: Query berat di satu service dapat menghabiskan connection pool atau CPU untuk seluruh sistem.<br>3. **SPOF**: Jika database crash, seluruh sistem mati serentak. |

---

### Pertanyaan 4:
> **Apa peran API Gateway dalam sistem ini? Sebutkan minimal tiga fungsi lain yang dapat ditambahkan pada gateway (misalnya autentikasi, rate limiting, load balancing).**

**Jawaban:**
1. **Peran API Gateway dalam Sistem Ini:**  
   - **Single Entry Point & Reverse Proxy:** Mengonsolidasikan port dan domain sehingga klien hanya perlu mengakses port `8080`.
   - **Request Routing (Path-Based Routing):** Meneruskan lalu lintas `/mahasiswa` ke kontainer `mahasiswa-service:5000` dan `/matkul` ke `matkul-service:5000`.
   - **Static Content Hosting:** Menyajikan antarmuka Dashboard HTML/CSS/JS tanpa memerlukan web server terpisah.
   - **Eliminasi CORS:** Karena browser mengakses frontend dan API pada origin yang sama (`http://localhost:8080`), tidak timbul masalah *Cross-Origin Resource Sharing (CORS)*.

2. **Tiga Fungsi Lain yang Dapat Ditambahkan:**  
   - **Autentikasi & Otorisasi Terpusat:** Gateway dapat memvalidasi JWT token atau API Key sebelum request diteruskan ke backend. Service backend tidak perlu lagi mengulang logika verifikasi token.
   - **Rate Limiting & DDoS Protection:** Membatasi jumlah permintaan per detik/menit per IP klien (misal dengan modul `ngx_http_limit_req_module`) untuk mencegah *brute-force* atau kelebihan beban (*traffic spike*).
   - **Load Balancing & Failover:** Mendistribusikan beban secara merata ke beberapa replika kontainer (misal: 3 instance `matkul-service`) menggunakan algoritma Round Robin, Least Connections, atau IP Hash.

---

### Pertanyaan 5:
> **Jika jumlah mahasiswa sangat besar, service mana yang perlu di-scale lebih dulu dan bagaimana caranya? Bagaimana peran Nginx dalam skenario tersebut?**

**Jawaban:**
1. **Service yang Perlu Di-Scale Terlebih Dahulu:**  
   - **Mahasiswa Service** harus di-scale terlebih dahulu.  
   - **Alasan:** Pada periode pengisian KRS atau registrasi akademik (pendaftaran mahasiswa), lalu lintas read dan write pada Mahasiswa Service akan melonjak drastis ribuan kali lipat dibandingkan Mata Kuliah Service (katalog mata kuliah cenderung statis dan jarang berubah).

2. **Cara Melakukan Scaling:**  
   - **Horizontal Pod/Container Autoscaling:** Menambah replika kontainer Mahasiswa Service (misalnya dari 1 instance menjadi 5 instance) dengan perintah:
     ```bash
     docker compose up --scale mahasiswa-service=5 -d
     ```
   - **Database Scaling (MySQL):** Menerapkan *Read Replicas* (Master-Slave replication). Operasi `GET /mahasiswa` dialihkan ke database replica, sedangkan `POST`/`PUT`/`DELETE` tetap ke primary database.
   - **Caching Layer:** Menambahkan Redis di depan Mahasiswa Service dan Matkul Service untuk menyimpan cache query data mata kuliah dan mahasiswa.

3. **Peran Nginx API Gateway:**  
   - Nginx dikonfigurasi dengan blok `upstream` untuk melakukan **Load Balancing**:
     ```nginx
     upstream backend_mahasiswa {
         least_conn;
         server mahasiswa-service-1:5000;
         server mahasiswa-service-2:5000;
         server mahasiswa-service-3:5000;
     }
     ```
   - Nginx secara otomatis membagi beban request dari ribuan browser mahasiswa ke seluruh replika kontainer secara seimbang dan melakukan *active/passive healthcheck* (otomatis menghapus kontainer yang tidak merespons dari pool upstream).

---

### Pertanyaan 6:
> **Bandingkan komunikasi sinkron (REST) dengan asinkron (message broker seperti RabbitMQ). Kapan masing-masing lebih cocok?**

**Jawaban:**

| Parameter | Komunikasi Sinkron (REST HTTP / gRPC) | Komunikasi Asinkron (Message Broker / AMQP / Kafka) |
|---|---|---|
| **Mekanisme** | Request-Response langsung. Pengirim berhenti dan menunggu balasan hingga server selesai memproses. | Fire-and-Forget / Event-Driven. Pengirim menaruh pesan di queue/topic dan langsung melanjutkan prosesnya tanpa menunggu consumer selesai. |
| **Coupling** | **Tight runtime coupling**: Keduanya harus online dan memiliki latensi jaringan yang baik. | **Loose coupling**: Pengirim tidak perlu tahu siapa atau berapa banyak consumer yang memproses pesan. |
| **Ketahanan (*Resilience*)**| Jika receiver down, request gagal seketika (menghasilkan 500/503 atau timeout). | Jika receiver down, pesan tetap tersimpan aman di queue (*message persistence*) dan diproses saat receiver menyala kembali. |
| **Kompleksitas** | Relatif rendah, mudah di-debug, tidak memerlukan komponen perantara tambahan. | Lebih tinggi, membutuhkan cluster message broker, penanganan *dead-letter queue*, *duplicate message*, dan konsistensi eventual. |

**Kapan Masing-masing Lebih Cocok Digunakan?**
- **Gunakan REST (Sinkron):**  
  - Ketika klien **membutuhkan respons seketika** (*immediate feedback*) untuk melanjutkan alur pengguna. Contoh: Login/autentikasi pengguna, membaca detail profil, validasi real-time ketersediaan kuota kelas saat tombol ditekan.
- **Gunakan Message Broker (Asinkron):**  
  - Untuk tugas berdurasi panjang (*long-running background jobs*), seperti: pengiriman email notifikasi KRS, pembuatan file rekap transkrip PDF, sinkronisasi data antar-service (misalnya penghapusan matkul mengabari KRS), dan pengolahan data analitik berskala besar.

---

## 5. Bukti Hasil Pengujian Integrasi (Skenario 1 – 10)

Seluruh skenario integrasi diuji melalui API Gateway (`http://localhost:8080`) dan tercatat dengan hasil 100% BERHASIL (PASS):

| No | Skenario Pengujian | HTTP Method & URL | Body / Parameter | Hasil Status | Respons JSON / Output | Status Uji |
|:---:|---|---|---|:---:|---|:---:|
| **1** | Tambah Mahasiswa Baru | `POST /mahasiswa` | `{"nim":"2210001","nama":"Budi","email":"budi@mail.com","angkatan":2022}` | **201 Created** | `{"nim":"2210001","nama":"Budi","email":"budi@mail.com","angkatan":2022}` | **BERHASIL** |
| **2** | Validasi NIM Duplikat | `POST /mahasiswa` | `{"nim":"2210001","nama":"Budi Duplikat"}` | **409 Conflict** | `{"error":"NIM sudah terdaftar"}` | **BERHASIL** |
| **3** | Tambah Mata Kuliah | `POST /matkul` | `{"kode":"IF304","nama":"Kecerdasan Buatan","sks":3,"semester":5}` | **201 Created** | `{"kode":"IF304","nama":"Kecerdasan Buatan","semester":5,"sks":3}` | **BERHASIL** |
| **4** | Ambil Mata Kuliah (KRS) | `POST /mahasiswa/2210001/matkul` | `{"kode_mk":"IF301"}` | **201 Created** | `{"kode_mk":"IF301","nim":"2210001","pesan":"berhasil"}` | **BERHASIL** |
| **5** | Ambil MK Tidak Ada | `POST /mahasiswa/2210001/matkul` | `{"kode_mk":"XX999"}` | **404 Not Found** | `{"error":"mata kuliah tidak ditemukan"}` | **BERHASIL** |
| **6** | Ambil MK Dua Kali (Duplikat) | `POST /mahasiswa/2210001/matkul` | `{"kode_mk":"IF301"}` | **409 Conflict** | `{"error":"mata kuliah sudah diambil"}` | **BERHASIL** |
| **7** | Lihat KRS Mahasiswa | `GET /mahasiswa/2210001/matkul` | *(none)* | **200 OK** | `[{"kode":"IF301","kode_mk":"IF301","nama":"Sistem Terdistribusi","semester":5,"sks":3}]` | **BERHASIL** |
| **8** | Hapus Mahasiswa (Cascade) | `DELETE /mahasiswa/2210001` | *(none)* | **204 No Content** | `(Empty Body)` -> Verifikasi `GET` mengembalikan **404 Not Found** | **BERHASIL** |
| **9** | Ketahanan (Matkul Down) | `POST /mahasiswa/2210002/matkul` | `{"kode_mk":"IF301"}` | **503 Unavailable** | `{"error":"matkul-service tidak dapat dihubungi"}` *(service tidak crash)* | **BERHASIL** |
| **10** | Persistensi Data (Volume) | `GET /mahasiswa/2210002` setelah `docker compose down && up -d` | *(none)* | **200 OK** | `{"nim":"2210002","nama":"Siti","email":null,"angkatan":null}` *(data tetap ada)* | **BERHASIL** |

---

## 6. Kesimpulan

1. Arsitektur Microservice berhasil diwujudkan dengan memisahkan domain data Mahasiswa (MySQL) dan Mata Kuliah (PostgreSQL).
2. Nginx API Gateway berhasil menjalankan perannya sebagai *reverse proxy* dan penyedia antarmuka dashboard terpusat tanpa hambatan CORS.
3. Mekanisme penanganan galat (*fault tolerance*) dan isolasi kegagalan terbukti efektif saat salah satu downstream service dimatikan (menghasilkan status 503 tanpa *system crash*).
4. Persistensi basis data terbukti aman dengan Docker Volumes (`mysql_data` dan `pg_data`).

