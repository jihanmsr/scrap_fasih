import asyncio
import json
import os
import sys
import time
import base64
import gzip
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from urllib.parse import unquote

# Import get_authenticated_context from core
from scrape_granular_core import get_authenticated_context

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
        try:
            resp = await page.evaluate(f'''() => fetch("{url}", {{ headers: {{ "X-XSRF-TOKEN": "{token}" }} }}).then(r => r.json())''')
        except Exception as e:
            print(f"[ERROR] Gagal menarik allocations page {page_idx}: {e}")
            return None
            
        if not resp or not resp.get("success"):
            print(f"[ERROR] API allocations page {page_idx} gagal atau success=false.")
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

async def fetch_responsibility_report(page, token, survey_period_id, role_id, target_type):
    # report-progress-by-responsibility hanya memperbolehkan size maksimal 10.
    size = 10
    url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
    
    payload = {
        "surveyPeriodId": survey_period_id,
        "surveyRoleId": role_id,
        "size": size,
        "page": 0,
        "search": "",
        "target": target_type,
        "region": {
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": None,
            "region3Id": None,
            "region4Id": None,
            "region5Id": None,
            "region6Id": None,
            "region7Id": None,
            "region8Id": None,
            "region9Id": None,
            "region10Id": None
        },
        "regionSummaryLevel": 6
    }
    
    print(f"[INFO] Mengambil halaman pertama laporan progres (role {role_id}, target {target_type})...")
    try:
        first_resp = await page.evaluate("""
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
    except Exception as e:
        print(f"[ERROR] Gagal mengevaluasi halaman pertama (role {role_id}): {e}")
        return None
        
    if not first_resp or not first_resp.get("success"):
        err = first_resp.get("_error") if first_resp else "Empty response"
        print(f"[ERROR] Gagal menarik halaman pertama (role {role_id}): {err}")
        return None
        
    data = first_resp.get("data", {})
    all_content = list(data.get("content", []))
    total_elements = data.get("totalElements", 0)
    total_pages = (total_elements + size - 1) // size if size > 0 else 1
    
    print(f" ✅ Laporan progres (role {role_id}): total {total_elements} records, {total_pages} halaman.")
    
    if total_pages > 1:
        # Tarik sisa halaman dalam chunk sequential untuk mencegah overloading Playwright evaluate
        chunk_size = 15
        for i in range(1, total_pages, chunk_size):
            chunk_end = min(total_pages, i + chunk_size)
            print(f"  [INFO] Menarik halaman {i} sampai {chunk_end-1} (role {role_id})...")
            
            chunk_tasks = []
            for p_idx in range(i, chunk_end):
                p_payload = dict(payload)
                p_payload["page"] = p_idx
                chunk_tasks.append(page.evaluate("""
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
                """, {"url": url, "payload": p_payload, "token": token}))
                
            chunk_results = await asyncio.gather(*chunk_tasks)
            for idx, r in enumerate(chunk_results):
                if r and r.get("success"):
                    all_content.extend(r.get("data", {}).get("content", []))
                else:
                    err = r.get("_error") if r else "Empty response"
                    actual_page = i + idx
                    print(f"  [ERROR] Gagal menarik halaman {actual_page} (role {role_id}): {err}")
                    return None
            
            # Jeda singkat agar browser bernapas
            await asyncio.sleep(0.15)
                
    return all_content

def fetch_current_ipas_data(supabase_client):
    if supabase_client:
        try:
            res = supabase_client.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
            if res.data:
                return res.data[0]["value"]
        except Exception as e:
            print(f"[WARNING] Gagal mengambil ipas_data dari Supabase: {e}")
            
    # Fallback ke file lokal
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ipas_path = os.path.join(script_dir, "ipas_data.js")
        if os.path.exists(ipas_path):
            with open(ipas_path, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
    except Exception as e:
        print(f"[WARNING] Gagal mengambil ipas_data lokal: {e}")
        
    return None

def compress_sls(sls_list):
    return [
        [
            item.get("sls_code"),
            item.get("sls_name"),
            item.get("desa_name"),
            item.get("kec_name"),
            item.get("kab_name"),
            item.get("total"),
            item.get("assigned"),
            item.get("unassigned"),
            item.get("sync_count", 0),
            item.get("officers", [])
        ]
        for item in sls_list
    ]

async def main():
    start_time = time.time()
    print("==============================================================")
    print("  MEMULAI SCRAPE PROGRES CEPAT (scrape_fast_progress.py)")
    print("==============================================================")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    region_map_path = os.path.join(script_dir, "region_map_sulteng_full.json")
    
    # 1. Bangun mapping SLS dari region_map_sulteng_full.json
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

    # 2. Hubungkan ke browser dan dapatkan auth token
    async with async_playwright() as p:
        try:
            browser, context, page = await get_authenticated_context(p)
            print("[INFO] Browser Chromium berhasil dihubungkan.")
        except Exception as e:
            print(f"[ERROR] Gagal menghubungkan ke browser: {e}")
            sys.exit(1)

        # Pastikan navigasi ke FASIH untuk otentikasi
        if "fasih-sm.bps.go.id" not in page.url:
            print("[INFO] Navigasi ke FASIH untuk menyegarkan sesi...")
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(2)

        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token_raw:
            print("[ERROR] Sesi tidak ditemukan di browser. Harap login terlebih dahulu di tab Chrome.")
            if browser:
                await browser.close()
            sys.exit(1)
        token = unquote(token_raw)

        # 3. Tarik data user allocations
        users_umum = await fetch_users_mapping(page, token, SE_UMUM_PERIOD)
        users_ub = await fetch_users_mapping(page, token, SE_UB_PERIOD)

        if (users_umum is None) or (users_ub is None):
            print("[ERROR] Gagal menarik alokasi petugas. Batalkan proses agar tidak menimpa data yang ada.")
            if browser:
                try:
                    await page.close()
                    await browser.disconnect()
                except Exception:
                    pass
            sys.exit(1)

        # Simpan users_mapping.json secara lokal
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

        # 4. Tarik laporan responsibility (via chunked page.evaluate)
        print("[INFO] Memulai query report-progress-by-responsibility...")
        umum_pencacah = await fetch_responsibility_report(page, token, SE_UMUM_PERIOD, ROLE_PENCACAH_UMUM, "ALL")
        umum_pengawas = await fetch_responsibility_report(page, token, SE_UMUM_PERIOD, ROLE_PENGAWAS_UMUM, "TARGET_ONLY")
        ub_pencacah = await fetch_responsibility_report(page, token, SE_UB_PERIOD, ROLE_PENCACAH_UB, "ALL")
        ub_pengawas = await fetch_responsibility_report(page, token, SE_UB_PERIOD, ROLE_PENGAWAS_UB, "TARGET_ONLY")

        # Tutup tab / disconnect browser
        try:
            if browser:
                await page.close()
                await browser.disconnect()
            else:
                await context.close()
        except Exception:
            pass

        # Guard checks to prevent overwriting dashboard files with empty/failed data.
        # SE Umum MUST not be None or empty.
        if (umum_pencacah is None) or (umum_pengawas is None):
            print("[ERROR] Pengunduhan laporan progres SE Umum gagal (HTTP error atau response null). Batalkan proses agar tidak menimpa data yang ada.")
            sys.exit(1)
            
        if len(umum_pencacah) == 0 or len(umum_pengawas) == 0:
            print("[ERROR] Laporan progress SE Umum kosong! Batalkan proses agar tidak menimpa data yang ada.")
            sys.exit(1)
            
        if (ub_pencacah is None) or (ub_pengawas is None):
            print("[ERROR] Pengunduhan laporan progres SE UB gagal. Batalkan proses agar tidak menimpa data yang ada.")
            sys.exit(1)

    print(f"[INFO] Pengunduhan API selesai dalam {time.time() - start_time:.2f} detik. Memproses data...")

    # 5. Agregasikan Target dan Status breakdowns untuk SE Umum
    print("[INFO] Memproses data SE Umum...")
    sls_targets_umum = {}
    sls_breakdowns_umum = {}
    for item in umum_pengawas:
        for reg in item.get("regionSummary", []):
            code = reg.get("regionCode")
            if code:
                sls_targets_umum[code] = reg.get("total", 0)
                sls_breakdowns_umum[code] = reg.get("statusBreakdown", [])

    sls_assigned_umum = {}
    sls_officers_umum = {}
    for item in umum_pencacah:
        username = item.get("username")
        fullname = item.get("fullname")
        ofc_str = f"{fullname} ({username})" if fullname and fullname != "-" else username
        for reg in item.get("regionSummary", []):
            code = reg.get("regionCode")
            if code:
                sls_assigned_umum[code] = sls_assigned_umum.get(code, 0) + reg.get("total", 0)
                sls_officers_umum.setdefault(code, set()).add(ofc_str)

    all_sls_umum = set(sls_targets_umum.keys()).union(set(sls_assigned_umum.keys()))
    processed_sls_umum = []
    for code in all_sls_umum:
        sls_info = sls_lookup.get(code)
        total = sls_targets_umum.get(code, 0)
        assigned = sls_assigned_umum.get(code, 0)
        unassigned = max(0, total - assigned)
        breakdown = sls_breakdowns_umum.get(code, [])
        sync_count = sum(c.get("count", 0) for c in breakdown if c.get("status", "").upper() not in ["OPEN", "DRAFT"])
        
        processed_sls_umum.append({
            "sls_code": code,
            "sls_name": sls_info["sls_name"] if sls_info else "-",
            "desa_name": sls_info["desa_name"] if sls_info else "-",
            "kec_name": sls_info["kec_name"] if sls_info else "-",
            "kab_name": sls_info["kab_name"] if sls_info else "-",
            "total": total,
            "assigned": assigned,
            "unassigned": unassigned,
            "sync_count": sync_count,
            "officers": list(sls_officers_umum.get(code, []))
        })

    # 6. Agregasikan Target dan Status breakdowns untuk SE UB
    print("[INFO] Memproses data SE UB...")
    sls_targets_ub = {}
    sls_breakdowns_ub = {}
    for item in ub_pengawas:
        for reg in item.get("regionSummary", []):
            code = reg.get("regionCode")
            if code:
                sls_targets_ub[code] = reg.get("total", 0)
                sls_breakdowns_ub[code] = reg.get("statusBreakdown", [])

    sls_assigned_ub = {}
    sls_officers_ub = {}
    for item in ub_pencacah:
        username = item.get("username")
        fullname = item.get("fullname")
        ofc_str = f"{fullname} ({username})" if fullname and fullname != "-" else username
        for reg in item.get("regionSummary", []):
            code = reg.get("regionCode")
            if code:
                sls_assigned_ub[code] = sls_assigned_ub.get(code, 0) + reg.get("total", 0)
                sls_officers_ub.setdefault(code, set()).add(ofc_str)

    all_sls_ub = set(sls_targets_ub.keys()).union(set(sls_assigned_ub.keys()))
    processed_sls_ub = []
    for code in all_sls_ub:
        sls_info = sls_lookup.get(code)
        total = sls_targets_ub.get(code, 0)
        assigned = sls_assigned_ub.get(code, 0)
        unassigned = max(0, total - assigned)
        breakdown = sls_breakdowns_ub.get(code, [])
        sync_count = sum(c.get("count", 0) for c in breakdown if c.get("status", "").upper() not in ["OPEN", "DRAFT"])

        processed_sls_ub.append({
            "sls_code": code,
            "sls_name": sls_info["sls_name"] if sls_info else "-",
            "desa_name": sls_info["desa_name"] if sls_info else "-",
            "kec_name": kec_name if 'kec_name' in locals() else "-",
            "kab_name": kab_name if 'kab_name' in locals() else "-",
            "total": total,
            "assigned": assigned,
            "unassigned": unassigned,
            "sync_count": sync_count,
            "officers": list(sls_officers_ub.get(code, []))
        })

    # 7. Buat assign_data variables
    assign_umum_dict = {}
    for k, v in KAB_NAMES.items():
        assign_umum_dict[k] = {
            "kode_kab": k,
            "nama_kab": v,
            "total": 0,
            "assigned": 0,
            "have_not_assigned": 0,
            "timestamp": datetime.now().isoformat()
        }
    for sls in processed_sls_umum:
        kab_code = sls["sls_code"][:4]
        if kab_code in assign_umum_dict:
            assign_umum_dict[kab_code]["total"] += sls["total"]
            assign_umum_dict[kab_code]["assigned"] += sls["assigned"]
            assign_umum_dict[kab_code]["have_not_assigned"] += sls["unassigned"]

    assign_data_umum = list(assign_umum_dict.values())

    assign_ub_total = sum(s["total"] for s in processed_sls_ub)
    assign_ub_assigned = sum(s["assigned"] for s in processed_sls_ub)
    assign_ub_unassigned = sum(s["unassigned"] for s in processed_sls_ub)
    assign_data_ub = [
        {
            "kode_kab": "7200",
            "nama_kab": "SULAWESI TENGAH",
            "total": assign_ub_total,
            "assigned": assign_ub_assigned,
            "have_not_assigned": assign_ub_unassigned,
            "timestamp": datetime.now().isoformat()
        }
    ]

    petugas_data_umum = []
    for u in users_umum:
        regions = u.get("regions", [])
        formatted_regions = [{"regionCode": r.get("regionCode"), "regionName": r.get("regionName")} for r in regions]
        petugas_data_umum.append({
            "username": u.get("username", "-"),
            "fullname": u.get("fullname", "-"),
            "regions": formatted_regions,
            "totalRegions": len(formatted_regions)
        })

    petugas_data_ub = []
    for u in users_ub:
        regions = u.get("regions", [])
        formatted_regions = [{"regionCode": r.get("regionCode"), "regionName": r.get("regionName")} for r in regions]
        petugas_data_ub.append({
            "username": u.get("username", "-"),
            "fullname": u.get("fullname", "-"),
            "regions": formatted_regions,
            "totalRegions": len(formatted_regions)
        })

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

    # 8. Update ipas_data sambil mempertahankan data history timeline
    print("[INFO] Menggabungkan laporan progres dengan ipas_data historis...")
    current_ipas = fetch_current_ipas_data(supabase)
    if not current_ipas:
        print("[WARNING] ipas_data lama tidak ditemukan. Membuat template default...")
        current_ipas = {
            "se_umum": [{"kabupaten": name, "total_prelist": 0, "total_draft": 0, "total_open": 0, "total_submitted": 0, "total_rejected": 0, "total_approved": 0, "total_submitted_pencacah": 0, "total_submitted_respondent": 0, "persentase": 0.0, "today_completed": 0, "yesterday_completed": 0, "two_days_ago_completed": 0, "today_completed_breakdown": {}, "yesterday_completed_breakdown": {}, "two_days_ago_completed_breakdown": {}, "new_usaha_today": 0, "new_usaha_yesterday": 0, "new_rumah_today": 0, "new_rumah_yesterday": 0, "new_usaha_overall": 0, "new_rumah_overall": 0, "new_businesses": [], "kecamatan_list": []} for name in KAB_NAMES.values()],
            "se_ub": [{"kabupaten": name, "total_prelist": 0, "total_draft": 0, "total_open": 0, "total_submitted": 0, "total_rejected": 0, "total_approved": 0, "total_submitted_pencacah": 0, "total_submitted_respondent": 0, "persentase": 0.0, "today_completed": 0, "yesterday_completed": 0, "two_days_ago_completed": 0, "today_completed_breakdown": {}, "yesterday_completed_breakdown": {}, "two_days_ago_completed_breakdown": {}, "new_usaha_today": 0, "new_usaha_yesterday": 0, "new_rumah_today": 0, "new_rumah_yesterday": 0, "new_usaha_overall": 0, "new_rumah_overall": 0, "new_businesses": [], "kecamatan_list": []} for name in KAB_NAMES.values()]
        }

    # Bikin SLS status maps untuk se_umum dan se_ub
    se_umum_sls_status = {}
    for code, breakdown in sls_breakdowns_umum.items():
        target_stats = {}
        for c in breakdown:
            status_name = c.get("status")
            count = c.get("count", 0)
            if status_name:
                target_stats[status_name] = target_stats.get(status_name, 0) + count
        se_umum_sls_status[code] = {
            "target": target_stats,
            "nontarget": {}
        }

    se_ub_sls_status = {}
    for code, breakdown in sls_breakdowns_ub.items():
        target_stats = {}
        for c in breakdown:
            status_name = c.get("status")
            count = c.get("count", 0)
            if status_name:
                target_stats[status_name] = target_stats.get(status_name, 0) + count
        se_ub_sls_status[code] = {
            "target": target_stats,
            "nontarget": {}
        }

    # Helper untuk memperbarui list kabupaten & kecamatan
    def update_survey_statistics(survey_list, sls_targets, sls_breakdowns):
        for kab in survey_list:
            kab_name = kab.get("kabupaten")
            
            kab_prelist = 0
            kab_draft = 0
            kab_open = 0
            kab_submitted = 0
            kab_rejected = 0
            kab_approved = 0
            kab_sub_pencacah = 0
            kab_sub_respondent = 0

            # Hitung total dan breakdown di tingkat Kabupaten
            for sls_code, breakdown in sls_breakdowns.items():
                sls_info = sls_lookup.get(sls_code)
                if sls_info and sls_info["kab_name"] == kab_name:
                    for c in breakdown:
                        status = c.get("status", "")
                        count = c.get("count", 0)
                        cats = categorize_status(status, count)
                        kab_draft += cats["draft"]
                        kab_open += cats["open"]
                        kab_sub_pencacah += cats["submitted_pencacah"]
                        kab_sub_respondent += cats["submitted_respondent"]
                        kab_submitted += cats["submitted"]
                        kab_rejected += cats["rejected"]
                        kab_approved += cats["approved"]
                    kab_prelist += sls_targets.get(sls_code, 0)

            # Perbarui kab metrics
            kab["total_prelist"] = kab_prelist
            kab["total_draft"] = kab_draft
            kab["total_open"] = kab_open
            kab["total_submitted"] = kab_submitted
            kab["total_rejected"] = kab_rejected
            kab["total_approved"] = kab_approved
            kab["total_submitted_pencacah"] = kab_sub_pencacah
            kab["total_submitted_respondent"] = kab_sub_respondent
            kab["persentase"] = round((kab_submitted / kab_prelist * 100) if kab_prelist > 0 else 0.0, 2)

            # Hitung total di tingkat Kecamatan
            for kec in kab.get("kecamatan_list", []):
                kec_name = kec.get("kec_name")
                
                kec_prelist = 0
                kec_draft = 0
                kec_open = 0
                kec_submitted = 0
                kec_rejected = 0
                kec_approved = 0
                kec_sub_pencacah = 0
                kec_sub_respondent = 0

                for sls_code, breakdown in sls_breakdowns.items():
                    sls_info = sls_lookup.get(sls_code)
                    if sls_info and sls_info["kab_name"] == kab_name and sls_info["kec_name"] == kec_name:
                        for c in breakdown:
                            status = c.get("status", "")
                            count = c.get("count", 0)
                            cats = categorize_status(status, count)
                            kec_draft += cats["draft"]
                            kec_open += cats["open"]
                            kec_sub_pencacah += cats["submitted_pencacah"]
                            kec_sub_respondent += cats["submitted_respondent"]
                            kec_submitted += cats["submitted"]
                            kec_rejected += cats["rejected"]
                            kec_approved += cats["approved"]
                        kec_prelist += sls_targets.get(sls_code, 0)

                kec["total_prelist"] = kec_prelist
                kec["total_draft"] = kec_draft
                kec["total_open"] = kec_open
                kec["total_submitted"] = kec_submitted
                kec["total_rejected"] = kec_rejected
                kec["total_approved"] = kec_approved
                kec["total_submitted_pencacah"] = kec_sub_pencacah
                kec["total_submitted_respondent"] = kec_sub_respondent
                kec["persentase"] = round((kec_submitted / kec_prelist * 100) if kec_prelist > 0 else 0.0, 2)

    # Lakukan update data statistik
    update_survey_statistics(current_ipas.get("se_umum", []), sls_targets_umum, sls_breakdowns_umum)
    update_survey_statistics(current_ipas.get("se_ub", []), sls_targets_ub, sls_breakdowns_ub)

    # Hitung total tingkat Provinsi
    se_umum_prov_total = sum(kab["total_submitted"] for kab in current_ipas.get("se_umum", []))
    se_ub_prov_total = sum(kab["total_submitted"] for kab in current_ipas.get("se_ub", []))

    now_iso = datetime.now().isoformat()
    final_ipas_obj = {
        "updated_at": now_iso,
        "se_umum": current_ipas.get("se_umum", []),
        "se_ub": current_ipas.get("se_ub", []),
        "se_umum_sls_status": se_umum_sls_status,
        "se_ub_sls_status": se_ub_sls_status,
        "se_umum_prov_total": se_umum_prov_total,
        "se_ub_prov_total": se_ub_prov_total,
        "se_umum_prov_new_total": current_ipas.get("se_umum_prov_new_total", 0),
        "se_ub_prov_new_total": current_ipas.get("se_ub_prov_new_total", 0),
        "se_umum_prov_new_rumah_total": current_ipas.get("se_umum_prov_new_rumah_total", 0),
        "se_ub_prov_new_rumah_total": current_ipas.get("se_ub_prov_new_rumah_total", 0)
    }

    # Simpan ipas_data.js secara lokal
    ipas_data_path = os.path.join(script_dir, "ipas_data.js")
    with open(ipas_data_path, "w", encoding="utf-8") as f:
        f.write(f"window.IPAS_DATA = {json.dumps(final_ipas_obj, ensure_ascii=False, indent=2)};\n")
    print(" ✅ File ipas_data.js berhasil disimpan.")

    # 9. Upload data ke Supabase
    if supabase:
        print("[INFO] Sinkronisasi ke Supabase...")
        
        # A. Upload assign_data (terkompresi)
        try:
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
            
            # Upsert assign_data utama
            supabase.table("dashboard_store").delete().eq("key", "assign_data").execute()
            supabase.table("dashboard_store").insert({"key": "assign_data", "value": db_assign_payload}).execute()
            print(" ✅ database_store key 'assign_data' updated.")
            
            # Upsert assign_data snapshot harian
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"assign_data:{today_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
            supabase.table("dashboard_store").insert({"key": daily_key, "value": db_assign_payload}).execute()
            print(f" ✅ database_store key '{daily_key}' updated.")
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah assign_data ke Supabase: {e}")

        # B. Upload ipas_data
        try:
            # Upsert ipas_data utama
            supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
            supabase.table("dashboard_store").insert({"key": "ipas_data", "value": final_ipas_obj}).execute()
            print(" ✅ database_store key 'ipas_data' updated.")
            
            # Upsert ipas_data snapshot harian
            daily_key_ipas = f"ipas_data:{today_str}"
            supabase.table("dashboard_store").delete().eq("key", daily_key_ipas).execute()
            supabase.table("dashboard_store").insert({"key": daily_key_ipas, "value": final_ipas_obj}).execute()
            print(f" ✅ database_store key '{daily_key_ipas}' updated.")
        except Exception as e:
            print(f"[ERROR] Gagal mengunggah ipas_data ke Supabase: {e}")
            
        print(" ✅ Sinkronisasi Supabase selesai.")
    else:
        print("[WARNING] Koneksi Supabase tidak aktif. Skip upload database.")

    duration = time.time() - start_time
    print("==============================================================")
    print(f"  PROSES SCRAPE PROGRES CEPAT SELESAI DALAM {duration:.2f} DETIK!")
    print("==============================================================")

if __name__ == "__main__":
    asyncio.run(main())
