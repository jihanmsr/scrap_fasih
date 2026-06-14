"""
Script v5: Mencari petugas pencacah dengan beban kerja > 800 assignment.
Strategi: Loop per kabupaten/kota (4 digit) supaya setiap request kecil
dan tidak memicu server error di page tinggi.

Kabupaten Sulteng (kode 7201-7213):
7201 BANGGAI KEPULAUAN
7202 BANGGAI
7203 MOROWALI
7204 POSO
7205 DONGGALA
7206 TOLI-TOLI
7207 BUOL
7208 PARIGI MOUTONG
7209 TOJO UNA-UNA
7210 SIGI
7211 BANGGAI LAUT
7212 MOROWALI UTARA
7271 KOTA PALU

Output: pencacah_beban_lebih_800_v5.csv
"""

import requests
import json
import csv
import time
from pathlib import Path
from collections import defaultdict

# ── Konfigurasi ─────────────────────────────────────────────────────────────────

SURVEY_PERIOD_ID = "fd68e454-ba45-4b85-8205-f3bf777ded24"
PENCACAH_ROLE_ID = "6d7d919a-45e5-4779-bb87-2905b49fd31a"

BASE_URL = "https://fasih-sm.bps.go.id"
ALLOC_URL = f"{BASE_URL}/app/api/survey-user/api/v1/allocations-view/by-user"

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

OUTPUT_CSV = Path("/Users/jihanmaisaroh/scrap_fasih/pencacah_beban_lebih_800_v5.csv")
CACHE_JSON = Path("/Users/jihanmaisaroh/scrap_fasih/scratch/heavy_v5_all_users.json")

THRESHOLD = 800
PAGE_SIZE = 100  # Kecil agar aman

# Daftar kabupaten/kota Sulawesi Tengah
KABUPATEN = {
    "7201": "BANGGAI KEPULAUAN",
    "7202": "BANGGAI",
    "7203": "MOROWALI",
    "7204": "POSO",
    "7205": "DONGGALA",
    "7206": "TOLI-TOLI",
    "7207": "BUOL",
    "7208": "PARIGI MOUTONG",
    "7209": "TOJO UNA-UNA",
    "7210": "SIGI",
    "7211": "BANGGAI LAUT",
    "7212": "MOROWALI UTARA",
    "7271": "KOTA PALU",
}

# ── Helper ───────────────────────────────────────────────────────────────────────

def parse_cookies(raw):
    c = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            c[k.strip()] = v.strip()
    return c

COOKIES = parse_cookies(COOKIES_RAW)

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": BASE_URL,
    "Referer": BASE_URL + "/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "X-XSRF-TOKEN": XSRF_TOKEN,
}

def fetch_page(session, region_code, page):
    params = {
        "surveyPeriodId": SURVEY_PERIOD_ID,
        "surveyRoleId": PENCACAH_ROLE_ID,
        "page": page,
        "size": PAGE_SIZE,
        "regionCode": region_code,
    }
    for attempt in range(3):
        try:
            resp = session.get(ALLOC_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"    [WARN] {region_code} page={page} attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)
    return None

def fetch_all_for_kab(session, kab_code, kab_name):
    """Ambil semua pencacah untuk satu kabupaten."""
    # Halaman 0 dulu untuk tahu total
    first = fetch_page(session, kab_code, 0)
    if not first:
        print(f"  ❌ Gagal fetch {kab_name} ({kab_code})")
        return []

    data = first.get("data", {})
    total_elements = data.get("totalElements", 0)
    total_pages = data.get("totalPages", 0)
    content = data.get("content", [])

    if total_elements == 0:
        print(f"  {kab_name} ({kab_code}): 0 pencacah")
        return []

    print(f"  {kab_name} ({kab_code}): {total_elements} pencacah, {total_pages} halaman")

    all_users = list(content)
    for page in range(1, total_pages):
        res = fetch_page(session, kab_code, page)
        if not res:
            print(f"    ⚠ Gagal halaman {page}, skip.")
            continue
        content = res.get("data", {}).get("content", [])
        all_users.extend(content)
        time.sleep(0.2)

    return all_users

# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    session = requests.Session()

    # Test koneksi
    print("Testing koneksi API (kab 7201)...")
    test = fetch_page(session, "7201", 0)
    if not test:
        print("❌ Cookie expired atau tidak bisa konek. Update cookie dulu!")
        return
    print(f"✅ OK — totalElements: {test.get('data', {}).get('totalElements', '?')}")

    # ── Loop semua kabupaten ──────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("Mengambil data Pencacah per kabupaten...")
    print(f"{'='*55}")

    # Pakai dict by userId untuk de-duplikasi
    # (satu petugas mungkin muncul di beberapa kabupaten jika dia di-assign lintas kab)
    user_map = {}  # userId -> user dict (with max totalRegions)

    for kab_code, kab_name in KABUPATEN.items():
        users = fetch_all_for_kab(session, kab_code, kab_name)
        for u in users:
            uid = u.get("userId") or u.get("id") or u.get("email", "")
            if not uid:
                continue
            existing = user_map.get(uid)
            total_r = u.get("totalRegions", 0) or 0
            if existing is None or total_r > existing.get("totalRegions", 0):
                u["_kabupaten"] = kab_name
                user_map[uid] = u

    print(f"\n✅ Total petugas unik: {len(user_map):,}")

    # ── Simpan cache ──────────────────────────────────────────────────────────
    with open(CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(list(user_map.values()), f, ensure_ascii=False, indent=2)
    print(f"💾 Cache disimpan: {CACHE_JSON}")

    # ── Inspect struktur ──────────────────────────────────────────────────────
    all_users = list(user_map.values())
    if all_users:
        sample = all_users[0]
        print("\n--- Struktur user (sample) ---")
        for k, v in sample.items():
            print(f"  {k}: {str(v)[:100]}")
        print("---")

    # ── Analisis & filter ─────────────────────────────────────────────────────
    results = []
    for u in all_users:
        total_regions = u.get("totalRegions", 0) or 0
        email    = u.get("email", "")
        username = u.get("username", "")
        name     = u.get("name", "") or u.get("fullName", "") or username
        user_id  = u.get("userId", "") or u.get("id", "")
        kab      = u.get("_kabupaten", "")

        results.append({
            "userId": user_id,
            "email": email,
            "username": username,
            "name": name,
            "kabupaten": kab,
            "totalRegions": total_regions,
        })

    # Statistik
    all_counts = [r["totalRegions"] for r in results]
    if all_counts:
        print(f"\nStatistik beban kerja Pencacah (totalRegions):")
        print(f"  Total petugas unik : {len(all_counts):,}")
        print(f"  Min                : {min(all_counts):,}")
        print(f"  Max                : {max(all_counts):,}")
        print(f"  Rata-rata          : {sum(all_counts)/len(all_counts):.1f}")
        print(f"  Beban 0            : {sum(1 for x in all_counts if x == 0)}")
        print(f"  Beban 1-500        : {sum(1 for x in all_counts if 0 < x <= 500)}")
        print(f"  Beban 501-800      : {sum(1 for x in all_counts if 500 < x <= 800)}")
        print(f"  Beban > {THRESHOLD}       : {sum(1 for x in all_counts if x > THRESHOLD)}")

    # Filter
    heavy = [r for r in results if r["totalRegions"] > THRESHOLD]
    heavy.sort(key=lambda x: x["totalRegions"], reverse=True)

    print(f"\n{'='*55}")
    print(f"HASIL: {len(heavy)} Pencacah dengan beban > {THRESHOLD}")
    print(f"{'='*55}")
    for i, r in enumerate(heavy[:30], 1):
        print(f"  {i:3d}. {r['email']:<50s} | {r['totalRegions']:>5,} | {r['kabupaten']}")

    # ── Tulis CSV ─────────────────────────────────────────────────────────────
    output_data = heavy if heavy else sorted(results, key=lambda x: x["totalRegions"], reverse=True)
    label = f"> {THRESHOLD}" if heavy else "semua (diurutkan)"

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["No", "email", "username", "name", "userId", "kabupaten", "jumlah_assignment"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(output_data, 1):
            writer.writerow({
                "No": i,
                "email": r["email"],
                "username": r["username"],
                "name": r["name"],
                "userId": r["userId"],
                "kabupaten": r["kabupaten"],
                "jumlah_assignment": r["totalRegions"],
            })

    print(f"\n✅ CSV ({label}) tersimpan: {OUTPUT_CSV}")
    print(f"   Total baris: {len(output_data)}")

if __name__ == "__main__":
    main()
