# praktikum-microservices

Sistem Terdistribusi - Program Studi S1 Informatika

Sistem akademik sederhana berbasis arsitektur microservice dengan Python (Flask), MySQL, PostgreSQL, dan Nginx API Gateway.

## Arsitektur Sistem

```text
                    +----------------------+
   Browser/curl --> |  Nginx API Gateway   |  :8080
                    |  + Dashboard (/)     |
                    +----------+-----------+
                 /mahasiswa    |    /matkul
              +----------------+----------------+
              v                                 v
   +---------------------+   HTTP GET   +---------------------+
   | Mahasiswa Service   | -----------> | Matkul Service      |
   | Flask :5000         | /matkul/{kd} | Flask :5000         |
   +----------+----------+              +----------+----------+
              v                                    v
        MySQL (mahasiswa_db)             PostgreSQL (matkul_db)
```

## Pembagian Peran
- **Peserta A**: Service Mahasiswa (Python Flask + MySQL), folder `mahasiswa-service/`
- **Peserta B**: Service Mata Kuliah (Python Flask + PostgreSQL), folder `matkul-service/`
- **Peserta C**: API Gateway (Nginx), Web Dashboard, Docker Compose, folder `gateway/` & `docker-compose.yml`

## Kontrak API

Semua request dan response berformat JSON (`Content-Type: application/json`).

### Mahasiswa Service (`/mahasiswa`)
| Method | Path | Keterangan | Status Sukses |
|---|---|---|---|
| GET | `/mahasiswa` | Daftar semua mahasiswa | 200 |
| POST | `/mahasiswa` | Tambah mahasiswa (`nim`, `nama`, `email`, `angkatan`) | 201 |
| GET | `/mahasiswa/{nim}` | Detail satu mahasiswa | 200 |
| PUT | `/mahasiswa/{nim}` | Ubah data mahasiswa | 200 |
| DELETE | `/mahasiswa/{nim}` | Hapus mahasiswa beserta KRS-nya | 204 |
| GET | `/mahasiswa/{nim}/matkul` | Daftar matkul yang diambil (dengan detail) | 200 |
| POST | `/mahasiswa/{nim}/matkul` | Ambil matkul (`kode_mk`) | 201 |
| DELETE | `/mahasiswa/{nim}/matkul/{kode_mk}` | Batalkan pengambilan matkul | 204 |

### Matkul Service (`/matkul`)
| Method | Path | Keterangan | Status Sukses |
|---|---|---|---|
| GET | `/matkul` | Daftar semua mata kuliah | 200 |
| POST | `/matkul` | Tambah mata kuliah (`kode`, `nama`, `sks`, `semester`) | 201 |
| GET | `/matkul/{kode}` | Detail satu mata kuliah | 200 |
| PUT | `/matkul/{kode}` | Ubah data mata kuliah | 200 |
| DELETE | `/matkul/{kode}` | Hapus mata kuliah | 204 |

## Cara Menjalankan Sistem

1. Pastikan Docker Desktop sudah aktif.
2. Masuk ke direktori:
   ```bash
   cd praktikum-microservice
   ```
3. Jalankan container dengan Docker Compose:
   ```bash
   docker compose up --build
   ```
4. Buka browser:
   - Dashboard Web: [http://localhost:8080](http://localhost:8080)
   - API Mahasiswa: [http://localhost:8080/mahasiswa](http://localhost:8080/mahasiswa)
   - API Mata Kuliah: [http://localhost:8080/matkul](http://localhost:8080/matkul)
