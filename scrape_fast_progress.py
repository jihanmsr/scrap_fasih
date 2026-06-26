import asyncio
import json
import os
import sys
import time
import base64
import gzip
import datetime
import socket
import subprocess
import shutil
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from urllib.parse import unquote

# Import get_authenticated_context and check_session_valid from core
from scrape_granular_core import get_authenticated_context, check_session_valid

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY and "MASUKKAN" not in SUPABASE_URL:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[INFO] Koneksi Supabase berhasil diinisialisasi untuk scrape_fast_progress.")
    except Exception as e:
        print(f"[ERROR] Gagal menginisialisasi Supabase: {e}")

# Survey and Role configurations
SE_UMUM_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24"
SE_UB_PERIOD = "37526b20-81c8-42f5-a895-6190137d7394"

ROLE_PENCACAH_UMUM = "6d7d919a-45e5-4779-bb87-2905b49fd31a"
ROLE_PENGAWAS_UMUM = "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"

ROLE_PENCACAH_UB = "90f9a76b-1888-4589-b681-d6eb6bfdbb2d"
ROLE_PENGAWAS_UB = "7bcf696d-9c0e-4e1a-b58f-eacc79bfb499"

KAB_NAMES = {
    "7201": "[01] BANGGAI KEPULAUAN",
    "7202": "[02] BANGGAI",
    "7203": "[03] MOROWALI",
    "7204": "[04] POSO",
    "7205": "[05] DONGGALA",
    "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL",
    "7208": "[08] PARIGI MOUTONG",
    "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI",
    "7211": "[11] BANGGAI LAUT",
    "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

def categorize_status(status_str, count):
    status_upper = status_str.upper()
    draft = 0
    open_cnt = 0
    sub_pencacah = 0
    sub_respondent = 0
    submitted = 0
    rejected = 0
    approved = 0

    if status_upper == "DRAFT":
        draft = count
    elif status_upper == "OPEN":
        open_cnt = count
    elif "SUBMITTED" in status_upper:
        if "RESPONDENT" in status_upper:
            sub_respondent = count
        else:
            sub_pencacah = count
        submitted = count
    elif "REJECTED" in status_upper or "REVOKED" in status_upper:
        rejected = count
        submitted = count
    elif "APPROVED" in status_upper:
        approved = count
        submitted = count
    else:
        open_cnt = count

    return {
        "draft": draft,
        "open": open_cnt,
        "submitted_pencacah": sub_pencacah,
        "submitted_respondent": sub_respondent,
        "submitted": submitted,
        "rejected": rejected,
        "approved": approved
    }

async def fetch_users_mapping(page, token, period_id):
    print(f"[INFO] Menarik data alokasi petugas untuk periode {period_id}...")
    users = []
    page_idx = 0
    size = 1000
    while True:
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={period_id}&page={page_idx}&size={size}"
        resp = await fetch_api_safely(page, url, None, token, method="GET")
        
        # Get the fresh token in case it was refreshed during fetch_api_safely
        token = await get_xsrf_token(page) or token
        
        if not resp or not resp.get("success"):
            print(f"[ERROR] API allocations page {page_idx} gagal atau success=false: {resp.get('error') if resp else 'No response'}")
            return None
            
        content = resp.get("data", {}).get("content", [])
        if not content:
            break
        users.extend(content)
        total_pages = resp.get("data", {}).get("totalPages", 1)
        if page_idx >= total_pages - 1:
            break
        page_idx += 1
    print(f" ✅ Berhasil menarik {len(users)} alokasi petugas.")
    return users

def merge_user_records(records):
    merged = {}
    for r in records:
        uid = r.get("id") or r.get("userId")
        if not uid:
            continue
        if uid not in merged:
            merged[uid] = r
        else:
            # Gabungkan region
            old_regs = merged[uid].get("regions") or []
            new_regs = r.get("regions") or []
            seen_regs = {x.get("id") for x in old_regs if x.get("id")}
            for nr in new_regs:
                if nr.get("id") not in seen_regs:
                    old_regs.append(nr)
            merged[uid]["regions"] = old_regs
    return list(merged.values())

# Kab IDs per survey (dari surveys config di run_ipas_report_generation)
SURVEY_KAB_IDS = {
    "fd68e454-ba45-4b85-8205-f3bf777ded24": {  # SE Umum
        "province_id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "kabs": [
            ("7201", "[01] BANGGAI KEPULAUAN", "bc32354f-1245-426f-b2cf-a5733e1295ad"),
            ("7202", "[02] BANGGAI",            "530e9ca5-86ba-434e-9b04-405102e6d900"),
            ("7203", "[03] MOROWALI",           "9783f0c1-f047-477f-8840-11eae7cf70e2"),
            ("7204", "[04] POSO",               "fb9cd9f0-c4c0-4a37-9041-57190693f625"),
            ("7205", "[05] DONGGALA",           "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"),
            ("7206", "[06] TOLI-TOLI",          "d833fdce-ebfb-429b-a1bb-8966239fd8e4"),
            ("7207", "[07] BUOL",               "c523694a-2e72-4570-9489-da2d7b119fe7"),
            ("7208", "[08] PARIGI MOUTONG",     "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"),
            ("7209", "[09] TOJO UNA-UNA",       "736c4c22-51d1-44be-8b2c-aa197d9459a4"),
            ("7210", "[10] SIGI",               "0061da62-2a47-4dee-b8d0-239b33e2c59d"),
            ("7211", "[11] BANGGAI LAUT",       "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"),
            ("7212", "[12] MOROWALI UTARA",     "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"),
            ("7271", "[71] PALU",               "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"),
        ]
    },
    "37526b20-81c8-42f5-a895-6190137d7394": {  # SE UB
        "province_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
        "kabs": [
            ("7201", "[01] BANGGAI KEPULAUAN", "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb"),
            ("7202", "[02] BANGGAI",            "34165dd5-372e-42fa-99c6-0cc19a9b4d0b"),
            ("7203", "[03] MOROWALI",           "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424"),
            ("7204", "[04] POSO",               "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22"),
            ("7205", "[05] DONGGALA",           "c075c4b4-7eb0-4d72-9c16-5103088fb5eb"),
            ("7206", "[06] TOLI-TOLI",          "d3a28bfa-b611-488b-8255-369da5cedbf7"),
            ("7207", "[07] BUOL",               "dfe4c643-3282-40db-a5fd-cb288a4f592d"),
            ("7208", "[08] PARIGI MOUTONG",     "f18109d2-fc8b-4b9c-886a-dc242d21206e"),
            ("7209", "[09] TOJO UNA-UNA",       "4d01eba1-5ae9-4603-82a6-2c831aea9905"),
            ("7210", "[10] SIGI",               "2a240d3a-67ee-45b2-ae78-4b4b3a909a90"),
            ("7211", "[11] BANGGAI LAUT",       "288c5680-f6d5-4783-a946-d5a06f547c02"),
            ("7212", "[12] MOROWALI UTARA",     "a5324f17-7a00-436f-b468-2fc59fcf605d"),
            ("7271", "[71] PALU",               "1acfedb4-276e-44d6-9e45-6d43588536d6"),
        ]
    },
}

async def fetch_responsibility_report(page, token, survey_period_id, role_id, target_type):
    """
    Menarik data progres per-petugas dari report-progress-by-responsibility.
    Menggunakan payload format yang benar: {page, size, surveyPeriodId, surveyRoleId, target, region{}, regionSummaryLevel}
    """
    # Ambil province_id dan kab list yang sesuai untuk survey ini
    survey_cfg = SURVEY_KAB_IDS.get(survey_period_id, {})
    PROVINCE_ID = survey_cfg.get("province_id", "5214ecb2-bef1-4a86-9446-451cf430928e")
    kab_id_list = survey_cfg.get("kabs", [])

    report_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
    print(f"[INFO] Menarik data responsibility (payload benar) untuk periode={survey_period_id}, role={role_id}...")

    all_flat_rows = []

    def make_region(kab_id=None, kec_id=None):
        return {
            "region1Id": PROVINCE_ID,
            "region2Id": kab_id,
            "region3Id": kec_id,
            "region4Id": None, "region5Id": None, "region6Id": None,
            "region7Id": None, "region8Id": None, "region9Id": None, "region10Id": None
        }

    _debug_printed = [False]  # print sekali saja

    def flatten_content(content):
        """
        Ubah list content (per-user) dari API menjadi flat rows.
        Field names dicoba dengan fallback: targetCount/target, syncCount, dll.
        """
        rows = []
        for user in content:
            username = user.get("username") or ""
            fullname = user.get("fullName") or user.get("fullname") or username
            regions = user.get("regionSummary") or []

            # Debug print satu kali untuk lihat struktur asli API
            if not _debug_printed[0] and regions:
                import json as _json
                print(f"   [DEBUG] regionSummary[0] keys: {list(regions[0].keys())}")
                print(f"   [DEBUG] regionSummary[0] sample: {_json.dumps(regions[0], ensure_ascii=False)[:300]}")
                _debug_printed[0] = True
            elif not _debug_printed[0] and not regions:
                # user tanpa regionSummary - print user keys
                print(f"   [DEBUG] user keys (no regionSummary): {list(user.keys())}")
                for k, v in user.items():
                    if not isinstance(v, (list, dict)):
                        print(f"     {k}: {v}")
                _debug_printed[0] = True

            for reg in regions:
                region_code = (reg.get("regionCode") or reg.get("region5Id")
                               or reg.get("id") or reg.get("code") or reg.get("slsCode"))
                if not region_code:
                    continue

                # Coba semua kemungkinan field names untuk tiap count
                target   = (reg.get("targetCount") or reg.get("target") or
                            reg.get("totalTarget") or reg.get("total") or 0)
                submitted = (reg.get("submittedCount") or reg.get("submitted") or
                             reg.get("totalSubmitted") or reg.get("syncCount") or 0)
                approved  = (reg.get("approvedCount") or reg.get("approved") or
                             reg.get("totalApproved") or 0)
                rejected  = (reg.get("rejectedCount") or reg.get("rejected") or
                             reg.get("totalRejected") or reg.get("revokedCount") or 0)
                draft     = (reg.get("draftCount") or reg.get("draft") or
                             reg.get("totalDraft") or 0)
                open_cnt  = (reg.get("openCount") or reg.get("open") or
                             reg.get("totalOpen") or 0)

                # Kalau target masih 0 tapi ada submitted/approved, hitung dari sana
                if target == 0 and (submitted + approved + rejected + draft + open_cnt) > 0:
                    target = submitted + approved + rejected + draft + open_cnt

                sync_count = submitted + approved + rejected

                # Status dominan
                if approved > 0:
                    status_alias = "APPROVED"
                elif rejected > 0:
                    status_alias = "REJECTED"
                elif submitted > 0:
                    status_alias = "SUBMITTED_PENCACAH"
                elif draft > 0:
                    status_alias = "DRAFT"
                else:
                    status_alias = "OPEN"

                rows.append({
                    "region5Id": region_code,
                    "targetCount": target,
                    "syncCount": sync_count,
                    "assignmentStatusAlias": status_alias,
                    "username": username,
                    "fullname": fullname,
                })
        return rows

    if kab_id_list:
        # Iterasi per kabupaten agar tidak melebihi limit API
        for kab_code, kab_name, kab_id in kab_id_list:
            print(f"   [>] Responsibility: Kab {kab_name}...")
            page_idx = 0
            size = 10  # API membatasi max 10 per page
            kab_rows = []
            while True:
                payload = {
                    "surveyPeriodId": survey_period_id,
                    "surveyRoleId": role_id,
                    "size": size,
                    "page": page_idx,
                    "search": "",
                    "target": "TARGET_ONLY",
                    "region": make_region(kab_id=kab_id),
                    "regionSummaryLevel": 6
                }
                resp = await fetch_api_safely(page, report_url, payload, token)
                if not resp or not resp.get("success"):
                    # DEBUG: cetak raw response agar bisa dianalisis
                    import json as _json
                    print(f"      [DEBUG] Raw resp (Kab {kab_name} page {page_idx}): {_json.dumps(resp, ensure_ascii=False)[:400] if resp else 'None'}")
                    print(f"      [WARNING] Gagal/kosong untuk Kab {kab_name} page {page_idx}")
                    break

                data = resp.get("data", {})
                content = data.get("content", [])
                if not content:
                    break
                kab_rows.extend(flatten_content(content))
                total_pages = data.get("totalPages", 1)
                if page_idx >= total_pages - 1:
                    break
                page_idx += 1
            all_flat_rows.extend(kab_rows)
            print(f"      -> {len(kab_rows)} SLS assignments untuk Kab {kab_name}")
    else:
        # Fallback: query seluruh provinsi sekaligus
        print("[INFO] Fallback: query responsibility per provinsi (tanpa filter kab)...")
        page_idx = 0
        size = 10  # API membatasi max 10 per page
        while True:
            payload = {
                "surveyPeriodId": survey_period_id,
                "surveyRoleId": role_id,
                "size": size,
                "page": page_idx,
                "search": "",
                "target": "TARGET_ONLY",
                "region": make_region(),
                "regionSummaryLevel": 6
            }
            resp = await fetch_api_safely(page, report_url, payload, token)
            if not resp or not resp.get("success"):
                break
            data = resp.get("data", {})
            content = data.get("content", [])
            if not content:
                break
            all_flat_rows.extend(flatten_content(content))
            total_pages = data.get("totalPages", 1)
            if page_idx >= total_pages - 1:
                break
            page_idx += 1

    print(f" ✅ Total {len(all_flat_rows)} baris data responsibility berhasil ditarik.")
    return all_flat_rows



def fetch_current_ipas_data(supabase_client):
    if supabase_client:
        try:
            res = supabase_client.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
            if res.data:
                return res.data[0].get("value")
        except Exception as e:
            print(f"[WARNING] Gagal mengambil ipas_data lama dari Supabase: {e}")
    return None

def compress_sls(sls_list):
    return [
        [
            item.get("sls_code", ""),
            item.get("target_count", 0),
            item.get("sync_count", 0),
            item.get("officers", [])
        ]
        for item in sls_list
    ]

# =====================================================================
# HELPER FUNCTIONS UNTUK IPAS REPORT (DARI generate_ipas_report.py)
# =====================================================================

def is_tambahan(code_identity):
    if not code_identity:
        return False
    cleaned = code_identity.strip()
    if not cleaned.startswith("72"):
        return True
    parts = [p.strip() for p in cleaned.split(" - ")]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source in known_sources:
        return False
    if source.startswith("SE26") or source.startswith("SE2026"):
        return False
    return True

def extract_sls_code(code_identity):
    if not code_identity:
        return ""
    parts = [p.strip() for p in code_identity.split(" - ")]
    prefix = parts[0]
    digits = "".join([c for c in prefix if c.isdigit()])
    if digits.startswith("72"):
        if len(digits) >= 14:
            return digits[:14]
    return ""

def parse_bps_datetime(dt_str, local_tz):
    if not dt_str:
        return None
    cleaned = dt_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    elif not ("+" in cleaned[10:] or (cleaned[10:].count("-") > 0)):
        cleaned = cleaned + "+00:00"
    dt = datetime.datetime.fromisoformat(cleaned)
    return dt.astimezone(local_tz)

def classify_tambahan(code_identity, data1, data6):
    code_id_upper = (code_identity or "").upper()
    data1_upper = (data1 or "").upper()
    data6_upper = (data6 or "").upper()
    
    if "BANGUNAN KOSONG" in data1_upper or "RUMAH KOSONG" in data1_upper or "KOSONG" in data1_upper or "BANGUNAN KOSONG" in code_id_upper or "RUMAH KOSONG" in code_id_upper:
        return "Bangunan/Rumah Kosong", False
    if "1. YA" in code_id_upper or "1.YA" in code_id_upper:
        return "Keluarga Usaha", True
    if "2. TIDAK" in code_id_upper or "2.TIDAK" in code_id_upper:
        return "Keluarga (Bukan Usaha)", False
    if "KELUARGA" in data6_upper:
        if "UMKM" in data6_upper or "UMB" in data6_upper:
            return "Keluarga Usaha", True
        return "Keluarga", False
    if "/" in data1_upper:
        if "UMKM" in data6_upper or "UMB" in data6_upper:
            return "Keluarga Usaha", True
        return "Keluarga", False
    if "BANGUNAN_LAIN" in data6_upper or "BANGUNAN LAIN" in data6_upper:
        return "Bangunan Lain / Usaha", True
    if "UMKM" in data6_upper:
        return "Usaha (UMKM)", True
    if "UMB" in data6_upper:
        return "Usaha (UMB)", True
    return "Usaha Baru", True


session_refresh_lock = asyncio.Lock()

async def get_xsrf_token(page):
    try:
        cookies = await page.context.cookies()
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                return unquote(c["value"])
    except Exception:
        pass
    return ""

async def fetch_api_safely(page, url, payload, token, timeout_seconds=120, max_retries=3, method="POST"):
    global session_refresh_lock
    for attempt in range(1, max_retries + 1):
        try:
            if "fasih-sm.bps.go.id" not in page.url:
                raise Exception("Not on FASIH domain")
                
            current_token = await get_xsrf_token(page) or token
            res = await page.evaluate("""
                async ({url, payload, token, timeoutMs, method}) => {
                    const controller = new AbortController();
                    const id = setTimeout(() => controller.abort(), timeoutMs);
                    try {
                        const fetchOpts = {
                            method: method,
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            signal: controller.signal
                        };
                        if (method !== "GET" && payload !== null) {
                            fetchOpts.body = JSON.stringify(payload);
                        }
                        const r = await fetch(url, fetchOpts);
                        clearTimeout(id);
                        if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}`, status: r.status };
                        const text = await r.text();
                        try {
                            return JSON.parse(text);
                        } catch(e) {
                            return { error: "Invalid JSON", text: text.substring(0, 200) };
                        }
                    } catch(e) {
                        clearTimeout(id);
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload, "token": current_token, "timeoutMs": timeout_seconds * 1000, "method": method})
            
            is_session_error = False
            if isinstance(res, dict):
                err = res.get("error", "")
                status = res.get("status", 0)
                text = res.get("text", "")
                if err == "Invalid JSON" and "<!DOCTYPE html>" in text:
                    is_session_error = True
                elif status in (401, 403):
                    is_session_error = True
                elif "Failed to fetch" in str(err) or "fetch" in str(err).lower():
                    is_session_error = True
                    
            if is_session_error:
                async with session_refresh_lock:
                    new_token = await get_xsrf_token(page)
                    is_valid = await check_session_valid(page, new_token)
                    if not is_valid:
                        print(f"  [WARNING] Sesi FASIH kedaluwarsa saat mengakses {url}. Mencoba menyegarkan halaman browser...")
                        try:
                            if "fasih-sm.bps.go.id" not in page.url:
                                print(f"  [INFO] Menavigasi kembali ke FASIH dashboard karena URL saat ini: {page.url}")
                                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
                            else:
                                await page.reload(timeout=60000, wait_until="domcontentloaded")
                            await asyncio.sleep(2)
                            new_token = await get_xsrf_token(page)
                            is_valid = await check_session_valid(page, new_token)
                            while not is_valid:
                                print("\n==============================================================")
                                print("[WARNING] Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
                                print("Mencoba mendeteksi secara otomatis setiap 15 detik...")
                                print("==============================================================\n", flush=True)
                                await asyncio.sleep(15)
                                if "fasih-sm.bps.go.id" not in page.url and "sso.bps.go.id" not in page.url:
                                    try:
                                        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=30000)
                                    except Exception:
                                        pass
                                new_token = await get_xsrf_token(page)
                                is_valid = await check_session_valid(page, new_token)
                            print("  [SUCCESS] Sesi berhasil diperbarui dan diverifikasi!")
                        except Exception as refresh_err:
                            print(f"  [ERROR] Gagal menyegarkan halaman browser: {refresh_err}")
                if attempt < max_retries:
                    continue

            if isinstance(res, dict) and res.get("error"):
                status = res.get("status", 0)
                if status in (502, 503, 504) and attempt < max_retries:
                    wait_sec = 5 * attempt
                    print(f"    [RETRY {attempt}/{max_retries}] Server error {status}, menunggu {wait_sec}s...")
                    await asyncio.sleep(wait_sec)
                    continue
            return res
        except Exception as e:
            err_str = str(e)
            is_session_error = False
            if any(x in err_str.lower() for x in ["failed to fetch", "context was destroyed", "navigation", "destroyed", "execution context", "not on fasih domain"]):
                is_session_error = True
                
            if is_session_error:
                async with session_refresh_lock:
                    new_token = await get_xsrf_token(page)
                    is_valid = await check_session_valid(page, new_token)
                    if not is_valid:
                        print(f"  [WARNING] Sesi FASIH kedaluwarsa/bermasalah ({err_str}). Mencoba menyegarkan halaman browser...")
                        try:
                            if "fasih-sm.bps.go.id" not in page.url:
                                print(f"  [INFO] Menavigasi kembali ke FASIH dashboard karena URL saat ini: {page.url}")
                                await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
                            else:
                                await page.reload(timeout=60000, wait_until="domcontentloaded")
                            await asyncio.sleep(2)
                            new_token = await get_xsrf_token(page)
                            is_valid = await check_session_valid(page, new_token)
                            while not is_valid:
                                print("\n==============================================================")
                                print("[WARNING] Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
                                print("Mencoba mendeteksi secara otomatis setiap 15 detik...")
                                print("==============================================================\n", flush=True)
                                await asyncio.sleep(15)
                                if "fasih-sm.bps.go.id" not in page.url and "sso.bps.go.id" not in page.url:
                                    try:
                                        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=30000)
                                    except Exception:
                                        pass
                                new_token = await get_xsrf_token(page)
                                is_valid = await check_session_valid(page, new_token)
                            print("  [SUCCESS] Sesi berhasil diperbarui dan diverifikasi!")
                        except Exception as refresh_err:
                            print(f"  [ERROR] Gagal menyegarkan halaman browser: {refresh_err}")
                if attempt < max_retries:
                    continue
            
            if attempt == max_retries:
                print(f"    [ERROR] Gagal fetch: {e}")
                return {"error": err_str}
            await asyncio.sleep(2)

# =====================================================================
# PIPELINE UTAMA LAPORAN IPAS (DARI generate_ipas_report.py)
# =====================================================================

async def run_ipas_report_generation(page, xsrf_token):
    print("\n==============================================================")
    print("  MEMULAI PIPELINE LAPORAN IPAS (generate_ipas_report)")
    print("==============================================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define surveys
    surveys = {
        "se_umum": {
            "period_id": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "prov_id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "label": "Sensus Ekonomi 2026 (Umum)",
            "kabs": [
                {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "bc32354f-1245-426f-b2cf-a5733e1295ad"},
                {"code": "02", "name": "[02] BANGGAI", "id": "530e9ca5-86ba-434e-9b04-405102e6d900"},
                {"code": "03", "name": "[03] MOROWALI", "id": "9783f0c1-f047-477f-8840-11eae7cf70e2"},
                {"code": "04", "name": "[04] POSO", "id": "fb9cd9f0-c4c0-4a37-9041-57190693f625"},
                {"code": "05", "name": "[05] DONGGALA", "id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"},
                {"code": "06", "name": "[06] TOLI-TOLI", "id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4"},
                {"code": "07", "name": "[07] BUOL", "id": "c523694a-2e72-4570-9489-da2d7b119fe7"},
                {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"},
                {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "736c4c22-51d1-44be-8b2c-aa197d9459a4"},
                {"code": "10", "name": "[10] SIGI", "id": "0061da62-2a47-4dee-b8d0-239b33e2c59d"},
                {"code": "11", "name": "[11] BANGGAI LAUT", "id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"},
                {"code": "12", "name": "[12] MOROWALI UTARA", "id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"},
                {"code": "71", "name": "[71] PALU", "id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"}
            ]
        },
        "se_ub": {
            "period_id": "37526b20-81c8-42f5-a895-6190137d7394",
            "prov_id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
            "label": "Sensus Ekonomi 2026 - UB (Usaha Besar)",
            "kabs": [
                {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb"},
                {"code": "02", "name": "[02] BANGGAI", "id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b"},
                {"code": "03", "name": "[03] MOROWALI", "id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424"},
                {"code": "04", "name": "[04] POSO", "id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22"},
                {"code": "05", "name": "[05] DONGGALA", "id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb"},
                {"code": "06", "name": "[06] TOLI-TOLI", "id": "d3a28bfa-b611-488b-8255-369da5cedbf7"},
                {"code": "07", "name": "[07] BUOL", "id": "dfe4c643-3282-40db-a5fd-cb288a4f592d"},
                {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "f18109d2-fc8b-4b9c-886a-dc242d21206e"},
                {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "4d01eba1-5ae9-4603-82a6-2c831aea9905"},
                {"code": "10", "name": "[10] SIGI", "id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90"},
                {"code": "11", "name": "[11] BANGGAI LAUT", "id": "288c5680-f6d5-4783-a946-d5a06f547c02"},
                {"code": "12", "name": "[12] MOROWALI UTARA", "id": "a5324f17-7a00-436f-b468-2fc59fcf605d"},
                {"code": "71", "name": "[71] PALU", "id": "1acfedb4-276e-44d6-9e45-6d43588536d6"}
            ]
        }
    }

    # Load region maps
    region_map = {}
    region_map_path = os.path.join(script_dir, "region_map_sulteng.json")
    try:
        with open(region_map_path, "r", encoding="utf-8") as f:
            region_map = json.load(f)
        print(f"[INFO] {region_map_path} berhasil dimuat.")
    except Exception as e:
        print(f"[WARNING] Gagal memuat region_map_sulteng.json: {e}")

    kec_id_to_code = {}
    kec_id_to_desas = {}
    region_map_full_path = os.path.join(script_dir, "region_map_sulteng_full.json")
    try:
        with open(region_map_full_path, "r", encoding="utf-8") as f:
            full_map = json.load(f)
        for kab_code, kab_data in full_map.get("kabupaten", {}).items():
            for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
                kec_id = kec_data.get("kec_id")
                if kec_id:
                    kec_id_to_code[kec_id] = kec_code
                    desas = []
                    for desa_code, desa_data in kec_data.get("desa", {}).items():
                        d_id = desa_data.get("desa_id")
                        if d_id:
                            desas.append({
                                "id": d_id,
                                "name": desa_data.get("desa_name", desa_code)
                            })
                    kec_id_to_desas[kec_id] = desas
        print(f"[INFO] {region_map_full_path} loaded. Mapped {len(kec_id_to_code)} kecamatan UUIDs to codes and desas.")
    except Exception as e:
        print(f"[WARNING] Gagal memuat region_map_sulteng_full.json: {e}")

    output_data = {}
    datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"

    for survey_key, survey_cfg in surveys.items():
        print(f"\n=========================================")
        print(f"Memproses Survey: {survey_cfg['label']}")
        print(f"=========================================")
        
        period_id = survey_cfg["period_id"]
        sls_status_map = {}
        processed_record_ids = set()
        
        # Initialize final report dict
        report_data = {}
        for k in survey_cfg["kabs"]:
            import re
            match = re.search(r"\[(\d+)\]", k["name"])
            kab_code = "72" + match.group(1) if match else ""
            
            kec_list_initial = []
            kec_items = region_map.get(kab_code, {}).get("kecamatan", [])
            for kec in kec_items:
                if kec["name"] == "-":
                    continue
                
                kec_list_initial.append({
                    "kec_name": kec["name"],
                    "kec_id": kec["id"],
                    "total_prelist": 0,
                    "total_draft": 0,
                    "total_open": 0,
                    "total_submitted": 0,
                    "total_rejected": 0,
                    "total_approved": 0,
                    "total_submitted_pencacah": 0,
                    "total_submitted_respondent": 0,
                    "today_completed": 0,
                    "yesterday_completed": 0,
                    "two_days_ago_completed": 0,
                    "today_completed_breakdown": {},
                    "yesterday_completed_breakdown": {},
                    "two_days_ago_completed_breakdown": {},
                    "new_usaha_today": 0,
                    "new_usaha_yesterday": 0,
                    "new_usaha_overall": 0,
                    "new_rumah_today": 0,
                    "new_rumah_yesterday": 0,
                    "new_rumah_overall": 0,
                    "new_businesses": []
                })

            report_data[k["name"]] = {
                "kabupaten": k["name"],
                "total_prelist": 0,
                "total_draft": 0,
                "total_open": 0,
                "total_submitted": 0,
                "total_rejected": 0,
                "total_approved": 0,
                "total_submitted_pencacah": 0,
                "total_submitted_respondent": 0,
                "today_completed": 0,
                "yesterday_completed": 0,
                "two_days_ago_completed": 0,
                "today_completed_breakdown": {},
                "yesterday_completed_breakdown": {},
                "two_days_ago_completed_breakdown": {},
                "new_usaha_today": 0,
                "new_usaha_yesterday": 0,
                "new_rumah_today": 0,
                "new_rumah_yesterday": 0,
                "new_usaha_overall": 0,
                "new_rumah_overall": 0,
                "new_businesses": [],
                "kecamatan_list": kec_list_initial
            }

        for kab in survey_cfg["kabs"]:
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "target"
                }
            }
            payload_nontarget = {
                "start": 0, "length": 1000, "columns": [
                    {"data": "id"},
                    {"data": "codeIdentity"},
                    {"data": "data1"},
                    {"data": "data6"},
                    {"data": "assignmentStatusAlias"},
                    {"data": "region"}
                ], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "non-target"
                }
            }
            
            import re
            match = re.search(r"\[(\d+)\]", kab["name"])
            kab_code = "72" + match.group(1) if match else ""
            kec_items = region_map.get(kab_code, {}).get("kecamatan", [])
            kecs_to_fetch = [kec for kec in kec_items if kec["name"] != "-"]

            async def fetch_kec_status_agg(kec):
                kec_id = kec["id"]
                kec_name = kec["name"]
                payload_kec = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": survey_cfg["prov_id"],
                        "region2Id": kab["id"],
                        "region3Id": kec_id,
                        "surveyPeriodId": period_id,
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "target"
                    }
                }
                res_kec = await fetch_api_safely(page, datatable_url, payload_kec, xsrf_token)
                
                kec_prelist = res_kec.get("totalHit", 0) if res_kec else 0
                
                kec_submitted = 0
                kec_approved = 0
                kec_rejected = 0
                kec_draft = 0
                kec_submitted_pencacah = 0
                kec_submitted_respondent = 0
                
                desas = kec_id_to_desas.get(kec_id, [])
                if kec_prelist >= 10000 and desas:
                    print(f"      [INFO] Kec {kec_name} memiliki totalHit {kec_prelist} (>= 10000) di progress report. Membagi query per Desa...")
                    
                    async def fetch_desa_status_agg(desa):
                        d_id = desa["id"]
                        payload_desa = {
                            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                            "assignmentExtraParam": {
                                "region1Id": survey_cfg["prov_id"],
                                "region2Id": kab["id"],
                                "region3Id": kec_id,
                                "region4Id": d_id,
                                "surveyPeriodId": period_id,
                                "assignmentErrorStatusType": -1,
                                "filterTargetType": "target"
                            }
                        }
                        res_desa = await fetch_api_safely(page, datatable_url, payload_desa, xsrf_token)
                        
                        d_prelist = res_desa.get("totalHit", 0) if res_desa else 0
                        d_submitted = 0
                        d_approved = 0
                        d_rejected = 0
                        d_draft = 0
                        d_submitted_pencacah = 0
                        d_submitted_respondent = 0
                        
                        if res_desa and "searchAggregation" in res_desa:
                            agg = res_desa["searchAggregation"]
                            for item in agg:
                                key = item.get("keyAggregation", "")
                                count = item.get("docCount", 0)
                                if key == "DRAFT":
                                    d_draft += count
                                elif key == "SUBMITTED BY Pencacah":
                                    d_submitted_pencacah += count
                                    d_submitted += count
                                elif key == "SUBMITTED RESPONDENT":
                                    d_submitted_respondent += count
                                    d_submitted += count
                                elif "SUBMITTED" in key:
                                    if "RESPONDENT" in key.upper():
                                        d_submitted_respondent += count
                                    else:
                                        d_submitted_pencacah += count
                                    d_submitted += count
                                elif "REJECTED" in key or "REVOKED" in key:
                                    d_rejected += count
                                    d_submitted += count
                                elif "APPROVED" in key:
                                    d_approved += count
                                    d_submitted += count
                                    
                        return {
                            "total_target": d_prelist,
                            "total_draft": d_draft,
                            "total_submitted": d_submitted,
                            "total_rejected": d_rejected,
                            "total_approved": d_approved,
                            "total_submitted_pencacah": d_submitted_pencacah,
                            "total_submitted_respondent": d_submitted_respondent
                        }
                    
                    desa_tasks = [fetch_desa_status_agg(d) for d in desas]
                    desa_results = await asyncio.gather(*desa_tasks)
                    
                    kec_prelist = 0
                    for dr in desa_results:
                        kec_prelist += dr["total_target"]
                        kec_draft += dr["total_draft"]
                        kec_submitted += dr["total_submitted"]
                        kec_rejected += dr["total_rejected"]
                        kec_approved += dr["total_approved"]
                        kec_submitted_pencacah += dr["total_submitted_pencacah"]
                        kec_submitted_respondent += dr["total_submitted_respondent"]
                        
                    print(f"      [SUCCESS] Kec {kec_name} selesai di-agregasi per Desa. Real Prelist={kec_prelist}")
                else:
                    if res_kec and "searchAggregation" in res_kec:
                        agg = res_kec["searchAggregation"]
                        for item in agg:
                            key = item.get("keyAggregation", "")
                            count = item.get("docCount", 0)
                            if key == "DRAFT":
                                kec_draft += count
                            elif key == "SUBMITTED BY Pencacah":
                                kec_submitted_pencacah += count
                                kec_submitted += count
                            elif key == "SUBMITTED RESPONDENT":
                                kec_submitted_respondent += count
                                kec_submitted += count
                            elif "SUBMITTED" in key:
                                if "RESPONDENT" in key.upper():
                                    kec_submitted_respondent += count
                                else:
                                    kec_submitted_pencacah += count
                                kec_submitted += count
                            elif "REJECTED" in key or "REVOKED" in key:
                                kec_rejected += count
                                kec_submitted += count
                            elif "APPROVED" in key:
                                kec_approved += count
                                kec_submitted += count
                                
                return {
                    "kec_id": kec_id,
                    "total_target": kec_prelist,
                    "total_draft": kec_draft,
                    "total_submitted": kec_submitted,
                    "total_rejected": kec_rejected,
                    "total_approved": kec_approved,
                    "total_submitted_pencacah": kec_submitted_pencacah,
                    "total_submitted_respondent": kec_submitted_respondent
                }

            tasks = [
                fetch_api_safely(page, datatable_url, payload, xsrf_token),
                fetch_api_safely(page, datatable_url, payload_nontarget, xsrf_token)
            ]
            for kec in kecs_to_fetch:
                tasks.append(fetch_kec_status_agg(kec))

            task_results = await asyncio.gather(*tasks)
            res = task_results[0]
            res_nontarget = task_results[1]
            kec_results = task_results[2:]

            kec_status_map_local = {r["kec_id"]: r for r in kec_results}

            for kec_stats in report_data[kab["name"]]["kecamatan_list"]:
                k_id = kec_stats["kec_id"]
                if k_id in kec_status_map_local:
                    ks = kec_status_map_local[k_id]
                    kec_stats["total_prelist"] = ks["total_target"]
                    kec_stats["total_draft"] = ks["total_draft"]
                    kec_stats["total_submitted"] = ks["total_submitted"]
                    kec_stats["total_rejected"] = ks["total_rejected"]
                    kec_stats["total_approved"] = ks["total_approved"]
                    kec_stats["total_submitted_pencacah"] = ks["total_submitted_pencacah"]
                    kec_stats["total_submitted_respondent"] = ks["total_submitted_respondent"]
            
            if not res or "error" in res:
                print(f"  [ERROR] Gagal memproses {kab['name']}: {res.get('error') if res else 'Unknown error'}")
                if res and res.get("text"):
                    print(f"    [RESPONSE TEXT] {res.get('text')}")
                continue
            
            prelist_target = 0
            draft_target = 0
            open_target = 0
            submitted_target = 0
            rejected_target = 0
            approved_target = 0
            submitted_pencacah_target = 0
            submitted_respondent_target = 0
            
            agg_target = res.get("searchAggregation", [])
            for item in agg_target:
                key = item.get("keyAggregation", "")
                count = item.get("docCount", 0)
                prelist_target += count
                if key == "DRAFT":
                    draft_target += count
                elif key == "OPEN":
                    open_target += count
                elif "SUBMITTED" in key:
                    submitted_target += count
                    if "RESPONDENT" in key.upper():
                        submitted_respondent_target += count
                    else:
                        submitted_pencacah_target += count
                elif "REJECTED" in key or "REVOKED" in key:
                    rejected_target += count
                elif "APPROVED" in key:
                    approved_target += count
            
            if prelist_target == 0:
                prelist_target = res.get("totalHit", 0)

            draft_nontarget = 0
            open_nontarget = 0
            submitted_nontarget = 0
            rejected_nontarget = 0
            approved_nontarget = 0
            
            tambahan_usaha = 0
            tambahan_rumah_baru = 0
            nontarget_records = res_nontarget.get("searchData", []) if res_nontarget else []
            
            for item in nontarget_records:
                code_id = item.get("codeIdentity") or ""
                rec_id = item.get("id")
                if rec_id and rec_id not in processed_record_ids:
                    processed_record_ids.add(rec_id)
                    sls_code = extract_sls_code(code_id)
                    if sls_code:
                        status_alias = item.get("assignmentStatusAlias") or ""
                        if status_alias:
                            is_t = not is_tambahan(code_id)
                            key_type = "target" if is_t else "nontarget"
                            if sls_code not in sls_status_map:
                                sls_status_map[sls_code] = {"target": {}, "nontarget": {}}
                            sls_status_map[sls_code][key_type][status_alias] = sls_status_map[sls_code][key_type].get(status_alias, 0) + 1

                if not is_tambahan(code_id):
                    continue
                status = item.get("assignmentStatusAlias", "")
                data1_val = item.get("data1") or ""
                data6_val = str(item.get("data6") or "").upper()
                jenis_lbl, is_usaha_derived = classify_tambahan(code_id, data1_val, data6_val)
                is_rumah = not is_usaha_derived
                
                status_upper = status.upper()
                
                kec_id = None
                n_region = item.get("region", {})
                if n_region:
                    kec_id = n_region.get("level1", {}).get("level2", {}).get("level3", {}).get("id")
                
                kec_stats = None
                if kec_id:
                    for k_item in report_data[kab["name"]]["kecamatan_list"]:
                        if k_item["kec_id"] == kec_id:
                            kec_stats = k_item
                            break
                
                if is_rumah:
                    tambahan_rumah_baru += 1
                    if kec_stats:
                        kec_stats["new_rumah_overall"] += 1
                else:
                    tambahan_usaha += 1
                    if kec_stats:
                        kec_stats["new_usaha_overall"] += 1

                if status_upper == "DRAFT":
                    draft_nontarget += 1
                elif status_upper == "OPEN":
                    open_nontarget += 1
                elif "SUBMITTED" in status_upper:
                    submitted_nontarget += 1
                elif "REJECTED" in status_upper or "REVOKED" in status_upper:
                    rejected_nontarget += 1
                elif "APPROVED" in status_upper:
                    approved_nontarget += 1
            
            total_prelist = prelist_target
            total_draft = draft_target
            total_open = open_target
            total_submitted = submitted_target + approved_target + rejected_target
            total_rejected = rejected_target
            total_approved = approved_target
            total_submitted_pencacah = submitted_pencacah_target
            total_submitted_respondent = submitted_respondent_target
            
            report_data[kab["name"]]["total_prelist"] = total_prelist
            report_data[kab["name"]]["total_draft"] = total_draft
            report_data[kab["name"]]["total_open"] = total_open
            report_data[kab["name"]]["total_submitted"] = total_submitted
            report_data[kab["name"]]["total_rejected"] = total_rejected
            report_data[kab["name"]]["total_approved"] = total_approved
            report_data[kab["name"]]["total_submitted_pencacah"] = total_submitted_pencacah
            report_data[kab["name"]]["total_submitted_respondent"] = total_submitted_respondent
            report_data[kab["name"]]["new_usaha_overall"] = tambahan_usaha
            report_data[kab["name"]]["new_rumah_overall"] = tambahan_rumah_baru
            print(f"  {kab['name']}: Prelist={total_prelist}, UsahaBaruOverall={tambahan_usaha}, RumahBaruOverall={tambahan_rumah_baru}, Draft={total_draft}, Open={total_open}, Submitted={total_submitted}")
            for kec_stats in report_data[kab["name"]]["kecamatan_list"]:
                kec_prelist = kec_stats.get("total_prelist", 0)
                kec_draft = kec_stats.get("total_draft", 0)
                kec_submitted = kec_stats.get("total_submitted", 0)
                kec_open = max(0, kec_prelist - kec_draft - kec_submitted)
                kec_new_usaha = kec_stats.get("new_usaha_overall", 0)
                kec_new_rumah = kec_stats.get("new_rumah_overall", 0)
                kec_name = kec_stats.get("kec_name", "-")
                print(f"    -> Kec {kec_name}: Prelist={kec_prelist}, UsahaBaruOverall={kec_new_usaha}, RumahBaruOverall={kec_new_rumah}, Draft={kec_draft}, Open={kec_open}, Submitted={kec_submitted}")

        prov_original_total = sum(report_data[k["name"]]["total_prelist"] for k in survey_cfg["kabs"])
        prov_new_total = sum(report_data[k["name"]]["new_usaha_overall"] for k in survey_cfg["kabs"])
        prov_new_rumah_total = sum(report_data[k["name"]]["new_rumah_overall"] for k in survey_cfg["kabs"])
        prov_draft_total = sum(report_data[k["name"]]["total_draft"] for k in survey_cfg["kabs"])
        prov_open_total = sum(report_data[k["name"]]["total_open"] for k in survey_cfg["kabs"])
        prov_submitted_total = sum(report_data[k["name"]]["total_submitted"] for k in survey_cfg["kabs"])

        output_data[f"{survey_key}_prov_total"] = prov_original_total
        output_data[f"{survey_key}_prov_new_total"] = prov_new_total
        output_data[f"{survey_key}_prov_new_rumah_total"] = prov_new_rumah_total

        print(f"\n  =========================================")
        print(f"  TOTAL PROVINSI ({survey_cfg['label']}):")
        print(f"  Prelist={prov_original_total}, UsahaBaruOverall={prov_new_total}, RumahBaruOverall={prov_new_rumah_total}, Draft={prov_draft_total}, Open={prov_open_total}, Submitted={prov_submitted_total}")
        print(f"  =========================================\n")

        local_tz = datetime.timezone(datetime.timedelta(hours=8))
        today = datetime.datetime.now(local_tz).date()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        # Load mapping kecamatan dari region_map_sulteng.json
        kab_to_kec_map = {}
        if os.path.exists(region_map_path):
            try:
                with open(region_map_path, "r", encoding="utf-8") as f:
                    rmap = json.load(f)
                    for rdata in rmap.values():
                        kab_to_kec_map[rdata.get("kab_name")] = rdata.get("kecamatan", [])
            except Exception as e:
                print(f"Error loading region map: {e}")

        all_records = []
        print("Mengambil rincian data progres harian tingkat provinsi...")
        start = 0
        length = 500
        
        while True:
            payload = {
                "start": start,
                "length": length,
                "columns": [
                    {"data": "id"},
                    {"data": "codeIdentity"},
                    {"data": "data1"},
                    {"data": "data6"},
                    {"data": "dateCreated"},
                    {"data": "dateModified"},
                    {"data": "assignmentStatusAlias"},
                    {"data": "region"}
                ],
                "order": [{"column": 5, "dir": "desc"}],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            res = await fetch_api_safely(page, datatable_url, payload, xsrf_token)
            if not res or "error" in res:
                print(f"  [ERROR] Gagal mengambil rincian progres provinsi: {res.get('error') if res else 'Unknown error'}")
                if res and res.get("text"):
                    print(f"    [RESPONSE TEXT] {res.get('text')}")
                break
            
            records_part = res.get("searchData", [])
            if not records_part:
                break
                
            all_records.extend(records_part)
            print(f"  Fetched {len(records_part)} records (Total Akumulasi: {len(all_records)})")
            
            has_recent_record = False
            for r in records_part:
                dm_str = r.get("dateModified")
                if dm_str:
                    try:
                        dt = parse_bps_datetime(dm_str, local_tz)
                        if dt and dt.date() >= two_days_ago:
                            has_recent_record = True
                            break
                    except Exception:
                        pass
            
            if not has_recent_record and len(records_part) > 0:
                print(f"  [INFO] Berhenti lebih awal karena halaman ini tidak memiliki record dari H-2 s/d Hari ini.")
                break
                
            start += length
            if start >= res.get("totalHit", 0):
                break
            await asyncio.sleep(0.05)
        
        # Snapshots
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        two_days_ago_str = two_days_ago.strftime("%Y-%m-%d")
        yesterday_snapshot = None
        two_days_ago_snapshot = None
        
        if supabase:
            try:
                res_yest = supabase.table("dashboard_store").select("value").eq("key", f"ipas_data:{yesterday_str}").execute()
                if res_yest.data:
                    yesterday_snapshot = res_yest.data[0].get("value")
                    print(f"  [SUPABASE] Menemukan snapshot kemarin ({yesterday_str}) untuk {survey_key}")
            except Exception as e:
                print(f"  [SUPABASE] Gagal mengambil snapshot kemarin: {e}")
                
            try:
                res_two = supabase.table("dashboard_store").select("value").eq("key", f"ipas_data:{two_days_ago_str}").execute()
                if res_two.data:
                    two_days_ago_snapshot = res_two.data[0].get("value")
                    print(f"  [SUPABASE] Menemukan snapshot 2 hari lalu ({two_days_ago_str}) untuk {survey_key}")
                else:
                    for fallback_offset in [3, 4, 5]:
                        fallback_date = today - datetime.timedelta(days=fallback_offset)
                        fallback_str = fallback_date.strftime("%Y-%m-%d")
                        try:
                            res_fb = supabase.table("dashboard_store").select("value").eq("key", f"ipas_data:{fallback_str}").execute()
                            if res_fb.data:
                                two_days_ago_snapshot = res_fb.data[0].get("value")
                                print(f"  [SUPABASE] H-2 tidak ada. Menggunakan snapshot H-{fallback_offset} ({fallback_str}) sebagai fallback H-2")
                                break
                        except Exception:
                            pass
            except Exception as e:
                print(f"  [SUPABASE] Gagal mengambil snapshot 2 hari lalu: {e}")

        has_yesterday_snapshot = False
        has_two_days_ago_snapshot = False
        
        for k in survey_cfg["kabs"]:
            kab_name = k["name"]
            y_kab = None
            t_kab = None
            
            if yesterday_snapshot and survey_key in yesterday_snapshot:
                y_kab = next((x for x in yesterday_snapshot[survey_key] if x.get("kabupaten") == kab_name), None)
            if two_days_ago_snapshot and survey_key in two_days_ago_snapshot:
                t_kab = next((x for x in two_days_ago_snapshot[survey_key] if x.get("kabupaten") == kab_name), None)
                
            if y_kab:
                has_yesterday_snapshot = True
                report_data[kab_name]["yesterday_completed"] = y_kab.get("today_completed", 0)
                report_data[kab_name]["yesterday_completed_breakdown"] = y_kab.get("today_completed_breakdown", {})
                
                for kec_s in report_data[kab_name]["kecamatan_list"]:
                    y_kec = next((x for x in y_kab.get("kecamatan_list", []) if x.get("kec_id") == kec_s["kec_id"] or x.get("kec_name") == kec_s["kec_name"]), None)
                    if y_kec:
                        kec_s["yesterday_completed"] = y_kec.get("today_completed", 0)
                        kec_s["yesterday_completed_breakdown"] = y_kec.get("today_completed_breakdown", {})
                
                if not t_kab:
                    report_data[kab_name]["two_days_ago_is_estimate"] = True
                    for kec_s in report_data[kab_name]["kecamatan_list"]:
                        kec_s["two_days_ago_is_estimate"] = True
                            
            if t_kab:
                has_two_days_ago_snapshot = True
                report_data[kab_name]["two_days_ago_completed"] = t_kab.get("today_completed", 0)
                report_data[kab_name]["two_days_ago_completed_breakdown"] = t_kab.get("today_completed_breakdown", {})
                report_data[kab_name]["two_days_ago_is_estimate"] = False
                
                for kec_s in report_data[kab_name]["kecamatan_list"]:
                    t_kec = next((x for x in t_kab.get("kecamatan_list", []) if x.get("kec_id") == kec_s["kec_id"] or x.get("kec_name") == kec_s["kec_name"]), None)
                    if t_kec:
                        kec_s["two_days_ago_completed"] = t_kec.get("today_completed", 0)
                        kec_s["two_days_ago_completed_breakdown"] = t_kec.get("today_completed_breakdown", {})
                        kec_s["two_days_ago_is_estimate"] = False  

        print("Mengolah riwayat tanggal dan mengelompokkan ke Kabupaten & Kecamatan...")
        kab_id_to_name = {k["id"]: k["name"] for k in survey_cfg["kabs"]}
        kab_code_to_name = {f"72{k['code']}": k["name"] for k in survey_cfg["kabs"]}
        
        for r in all_records:
            code_id = r.get("codeIdentity") or ""
            rec_id = r.get("id")
            if rec_id and rec_id not in processed_record_ids:
                processed_record_ids.add(rec_id)
                sls_code = extract_sls_code(code_id)
                if sls_code:
                    status_alias = r.get("assignmentStatusAlias") or ""
                    if status_alias:
                        is_t = not is_tambahan(code_id)
                        key_type = "target" if is_t else "nontarget"
                        if sls_code not in sls_status_map:
                            sls_status_map[sls_code] = {"target": {}, "nontarget": {}}
                        sls_status_map[sls_code][key_type][status_alias] = sls_status_map[sls_code][key_type].get(status_alias, 0) + 1

            kab_name = None
            kec_id = None
            
            region = r.get("region", {})
            if region:
                lvl2 = region.get("level1", {}).get("level2", {}) or {}
                kab_id = lvl2.get("id")
                if kab_id and kab_id in kab_id_to_name:
                    kab_name = kab_id_to_name[kab_id]
                else:
                    kab_code = lvl2.get("fullCode")
                    if kab_code and kab_code in kab_code_to_name:
                        kab_name = kab_code_to_name[kab_code]
                
                lvl3 = lvl2.get("level3", {}) or {}
                kec_id = lvl3.get("id")
            
            if not kab_name:
                code_identity = r.get("codeIdentity")
                if code_identity:
                    import re
                    match = re.search(r"\b(72\d{2})\b", code_identity)
                    if match:
                        kab_name = kab_code_to_name.get(match.group(1))
                    else:
                        if len(code_identity) >= 4:
                            kab_name = kab_code_to_name.get(code_identity[:4])
            
            if not kab_name:
                continue
                
            status_alias = r.get("assignmentStatusAlias")
            is_target = not is_tambahan(r.get("codeIdentity") or "")
            
            kec_stats = None
            if kec_id and kab_name in report_data:
                for k_item in report_data[kab_name]["kecamatan_list"]:
                    if k_item["kec_id"] == kec_id:
                        kec_stats = k_item
                        break

            if not kec_stats and kab_name in report_data:
                level_regions = r.get("levelRegions") or []
                kec_name_from_region = None
                for lr in level_regions:
                    if lr.get("level") == 3:
                        kec_name_from_region = (lr.get("name") or "").upper().strip()
                        break
                if kec_name_from_region:
                    for k_item in report_data[kab_name]["kecamatan_list"]:
                        if k_item["kec_name"].upper().strip() == kec_name_from_region:
                            kec_stats = k_item
                            break

            status_upper = (status_alias or "").upper()
            if "SUBMITTED" in status_upper or "APPROVED" in status_upper or "REJECTED" in status_upper or "REVOKED" in status_upper:
                mod_date_str = r.get("dateModified")
                if mod_date_str:
                    try:
                        dt = parse_bps_datetime(mod_date_str, local_tz)
                        mod_date = dt.date() if dt else None
                        
                        if mod_date == today:
                            report_data[kab_name]["today_completed"] += 1
                            bd = report_data[kab_name].setdefault("today_completed_breakdown", {})
                            bd[status_alias] = bd.get(status_alias, 0) + 1
                            
                            if kec_stats:
                                kec_stats["today_completed"] += 1
                                kbd = kec_stats.setdefault("today_completed_breakdown", {})
                                kbd[status_alias] = kbd.get(status_alias, 0) + 1
                        elif mod_date == yesterday and not has_yesterday_snapshot:
                            report_data[kab_name]["yesterday_completed"] += 1
                            bd = report_data[kab_name].setdefault("yesterday_completed_breakdown", {})
                            bd[status_alias] = bd.get(status_alias, 0) + 1
                            
                            if kec_stats:
                                kec_stats["yesterday_completed"] += 1
                                kbd = kec_stats.setdefault("yesterday_completed_breakdown", {})
                                kbd[status_alias] = kbd.get(status_alias, 0) + 1
                        elif mod_date == two_days_ago and not has_two_days_ago_snapshot:
                            report_data[kab_name]["two_days_ago_completed"] += 1
                            bd = report_data[kab_name].setdefault("two_days_ago_completed_breakdown", {})
                            bd[status_alias] = bd.get(status_alias, 0) + 1
                            
                            if kec_stats:
                                kec_stats["two_days_ago_completed"] += 1
                                kbd = kec_stats.setdefault("two_days_ago_completed_breakdown", {})
                                kbd[status_alias] = kbd.get(status_alias, 0) + 1
                    except Exception:
                        pass
                        
            create_date_str = r.get("dateCreated")
            if create_date_str:
                try:
                    dt = parse_bps_datetime(create_date_str, local_tz)
                    create_date = dt.date() if dt else None
                    comp_name = r.get("data1") or "-"
                    code_id = r.get("codeIdentity") or "-"
                    if is_tambahan(code_id):
                        data6_val = str(r.get("data6") or "").upper()
                        jenis_lbl, is_usaha_derived = classify_tambahan(code_id, comp_name, data6_val)
                        is_rumah = not is_usaha_derived
                        
                        if create_date == today:
                            if is_rumah:
                                report_data[kab_name]["new_rumah_today"] += 1
                                if kec_stats:
                                    kec_stats["new_rumah_today"] += 1
                            else:
                                report_data[kab_name]["new_usaha_today"] += 1
                                if kec_stats:
                                    kec_stats["new_usaha_today"] += 1
                        elif create_date == yesterday:
                            if is_rumah:
                                report_data[kab_name]["new_rumah_yesterday"] += 1
                                if kec_stats:
                                    kec_stats["new_rumah_yesterday"] += 1
                            else:
                                report_data[kab_name]["new_usaha_yesterday"] += 1
                                if kec_stats:
                                    kec_stats["new_usaha_yesterday"] += 1
                        
                        date_lbl = "today" if create_date == today else ("yesterday" if create_date == yesterday else "older")
                        biz_item = {
                            "name": comp_name,
                            "code": code_id,
                            "date": date_lbl,
                            "status": status_alias,
                            "type": "rumah" if is_rumah else "usaha",
                            "kecName": kec_stats["kec_name"] if kec_stats else "-",
                            "jenis": jenis_lbl
                        }
                        report_data[kab_name]["new_businesses"].append(biz_item)
                        if kec_stats:
                            kec_stats.setdefault("new_businesses", []).append(biz_item)
                except Exception:
                    pass

        final_list = []
        for kab_name, stats in report_data.items():
            prelist = stats["total_prelist"]
            completed = stats["total_submitted"]
            pct = round((completed / prelist * 100) if prelist > 0 else 0.0, 2)
            
            formatted_kecs = []
            for kec_s in stats["kecamatan_list"]:
                k_prelist = kec_s["total_prelist"]
                k_draft = kec_s["total_draft"]
                k_sub = kec_s["total_submitted"]
                k_open = max(0, k_prelist - k_sub - k_draft)
                kec_s["total_prelist"] = k_prelist
                kec_s["total_open"] = k_open
                kec_s["persentase"] = round((k_sub / k_prelist * 100) if k_prelist > 0 else 0.0, 2)
                kec_s["total_submitted_pencacah"] = kec_s.get("total_submitted_pencacah", 0)
                kec_s["total_submitted_respondent"] = kec_s.get("total_submitted_respondent", 0)
                formatted_kecs.append(kec_s)
            
            final_list.append({
                "kabupaten": kab_name,
                "total_prelist": prelist,
                "total_draft": stats["total_draft"],
                "total_open": stats["total_open"],
                "total_submitted": completed,
                "total_rejected": stats["total_rejected"],
                "total_approved": stats["total_approved"],
                "total_submitted_pencacah": stats.get("total_submitted_pencacah", 0),
                "total_submitted_respondent": stats.get("total_submitted_respondent", 0),
                "persentase": pct,
                "today_completed": stats["today_completed"],
                "yesterday_completed": stats["yesterday_completed"],
                "two_days_ago_completed": stats["two_days_ago_completed"],
                "two_days_ago_is_estimate": stats.get("two_days_ago_is_estimate", False),
                "today_completed_breakdown": stats.get("today_completed_breakdown", {}),
                "yesterday_completed_breakdown": stats.get("yesterday_completed_breakdown", {}),
                "two_days_ago_completed_breakdown": stats.get("two_days_ago_completed_breakdown", {}),
                "new_usaha_today": stats["new_usaha_today"],
                "new_usaha_yesterday": stats["new_usaha_yesterday"],
                "new_rumah_today": stats["new_rumah_today"],
                "new_rumah_yesterday": stats["new_rumah_yesterday"],
                "new_usaha_overall": stats.get("new_usaha_overall", 0),
                "new_rumah_overall": stats.get("new_rumah_overall", 0),
                "new_businesses": stats["new_businesses"],
                "kecamatan_list": formatted_kecs
            })
        
        output_data[survey_key] = final_list
        output_data[f"{survey_key}_sls_status"] = sls_status_map

    now_str = datetime.datetime.now(local_tz).isoformat()
    final_js_obj = {
        "updated_at": now_str,
        "se_umum": output_data["se_umum"],
        "se_ub": output_data["se_ub"],
        "se_umum_sls_status": output_data.get("se_umum_sls_status", {}),
        "se_ub_sls_status": output_data.get("se_ub_sls_status", {}),
        "se_umum_prov_total": output_data.get("se_umum_prov_total", 0),
        "se_ub_prov_total": output_data.get("se_ub_prov_total", 0),
        "se_umum_prov_new_total": output_data.get("se_umum_prov_new_total", 0),
        "se_ub_prov_new_total": output_data.get("se_ub_prov_new_total", 0),
        "se_umum_prov_new_rumah_total": output_data.get("se_umum_prov_new_rumah_total", 0),
        "se_ub_prov_new_rumah_total": output_data.get("se_ub_prov_new_rumah_total", 0)
    }
    
    # Save locally
    ipas_data_path = os.path.join(script_dir, "ipas_data.js")
    with open(ipas_data_path, "w", encoding="utf-8") as f:
        f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
    print(" ✅ File ipas_data.js berhasil disimpan.")

    # Upload to Supabase
    if supabase:
        try:
            print("Mengunggah data IPAS ke Supabase...")
            supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
            supabase.table("dashboard_store").insert({"key": "ipas_data", "value": final_js_obj}).execute()
            print(" ✅ Berhasil mengunggah data IPAS ke Supabase.")
            
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            daily_key = f"ipas_data:{today_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": final_js_obj}).execute()
            print(f" ✅ Berhasil mengunggah data IPAS harian ({daily_key}) ke Supabase.")
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah data IPAS ke Supabase: {e}")

async def check_session_valid(page, token):
    if not token:
        return False
    url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
    payload = {
        "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
        "assignmentExtraParam": {
            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
            "assignmentErrorStatusType": -1
        }
    }
    try:
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        if res and isinstance(res, dict):
            if "_error" in res:
                return False
            return "searchData" in res or "searchAggregation" in res
    except Exception:
        pass
    return False

# =====================================================================
# MAIN PIPELINE SCRAPE
# =====================================================================

async def main():
    start_time = time.time()
    print("==============================================================")
    print("  MEMULAI SCRAPE PROGRES CEPAT (scrape_fast_progress.py)")
    print("==============================================================")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    region_map_path = os.path.join(script_dir, "region_map_sulteng_full.json")
    
    sls_lookup = {}
    if os.path.exists(region_map_path):
        print(f"[INFO] Memuat SLS metadata dari {region_map_path}...")
        with open(region_map_path, "r", encoding="utf-8") as f:
            region_tree = json.load(f)
            for kab_code, kab_data in region_tree.get("kabupaten", {}).items():
                kab_name = kab_data.get("kab_name")
                for kec_code, kec_data in kab_data.get("kecamatan", {}).items():
                    kec_name = kec_data.get("kec_name")
                    for desa_code, desa_data in kec_data.get("desa", {}).items():
                        desa_name = desa_data.get("desa_name")
                        for sls in desa_data.get("sls", []):
                            sls_full_code = sls.get("sls_full_code")
                            if sls_full_code:
                                sls_lookup[sls_full_code] = {
                                    "sls_code": sls_full_code,
                                    "sls_name": sls.get("sls_name"),
                                    "desa_name": desa_name,
                                    "kec_name": kec_name,
                                    "kab_name": kab_name,
                                    "kab_code": kab_code,
                                    "kec_code": kec_code,
                                    "desa_code": desa_code
                                }
        print(f" ✅ Memuat {len(sls_lookup)} metadata SLS.")
    else:
        print(f"[ERROR] File {region_map_path} tidak ditemukan!")
        sys.exit(1)

    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
            print("[INFO] Browser Chromium berhasil dihubungkan.")
        except Exception as e:
            print(f"[ERROR] Gagal menghubungkan ke browser: {e}")
            sys.exit(1)

        attempt_count = 0
        while True:
            attempt_count += 1
            if "fasih-sm.bps.go.id" not in page.url:
                print("[INFO] Navigasi ke FASIH untuk menyegarkan sesi...")
                try:
                    await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"[WARNING] Gagal memuat halaman FASIH: {e}")
            else:
                if attempt_count > 1:
                    print(f"[INFO] Reloading page (attempt {attempt_count})...")
                    try:
                        await page.reload(timeout=60000, wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"[WARNING] Gagal memuat ulang halaman: {e}")

            cookies = await context.cookies()
            token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
            token = unquote(token_raw) if token_raw else ""
            
            if token and await check_session_valid(page, token):
                print("[SUCCESS] Sesi berhasil diverifikasi dan siap digunakan!")
                break
                
            print("\n==============================================================")
            print("[WARNING] Sesi FASIH tidak valid atau telah kedaluwarsa.")
            print("Harap LOGIN atau REFRESH halaman FASIH di browser Chrome Anda.")
            print("Mencoba mendeteksi secara otomatis setiap 15 detik...")
            print("==============================================================\n")
            await asyncio.sleep(15)


        # -------------------------------------------------------------
        # STEP 1: SCRAPE PROGRESS BY RESPONSIBILITY (STATUS ASSIGN PETUGAS)
        # -------------------------------------------------------------
        print("\n--- [STEP 1/2] Menarik Progres Alokasi Petugas ---")
        users_umum = await fetch_users_mapping(page, token, SE_UMUM_PERIOD)
        users_ub = await fetch_users_mapping(page, token, SE_UB_PERIOD)

        if (users_umum is None) or (users_ub is None):
            print("[ERROR] Gagal menarik alokasi petugas. Batalkan proses.")
            if browser:
                try:
                    await page.close()
                    await browser.disconnect()
                except Exception:
                    pass
            sys.exit(1)

        users_map = {}
        for u in users_umum + users_ub:
            uid = u.get("id") or u.get("userId")
            if uid:
                users_map[uid] = {
                    "username": u.get("username", "-"),
                    "fullname": u.get("fullname", "-")
                }

        with open(os.path.join(script_dir, "users_mapping.json"), "w", encoding="utf-8") as f:
            json.dump(users_map, f, indent=2)
        print(" ✅ Mapping user ID diperbarui.")

        raw_responsibility_umum = await fetch_responsibility_report(page, token, SE_UMUM_PERIOD, ROLE_PENCACAH_UMUM, "TARGET_ONLY")
        raw_responsibility_ub = await fetch_responsibility_report(page, token, SE_UB_PERIOD, ROLE_PENCACAH_UB, "TARGET_ONLY")

        # Pengelompokan Data SE Umum
        sls_targets_umum = {}
        sls_breakdowns_umum = {}
        petugas_data_umum = {}
        assign_data_umum_map = {}

        for row in raw_responsibility_umum:
            sls_code = row.get("region5Id")
            if not sls_code:
                continue
            
            target_count = row.get("targetCount", 0)
            sync_count = row.get("syncCount", 0)
            status_alias = row.get("assignmentStatusAlias", "OPEN")
            username = row.get("username")
            fullname = row.get("fullname") or username or "-"

            sls_targets_umum[sls_code] = sls_targets_umum.get(sls_code, 0) + target_count

            # Breakdown status
            sls_breakdowns_umum.setdefault(sls_code, [])
            found = False
            for item in sls_breakdowns_umum[sls_code]:
                if item["status"] == status_alias:
                    item["count"] += target_count
                    found = True
                    break
            if not found:
                sls_breakdowns_umum[sls_code].append({"status": status_alias, "count": target_count})

            # Petugas data
            if username:
                pet_info = petugas_data_umum.setdefault(username, {
                    "username": username,
                    "fullname": fullname,
                    "target_count": 0,
                    "sync_count": 0,
                    "draft_count": 0,
                    "open_count": 0,
                    "submitted_count": 0,
                    "approved_count": 0,
                    "rejected_count": 0,
                })
                pet_info["target_count"] += target_count
                pet_info["sync_count"] += sync_count
                
                cats = categorize_status(status_alias, target_count)
                pet_info["draft_count"] += cats["draft"]
                pet_info["open_count"] += cats["open"]
                pet_info["submitted_count"] += cats["submitted"]
                pet_info["approved_count"] += cats["approved"]
                pet_info["rejected_count"] += cats["rejected"]

            # SLS info
            sls_info = sls_lookup.get(sls_code)
            if sls_info:
                kab_name = sls_info["kab_name"]
                kec_name = sls_info["kec_name"]
                
                key = (kab_name, kec_name)
                assign_data_umum_map.setdefault(key, {
                    "kabupaten": kab_name,
                    "kecamatan": kec_name,
                    "total_prelist": 0,
                    "total_draft": 0,
                    "total_open": 0,
                    "total_submitted": 0,
                    "total_rejected": 0,
                    "total_approved": 0,
                    "total_submitted_pencacah": 0,
                    "total_submitted_respondent": 0,
                    "persentase": 0.0
                })
                
                sum_info = assign_data_umum_map[key]
                sum_info["total_prelist"] += target_count
                cats = categorize_status(status_alias, target_count)
                sum_info["total_draft"] += cats["draft"]
                sum_info["total_open"] += cats["open"]
                sum_info["total_submitted_pencacah"] += cats["submitted_pencacah"]
                sum_info["total_submitted_respondent"] += cats["submitted_respondent"]
                sum_info["total_submitted"] += cats["submitted"]
                sum_info["total_rejected"] += cats["rejected"]
                sum_info["total_approved"] += cats["approved"]

        # Pengelompokan Data SE UB
        sls_targets_ub = {}
        sls_breakdowns_ub = {}
        petugas_data_ub = {}
        assign_data_ub_map = {}

        for row in raw_responsibility_ub:
            sls_code = row.get("region5Id")
            if not sls_code:
                continue
            
            target_count = row.get("targetCount", 0)
            sync_count = row.get("syncCount", 0)
            status_alias = row.get("assignmentStatusAlias", "OPEN")
            username = row.get("username")
            fullname = row.get("fullname") or username or "-"

            sls_targets_ub[sls_code] = sls_targets_ub.get(sls_code, 0) + target_count

            # Breakdown status
            sls_breakdowns_ub.setdefault(sls_code, [])
            found = False
            for item in sls_breakdowns_ub[sls_code]:
                if item["status"] == status_alias:
                    item["count"] += target_count
                    found = True
                    break
            if not found:
                sls_breakdowns_ub[sls_code].append({"status": status_alias, "count": target_count})

            # Petugas data
            if username:
                pet_info = petugas_data_ub.setdefault(username, {
                    "username": username,
                    "fullname": fullname,
                    "target_count": 0,
                    "sync_count": 0,
                    "draft_count": 0,
                    "open_count": 0,
                    "submitted_count": 0,
                    "approved_count": 0,
                    "rejected_count": 0,
                })
                pet_info["target_count"] += target_count
                pet_info["sync_count"] += sync_count
                
                cats = categorize_status(status_alias, target_count)
                pet_info["draft_count"] += cats["draft"]
                pet_info["open_count"] += cats["open"]
                pet_info["submitted_count"] += cats["submitted"]
                pet_info["approved_count"] += cats["approved"]
                pet_info["rejected_count"] += cats["rejected"]

            # SLS info
            sls_info = sls_lookup.get(sls_code)
            if sls_info:
                kab_name = sls_info["kab_name"]
                kec_name = sls_info["kec_name"]
                
                key = (kab_name, kec_name)
                assign_data_ub_map.setdefault(key, {
                    "kabupaten": kab_name,
                    "kecamatan": kec_name,
                    "total_prelist": 0,
                    "total_draft": 0,
                    "total_open": 0,
                    "total_submitted": 0,
                    "total_rejected": 0,
                    "total_approved": 0,
                    "total_submitted_pencacah": 0,
                    "total_submitted_respondent": 0,
                    "persentase": 0.0
                })
                
                sum_info = assign_data_ub_map[key]
                sum_info["total_prelist"] += target_count
                cats = categorize_status(status_alias, target_count)
                sum_info["total_draft"] += cats["draft"]
                sum_info["total_open"] += cats["open"]
                sum_info["total_submitted_pencacah"] += cats["submitted_pencacah"]
                sum_info["total_submitted_respondent"] += cats["submitted_respondent"]
                sum_info["total_submitted"] += cats["submitted"]
                sum_info["total_rejected"] += cats["rejected"]
                sum_info["total_approved"] += cats["approved"]

        # Finalisasi output list untuk assign_data
        assign_data_umum = list(assign_data_umum_map.values())
        for x in assign_data_umum:
            x["persentase"] = round((x["total_submitted"] / x["total_prelist"] * 100) if x["total_prelist"] > 0 else 0.0, 2)
            
        assign_data_ub = list(assign_data_ub_map.values())
        for x in assign_data_ub:
            x["persentase"] = round((x["total_submitted"] / x["total_prelist"] * 100) if x["total_prelist"] > 0 else 0.0, 2)

        # Proses SLS allocations
        processed_sls_umum = []
        for code, target_count in sls_targets_umum.items():
            breakdown = sls_breakdowns_umum.get(code, [])
            sync_count = 0
            for item in breakdown:
                if item["status"] != "OPEN":
                    sync_count += item["count"]
            
            # Cari petugas
            officers = []
            for row in raw_responsibility_umum:
                if row.get("region5Id") == code and row.get("username"):
                    if row.get("username") not in officers:
                        officers.append(row.get("username"))
                        
            processed_sls_umum.append({
                "sls_code": code,
                "target_count": target_count,
                "sync_count": sync_count,
                "officers": officers
            })

        processed_sls_ub = []
        for code, target_count in sls_targets_ub.items():
            breakdown = sls_breakdowns_ub.get(code, [])
            sync_count = 0
            for item in breakdown:
                if item["status"] != "OPEN":
                    sync_count += item["count"]
                    
            officers = []
            for row in raw_responsibility_ub:
                if row.get("region5Id") == code and row.get("username"):
                    if row.get("username") not in officers:
                        officers.append(row.get("username"))
                        
            processed_sls_ub.append({
                "sls_code": code,
                "target_count": target_count,
                "sync_count": sync_count,
                "officers": officers
            })

        # Gabungkan mapping alokasi ke petugas
        formatted_petugas_umum = []
        for u in users_umum:
            username = u.get("username")
            if not username:
                continue
            
            pet_stats = petugas_data_umum.get(username, {})
            formatted_regions = []
            u_regions = u.get("regions") or []
            for r in u_regions:
                r_id = r.get("id")
                r_name = r.get("name")
                r_level = r.get("level")
                if r_id and r_level == 5: # SLS Level
                    formatted_regions.append({"id": r_id, "name": r_name})
                    
            formatted_petugas_umum.append({
                "id": u.get("id") or u.get("userId"),
                "username": username,
                "fullname": u.get("fullname") or u.get("name") or username,
                "target_count": pet_stats.get("target_count", 0),
                "sync_count": pet_stats.get("sync_count", 0),
                "draft_count": pet_stats.get("draft_count", 0),
                "open_count": pet_stats.get("open_count", 0),
                "submitted_count": pet_stats.get("submitted_count", 0),
                "approved_count": pet_stats.get("approved_count", 0),
                "rejected_count": pet_stats.get("rejected_count", 0),
                "regions": formatted_regions,
                "totalRegions": len(formatted_regions)
            })

        formatted_petugas_ub = []
        for u in users_ub:
            username = u.get("username")
            if not username:
                continue
            
            pet_stats = petugas_data_ub.get(username, {})
            formatted_regions = []
            u_regions = u.get("regions") or []
            for r in u_regions:
                r_id = r.get("id")
                r_name = r.get("name")
                r_level = r.get("level")
                if r_id and r_level == 5:
                    formatted_regions.append({"id": r_id, "name": r_name})
                    
            formatted_petugas_ub.append({
                "id": u.get("id") or u.get("userId"),
                "username": username,
                "fullname": u.get("fullname") or u.get("name") or username,
                "target_count": pet_stats.get("target_count", 0),
                "sync_count": pet_stats.get("sync_count", 0),
                "draft_count": pet_stats.get("draft_count", 0),
                "open_count": pet_stats.get("open_count", 0),
                "submitted_count": pet_stats.get("submitted_count", 0),
                "approved_count": pet_stats.get("approved_count", 0),
                "rejected_count": pet_stats.get("rejected_count", 0),
                "regions": formatted_regions,
                "totalRegions": len(formatted_regions)
            })

        # Gabungkan mapping petugas (kombinasi data)
        petugas_data_umum = merge_user_records(formatted_petugas_umum)
        petugas_data_ub = merge_user_records(formatted_petugas_ub)

        # Simpan assign_data.js secara lokal
        js_content = f"window.ASSIGN_DATA_UMUM = {json.dumps(assign_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_DATA_UB   = {json.dumps(assign_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(compress_sls(processed_sls_umum), indent=4, ensure_ascii=False)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UB   = {json.dumps(compress_sls(processed_sls_ub),   indent=4, ensure_ascii=False)};\n"
        js_content += f"window.PETUGAS_DATA_UMUM = {json.dumps(petugas_data_umum, indent=4, ensure_ascii=False)};\n"
        js_content += f"window.PETUGAS_DATA_UB   = {json.dumps(petugas_data_ub,   indent=4, ensure_ascii=False)};\n"
        js_content += """
const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
if (activeSubtab === 'se2026') {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM || [];
    window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM || [];
} else {
    window.ASSIGN_DATA = window.ASSIGN_DATA_UB || [];
    window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB || [];
    window.PETUGAS_DATA = window.PETUGAS_DATA_UB || [];
}
"""
        assign_data_path = os.path.join(script_dir, "assign_data.js")
        with open(assign_data_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(" ✅ File assign_data.js berhasil disimpan.")

        # Upload assign_data ke Supabase
        if supabase:
            try:
                now_iso = datetime.datetime.now().isoformat()
                assign_payload = {
                    "updated_at": now_iso,
                    "assign_data_umum": assign_data_umum,
                    "assign_data_ub": assign_data_ub,
                    "assign_sls_data_umum": compress_sls(processed_sls_umum),
                    "assign_sls_data_ub": compress_sls(processed_sls_ub),
                    "petugas_data_umum": petugas_data_umum,
                    "petugas_data_ub": petugas_data_ub
                }
                raw_str = json.dumps(assign_payload, ensure_ascii=False)
                compressed_str = base64.b64encode(gzip.compress(raw_str.encode('utf-8'))).decode('utf-8')
                db_assign_payload = {
                    "is_compressed": True,
                    "compressed_data": compressed_str
                }

                # ✅ Simpan ke key 'assign_data_fast' (tidak timpa granular!)
                # Key 'assign_data' hanya diisi oleh merge_granulars.py (data lengkap 1.18jt target)
                supabase.table("dashboard_store").delete().eq("key", "assign_data_fast").execute()
                supabase.table("dashboard_store").insert({"key": "assign_data_fast", "value": db_assign_payload}).execute()
                print(" ✅ database_store key 'assign_data_fast' updated (SLS & petugas stats).")

                # Cek apakah data granular sudah ada — kalau belum, isi assign_data sebagai fallback
                existing_granular = supabase.table("dashboard_store").select("key").eq("key", "assign_data").execute()
                if not existing_granular.data:
                    supabase.table("dashboard_store").insert({"key": "assign_data", "value": db_assign_payload}).execute()
                    print(" ℹ️  assign_data belum ada — di-isi dengan fast data sebagai fallback.")
                else:
                    print(" ℹ️  assign_data granular sudah ada → TIDAK ditimpa oleh fast scraper.")

                # Snapshot harian tetap pakai key sendiri
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                daily_key = f"assign_data_fast:{today_str}"
                supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
                supabase.table("dashboard_store").insert({"key": daily_key, "value": db_assign_payload}).execute()
                print(f" ✅ database_store key '{daily_key}' updated.")
            except Exception as e:
                print(f"[ERROR] Gagal mengunggah assign_data ke Supabase: {e}")

        # -------------------------------------------------------------
        # STEP 2: RUN IPAS REPORT PIPELINE (TREN CAPAIAN & USAHA BARU)
        # -------------------------------------------------------------
        print("\n--- [STEP 2/2] Menjalankan Pipeline Laporan IPAS ---")
        try:
            await run_ipas_report_generation(page, token)
        except Exception as e:
            print(f"[ERROR] Pipeline Laporan IPAS gagal: {e}")

        # Cleanup Playwright browser cleanly
        try:
            if browser:
                await page.close()
                await browser.disconnect()
            else:
                await context.close()
        except Exception:
            pass

    duration = time.time() - start_time
    print("\n==============================================================")
    print(f"🎉 UNIFIED UPDATE SELESAI DALAM {duration:.2f} DETIK!")
    print("==============================================================")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Proses dihentikan oleh pengguna.")
        sys.exit(0)
