import asyncio
import os
import sys

# Pastikan directory root masuk dalam sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

from scrape_sync import scrape_sync_data
from generate_ipas_report import generate_report
from scrape_via_api import scrape_via_api
from scrape_granular_assignments import scrape_all_granular

async def run_all():
    print("=========================================")
    print("   MEMULAI PROSES UPDATE DATA SEKALIKUS  ")
    print("=========================================\n")

    # 1. Tarik Data Sync Superset
    print("[1/4] Menarik data sinkronisasi Superset...")
    try:
        await scrape_sync_data()
        print("-> Sukses menarik data sync Superset.\n")
    except Exception as e:
        print(f"-> [ERROR] Gagal menarik data sync: {e}\n")

    # 2. Generate Laporan Utama IPAS (Dashboard SE Umum/UB & Progres Harian)
    print("[2/4] Menghasilkan laporan utama dashboard & statistik harian...")
    try:
        await generate_report()
        print("-> Sukses memperbarui data IPAS dashboard & progres harian.\n")
    except Exception as e:
        print(f"-> [ERROR] Gagal memperbarui data IPAS: {e}\n")

    # 3. Scrape Email UB (Bounced History)
    print("[3/4] Menarik status pengiriman email Usaha Besar (UB)...")
    try:
        # scrape_via_api adalah fungsi sinkron (synchronous)
        scrape_via_api()
        print("-> Sukses memperbarui riwayat email bounce UB.\n")
    except Exception as e:
        print(f"-> [ERROR] Gagal menarik email UB: {e}\n")

    # 4. Scrape Granular Assignments (Status Target per SLS)
    print("[4/4] Menarik rincian target granular tingkat SLS...")
    try:
        await scrape_all_granular()
        print("-> Sukses memperbarui rincian target granular SLS.\n")
    except Exception as e:
        print(f"-> [ERROR] Gagal menarik target granular: {e}\n")

    print("=========================================")
    print("     PROSES UPDATE SELESAI DENGAN SUKSES ")
    print("=========================================")

if __name__ == "__main__":
    asyncio.run(run_all())
