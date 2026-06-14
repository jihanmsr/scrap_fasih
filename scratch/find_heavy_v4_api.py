"""
Script v4: Mencari petugas pencacah dengan beban kerja > 800 assignment.
Menggunakan endpoint: /app/api/survey-user/api/v1/allocations-view/by-user
Satu "assignment" = satu wilayah (totalRegions) yang di-assign ke petugas.

Untuk beban > 800 unit listing keluarga, perlu endpoint datatable dengan filter per-user,
tapi di sini kita pakai totalRegions sebagai proksi beban kerja dulu.

Output: pencacah_beban_lebih_800_v4.csv
"""

import requests
import json
import csv
import time
from pathlib import Path
from urllib.parse import unquote

# ── Konfigurasi ─────────────────────────────────────────────────────────────────

SURVEY_PERIOD_ID = "fd68e454-ba45-4b85-8205-f3bf777ded24"

# Role IDs dari script sebelumnya
PENCACAH_ROLE_ID  = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
PENGAWAS_ROLE_ID  = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"

BASE_URL = "https://fasih-sm.bps.go.id"
ALLOC_URL = f"{BASE_URL}/app/api/survey-user/api/v1/allocations-view/by-user"

# Cookie dari curl user (update jika expired)
COOKIES_RAW = (
    "f5avraaaaaaaaaaaaaaaa_session_=AGPNJMOLNCLGCOPGNLMOLCMIPMONNKDKCPIIENOCOJABCBNNIFGCFIBOFJNEGLMAMKIDFCLENADONPINMFEANPDFLNIHFLPKADFFCDJPICNGNEHLIEJCCFBNBGMJPDEJ; "
    "f5_cspm=1234; "
    "f5avraaaaaaaaaaaaaaaa_session_=LJFAKDEIMBNEGIIJFFKGCFFDOHEALJLCLKBIMBIKBEABLPFGIICPIGLIGDBOCOOMHMADLDDAIAEKLDDNOKJAMKFOLNONJFCJJEHOFFCKKBIBLOKDABBFFOOONFPENMON; "
    "_ga=GA1.3.1140734912.1781239400; "
    "XSRF-TOKEN=2aa4543c-db0f-40f3-904c-6ea9c5b907bf; "
    "TS01acc472=01266d26d0131ad4d90a313d8b4e41273a43d8c32b957febe1203f3abb0bef61a21ab7411f72b1c695f3b8577e43ef03d6e8c1d1b7b641b61c14d25448557d7e1657062950e253e23d8fce79b39befd9435f7f493c8dfe98811b565fc218fa383177313677546797685a7fe67f708d5cc19a9d71ad87780e730d180fa8c251913d14b94ee77e1258dcb38c586e0a08591932a4942bcd199a53ee3d080d812d400ef95ddbe973901ca80e52b1c96ab755ed1e21e8bf5b86bb2d01098234e8c01d368d63002f61eaaf257981a24d007d5f717195a0aa; "
    "TS0151fc2b=0167a1c8617a278160e553d265d03646ab0c79bf314f941fae1bf01a505d89745d3dd22519ac889ac5c36aca04e3fe73949a4882e4; "
    "f5avr1146915014aaaaaaaaaaaaaaaa_cspm_=LEJDJNLODGMBMKHFOFMGHPBLPJOIOHHFDDPFCJAPKJFLKJPNOKEHIKNHKKIPMDNKJIMCNJEPAEAMJOBLKKPAKDNBAHKBLCHKAPFLELHEODHIMGKCDINOCAFKJDIGGGEK; "
    "db8ca2b43ed851cc93e71fd5fd72bff7=d45a11eb518a297a8141c49942c33d62; "
    "JSESSIONID=CA227D5C3BA8FDE09C856D04F48EF6F8; "
    "_ga_XXTTVXWHDB=GS2.3.s1781307346$o2$g0$t1781307346$j60$l0$h0; "
    "f5avraaaaaaaaaaaaaaaa_session_=CJOFBMJPHMINOIODOFAAJJEDBMAHPPFNJEMLMBBAPIDBPINHBKHNIJLPIGBAJKMKPMKDBIEHKHBDBIKCBCNADBANIJIPHDKGFFFODDLBCIFIEFKCNJAPHLKEIMHLFMIK; "
    "SESSION=b1ff4eaa-6688-42a7-a425-840eadd69b8e; "
    "TS01bafd94=01266d26d0809775dd819de1f0de9ac4d23d16635baf848eb73b1d845c9d58e54b3450f960e1fcd24652119248ebaeb832fdb81781; "
    "f5avr1980069168aaaaaaaaaaaaaaaa_cspm_=GLKDLKAAPIENAEMODAJPOBCMPAIIINJHLHKDCEEBMKFIPPHAMPFPKIBKHEJGHCHLOBOCDBGCCLAHGIHPFBEACLBAMEJHDEPAKOFHLMAMOKMNKDGMDFGONJIOGIFOLNDC; "
    "TS5d9b593f027=0868f8be6fab2000c1f116a745a8585f55d5dfab4cae919f6702baa9c8af826eda9b3d2f55294f1808078de68c11300047fd916f549826fce83fa258a0dda217a90d8d34e21d58c8e3aa88b3fd835ac24186fd47c765ae7d3f1f771c755bcfd2"
)
XSRF_TOKEN = "2aa4543c-db0f-40f3-904c-6ea9c5b907bf"

OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800_v4.csv")

# Kode wilayah Sulawesi Tengah = "72"
# Kalau mau semua provinsi, hapus regionCode atau pakai "72"
REGION_CODE = "72"

THRESHOLD = 800

# ── Helper ───────────────────────────────────────────────────────────────────────

def parse_cookies(raw: str) -> dict:
    cookies = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

COOKIES = parse_cookies(COOKIES_RAW)

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "Connection": "keep-alive",
    "Origin": BASE_URL,
    "Referer": BASE_URL + "/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "X-XSRF-TOKEN": XSRF_TOKEN,
}

def fetch_users_page(session, role_id, page, size=200):
    params = {
        "surveyPeriodId": SURVEY_PERIOD_ID,
        "surveyRoleId": role_id,
        "page": page,
        "size": size,
        "regionCode": REGION_CODE,
    }
    for attempt in range(3):
        try:
            resp = session.get(ALLOC_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  [WARN] page={page} attempt {attempt+1}/3: {e}")
            time.sleep(2)
    return None

def fetch_all_users(session, role_id, role_name):
    """Ambil semua user untuk role tertentu dengan paginasi."""
    print(f"\n{'='*55}")
    print(f"Mengambil data {role_name}...")
    print(f"{'='*55}")

    # Halaman pertama untuk tahu total
    first = fetch_users_page(session, role_id, page=0, size=1)
    if not first:
        print(f"❌ Gagal mengambil data {role_name}")
        return []

    data = first.get("data", {})
    total_elements = data.get("totalElements", 0)
    total_pages = data.get("totalPages", 0)
    print(f"  Total {role_name}: {total_elements:,} user ({total_pages} halaman)")

    if total_elements == 0:
        return []

    page_size = 200
    all_users = []
    for page in range(total_pages):
        result = fetch_users_page(session, role_id, page=page, size=page_size)
        if not result:
            print(f"  ❌ Gagal halaman {page}, skip.")
            continue
        content = result.get("data", {}).get("content", [])
        all_users.extend(content)
        pct = (page + 1) / total_pages * 100
        print(f"  [{pct:5.1f}%] Halaman {page+1}/{total_pages}: +{len(content)} user (total: {len(all_users)})")
        time.sleep(0.15)

    return all_users

# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    session = requests.Session()

    # Test koneksi
    print("Testing koneksi API...")
    test = fetch_users_page(session, PENCACAH_ROLE_ID, page=0, size=1)
    if not test:
        print("❌ Gagal terhubung ke API. Kemungkinan cookie sudah expired.")
        print("   Silakan perbarui cookie dari browser dan jalankan ulang script.")
        return

    resp_data = test.get("data", {})
    print(f"✅ Koneksi berhasil. Response keys: {list(test.keys())}")
    print(f"   data keys: {list(resp_data.keys())}")

    # ── Ambil semua Pencacah ──────────────────────────────────────────────────
    pencacah_users = fetch_all_users(session, PENCACAH_ROLE_ID, "Pencacah")
    print(f"\n✅ Total Pencacah terkumpul: {len(pencacah_users):,}")

    # ── Inspect satu user ──────────────────────────────────────────────────────
    if pencacah_users:
        sample = pencacah_users[0]
        print("\n--- Struktur user pertama ---")
        for k, v in sample.items():
            val_str = str(v)[:100]
            print(f"  {k}: {val_str}")
        print("---")

    # ── Analisis beban kerja ──────────────────────────────────────────────────
    print("\nMenganalisis beban kerja Pencacah...")

    results = []
    for u in pencacah_users:
        total_regions = u.get("totalRegions", 0) or 0
        email = u.get("email", "")
        username = u.get("username", "")
        name = u.get("name", "") or u.get("fullName", "") or username
        user_id = u.get("userId", "") or u.get("id", "")

        # Cari kabupaten dari regions[0] jika ada
        regions = u.get("regions", [])
        kab = ""
        if regions:
            r0 = regions[0]
            # Biasanya ada regionCode atau nama
            kab = r0.get("kabupaten", "") or r0.get("regionCode", "")[:6] if r0 else ""

        results.append({
            "userId": user_id,
            "email": email,
            "username": username,
            "name": name,
            "totalRegions": total_regions,
            "kabupaten_sample": kab,
        })

    # Statistik
    if results:
        all_regions = [r["totalRegions"] for r in results]
        print(f"\nStatistik beban kerja (totalRegions = jumlah SLS/unit assignment):")
        print(f"  Total Pencacah       : {len(results):,}")
        print(f"  Min                  : {min(all_regions):,}")
        print(f"  Max                  : {max(all_regions):,}")
        print(f"  Rata-rata            : {sum(all_regions)/len(all_regions):.1f}")
        print(f"  Beban 0              : {sum(1 for x in all_regions if x == 0)}")
        print(f"  Beban 1-500          : {sum(1 for x in all_regions if 0 < x <= 500)}")
        print(f"  Beban 501-800        : {sum(1 for x in all_regions if 500 < x <= 800)}")
        print(f"  Beban > {THRESHOLD}         : {sum(1 for x in all_regions if x > THRESHOLD)}")

    # ── Filter > THRESHOLD ────────────────────────────────────────────────────
    heavy = [r for r in results if r["totalRegions"] > THRESHOLD]
    heavy.sort(key=lambda x: x["totalRegions"], reverse=True)

    print(f"\n{'='*55}")
    print(f"HASIL: {len(heavy)} Pencacah dengan beban > {THRESHOLD} assignment")
    print(f"{'='*55}")

    if heavy:
        for i, r in enumerate(heavy[:30], 1):
            print(f"  {i:3d}. {r['email']:<50s} | {r['totalRegions']:>5,} regions")

    # ── Tulis CSV ──────────────────────────────────────────────────────────────
    if heavy:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["No", "email", "username", "name", "userId", "jumlah_assignment"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, r in enumerate(heavy, 1):
                writer.writerow({
                    "No": i,
                    "email": r["email"],
                    "username": r["username"],
                    "name": r["name"],
                    "userId": r["userId"],
                    "jumlah_assignment": r["totalRegions"],
                })
        print(f"\n✅ CSV tersimpan: {OUTPUT_CSV}")
    else:
        print(f"\n⚠️  Tidak ada petugas dengan beban > {THRESHOLD}.")
        # Tulis semua petugas tetap, diurutkan dari terbesar
        all_sorted = sorted(results, key=lambda x: x["totalRegions"], reverse=True)
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["No", "email", "username", "name", "userId", "jumlah_assignment"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, r in enumerate(all_sorted, 1):
                writer.writerow({
                    "No": i,
                    "email": r["email"],
                    "username": r["username"],
                    "name": r["name"],
                    "userId": r["userId"],
                    "jumlah_assignment": r["totalRegions"],
                })
        print(f"   Semua petugas (diurutkan terbesar) ditulis ke: {OUTPUT_CSV}")

    # ── Dump sample ───────────────────────────────────────────────────────────
    if pencacah_users:
        debug_path = Path("/Users/jihanmaisaroh/scrap_fasih/scratch/heavy_v4_debug.json")
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(pencacah_users[:3], f, ensure_ascii=False, indent=2)
        print(f"📄 Sample user tersimpan: {debug_path}")


if __name__ == "__main__":
    main()
