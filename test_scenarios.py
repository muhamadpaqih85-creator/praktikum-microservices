#!/usr/bin/env python3
"""
Script Pengujian Otomatis Seluruh Skenario (1 - 10)
Sistem Terdistribusi - Praktikum Microservice
"""

import subprocess
import time
import requests

GATEWAY_URL = "http://localhost:8080"

def banner(title):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)

def wait_for_services():
    print("Menunggu semua layanan di API Gateway siap...")
    for i in range(45):
        try:
            r1 = requests.get(f"{GATEWAY_URL}/mahasiswa", timeout=2)
            r2 = requests.get(f"{GATEWAY_URL}/matkul", timeout=2)
            if r1.status_code == 200 and r2.status_code == 200:
                print("Semua layanan siap dan merespons normal!")
                return True
        except Exception:
            pass
        time.sleep(2)
        print(f"  Percobaan {i+1}: menunggu inisialisasi database & service...")
    return False

def run_scenario_1():
    banner("Skenario 1: Tambah Mahasiswa")
    payload = {"nim": "2210001", "nama": "Budi", "email": "budi@mail.com", "angkatan": 2022}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 201)")
    print(f"Response: {r.text}")
    assert r.status_code == 201, f"Gagal, diharapkan 201 tetapi dapat {r.status_code}"
    print("Hasil Skenario 1: BERHASIL (PASS)")

def run_scenario_2():
    banner("Skenario 2: NIM Duplikat")
    payload = {"nim": "2210001", "nama": "Budi Duplikat"}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 409)")
    print(f"Response: {r.text}")
    assert r.status_code == 409, f"Gagal, diharapkan 409 tetapi dapat {r.status_code}"
    print("Hasil Skenario 2: BERHASIL (PASS)")

def run_scenario_3():
    banner("Skenario 3: Tambah Mata Kuliah")
    payload = {"kode": "IF304", "nama": "Kecerdasan Buatan", "sks": 3, "semester": 5}
    r = requests.post(f"{GATEWAY_URL}/matkul", json=payload)
    print(f"Request: POST {GATEWAY_URL}/matkul -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 201)")
    print(f"Response: {r.text}")
    assert r.status_code == 201, f"Gagal, diharapkan 201 tetapi dapat {r.status_code}"
    print("Hasil Skenario 3: BERHASIL (PASS)")

def run_scenario_4():
    banner("Skenario 4: Ambil Mata Kuliah (KRS)")
    payload = {"kode_mk": "IF301"}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa/2210001/matkul", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa/2210001/matkul -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 201)")
    print(f"Response: {r.text}")
    assert r.status_code == 201, f"Gagal, diharapkan 201 tetapi dapat {r.status_code}"
    print("Hasil Skenario 4: BERHASIL (PASS)")

def run_scenario_5():
    banner("Skenario 5: Ambil Mata Kuliah Tidak Ada")
    payload = {"kode_mk": "XX999"}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa/2210001/matkul", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa/2210001/matkul -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 404)")
    print(f"Response: {r.text}")
    assert r.status_code == 404, f"Gagal, diharapkan 404 tetapi dapat {r.status_code}"
    print("Hasil Skenario 5: BERHASIL (PASS)")

def run_scenario_6():
    banner("Skenario 6: Ambil Mata Kuliah Dua Kali (Duplikat KRS)")
    payload = {"kode_mk": "IF301"}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa/2210001/matkul", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa/2210001/matkul -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 409)")
    print(f"Response: {r.text}")
    assert r.status_code == 409, f"Gagal, diharapkan 409 tetapi dapat {r.status_code}"
    print("Hasil Skenario 6: BERHASIL (PASS)")

def run_scenario_7():
    banner("Skenario 7: Lihat KRS Mahasiswa")
    r = requests.get(f"{GATEWAY_URL}/mahasiswa/2210001/matkul")
    print(f"Request: GET {GATEWAY_URL}/mahasiswa/2210001/matkul")
    print(f"Status: {r.status_code} (Harapan: 200)")
    print(f"Response: {r.text}")
    assert r.status_code == 200, f"Gagal, diharapkan 200 tetapi dapat {r.status_code}"
    data = r.json()
    assert len(data) >= 1 and data[0].get("kode_mk") == "IF301", "Data KRS tidak cocok"
    print("Hasil Skenario 7: BERHASIL (PASS)")

def run_scenario_8():
    banner("Skenario 8: Hapus Mahasiswa (Cascade KRS)")
    r = requests.delete(f"{GATEWAY_URL}/mahasiswa/2210001")
    print(f"Request: DELETE {GATEWAY_URL}/mahasiswa/2210001")
    print(f"Status: {r.status_code} (Harapan: 204)")
    assert r.status_code == 204, f"Gagal, diharapkan 204 tetapi dapat {r.status_code}"

    # Verifikasi mahasiswa sudah terhapus
    r_check = requests.get(f"{GATEWAY_URL}/mahasiswa/2210001")
    print(f"Verifikasi Mahasiswa: GET {GATEWAY_URL}/mahasiswa/2210001 -> Status {r_check.status_code} (Harapan: 404)")
    assert r_check.status_code == 404, "Mahasiswa masih ada!"
    print("Hasil Skenario 8: BERHASIL (PASS)")

def run_scenario_9():
    banner("Skenario 9: Ketahanan Sistem (Matkul Service Dimatikan)")
    # Siapkan mahasiswa baru terlebih dahulu
    requests.post(f"{GATEWAY_URL}/mahasiswa", json={"nim": "2210002", "nama": "Siti"})
    
    print("Menghentikan container matkul-service...")
    subprocess.run(["docker", "compose", "stop", "matkul-service"], check=True)
    time.sleep(2)

    payload = {"kode_mk": "IF301"}
    r = requests.post(f"{GATEWAY_URL}/mahasiswa/2210002/matkul", json=payload)
    print(f"Request: POST {GATEWAY_URL}/mahasiswa/2210002/matkul -> Body: {payload}")
    print(f"Status: {r.status_code} (Harapan: 503)")
    print(f"Response: {r.text}")
    assert r.status_code == 503, f"Gagal, diharapkan 503 tetapi dapat {r.status_code}"

    print("Menghidupkan kembali container matkul-service...")
    subprocess.run(["docker", "compose", "start", "matkul-service"], check=True)
    time.sleep(3)
    print("Hasil Skenario 9: BERHASIL (PASS)")

def run_scenario_10():
    banner("Skenario 10: Persistensi Data (Restart Stack tanpa -v)")
    # Pastikan data ada sebelum restart
    r_mhs = requests.get(f"{GATEWAY_URL}/mahasiswa/2210002")
    assert r_mhs.status_code == 200, "Data mahasiswa 2210002 harus ada sebelum restart"

    print("Menjalankan docker compose down (tanpa -v)...")
    subprocess.run(["docker", "compose", "down"], check=True)
    time.sleep(2)

    print("Menjalankan docker compose up -d...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    time.sleep(5)

    if not wait_for_services():
        raise RuntimeError("Service tidak pulih setelah restart")

    r_mhs_after = requests.get(f"{GATEWAY_URL}/mahasiswa/2210002")
    print(f"Verifikasi Mahasiswa: GET {GATEWAY_URL}/mahasiswa/2210002 -> Status {r_mhs_after.status_code}")
    print(f"Response: {r_mhs_after.text}")
    assert r_mhs_after.status_code == 200, "Data mahasiswa hilang setelah restart!"
    print("Hasil Skenario 10: BERHASIL (PASS)")

if __name__ == "__main__":
    if not wait_for_services():
        print("Error: Layanan belum aktif.")
        exit(1)

    try:
        run_scenario_1()
        run_scenario_2()
        run_scenario_3()
        run_scenario_4()
        run_scenario_5()
        run_scenario_6()
        run_scenario_7()
        run_scenario_8()
        run_scenario_9()
        run_scenario_10()
        print("\n" + "=" * 65)
        print(" SEMUA SKENARIO (1-10) TELAH BERHASIL DIUJI DENGAN SUKSES!")
        print("=" * 65)
    except Exception as e:
        print(f"\n[ERROR] Pengujian gagal: {e}")
        exit(1)
