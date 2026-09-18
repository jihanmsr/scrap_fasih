"""
add_delta_to_rekap_status.py
Menghitung delta penyelesaian dan rincian perubahan status dokumen
(Open, Draft, Submit PPL, Approved, Completed) per SLS, Desa, Kecamatan, dan Kabupaten
antara snapshot 18 September dan 16 September.
"""

import os
import json
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_18 = os.path.join(BASE_DIR, 'Rekap Progress Petugas 18_09.xlsx')
FILE_16 = os.path.join(BASE_DIR, 'rekap_progress_petugas_keluarga_usaha_bangkos.xlsx')
if not os.path.exists(FILE_16):
    FILE_16 = os.path.join(BASE_DIR, 'Rekap Progress Petugas 15_09.xlsx')

REKAP_STATUS_JS = os.path.join(BASE_DIR, 'rekap_status_sls.js')

STATUS_COLS = {
    'open': 'open',
    'draft': 'draft',
    'submitted_pencacah': 'submitted_by_pencacah',
    'submitted_respondent': 'submitted_respondent',
    'approved': 'approved_by_pengawas',
    'completed_admin': 'completed_by_admin_kabupaten',
    'rejected': 'rejected_by_pengawas',
    'revoked': 'revoked_by_pengawas'
}

def main():
    t0 = time.time()
    print("=" * 60)
    print("  MENGHITUNG RINCIAN DELTA STATUS DOKUMEN (18 vs 16 SEPT)")
    print("=" * 60)

    print(f"1. Membaca data terbaru: {os.path.basename(FILE_18)}...")
    df18 = pd.read_excel(FILE_18, dtype={'level_5_full_code': str, 'level_6_code': str})
    
    print(f"2. Membaca data pembanding: {os.path.basename(FILE_16)}...")
    df16 = pd.read_excel(FILE_16, dtype={'level_5_full_code': str, 'level_6_code': str})

    df16['id'] = df16['level_5_full_code'].astype(str).str.split('.').str[0].str.zfill(14) + df16['level_6_code'].astype(str).str.split('.').str[0].str.zfill(2)
    df18['id'] = df18['level_5_full_code'].astype(str).str.split('.').str[0].str.zfill(14) + df18['level_6_code'].astype(str).str.split('.').str[0].str.zfill(2)

    for k, col in STATUS_COLS.items():
        df16[col] = pd.to_numeric(df16[col], errors='coerce').fillna(0).astype(int) if col in df16.columns else 0
        df18[col] = pd.to_numeric(df18[col], errors='coerce').fillna(0).astype(int) if col in df18.columns else 0

    selesai_cols = [
        'submitted_by_pencacah', 'submitted_respondent', 'approved_by_pengawas',
        'completed_by_admin_kabupaten', 'rejected_by_pengawas', 'revoked_by_pengawas'
    ]
    df16['selesai'] = df16[[c for c in selesai_cols if c in df16.columns]].sum(axis=1)
    df18['selesai'] = df18[[c for c in selesai_cols if c in df18.columns]].sum(axis=1)

    # Build maps per SLS
    prev_maps = {}
    for k, col in STATUS_COLS.items():
        prev_maps[k] = df16.set_index('id')[col].to_dict()
    prev_maps['selesai'] = df16.set_index('id')['selesai'].to_dict()

    curr_maps = {}
    for k, col in STATUS_COLS.items():
        curr_maps[k] = df18.set_index('id')[col].to_dict()
    curr_maps['selesai'] = df18.set_index('id')['selesai'].to_dict()

    # Load rekap_status_sls.js
    print(f"3. Membaca {os.path.basename(REKAP_STATUS_JS)}...")
    with open(REKAP_STATUS_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    prefix = 'window.REKAP_STATUS_DATA = '
    idx = js_text.find(prefix)
    data = json.loads(js_text[idx + len(prefix):].rstrip(';\n '))

    def make_deltas(curr_dict, prev_dict):
        res = {}
        for k in STATUS_COLS.keys():
            diff = curr_dict.get(k, 0) - prev_dict.get(k, 0)
            if diff != 0:
                res[k] = diff
        return res

    # 1. SLS
    sls_by_desa = data.get('sls_by_desa', {})
    for d_code, sls_list in sls_by_desa.items():
        for s in sls_list:
            s_id = s.get('id')
            c_vals = {k: curr_maps[k].get(s_id, 0) for k in STATUS_COLS.keys()}
            p_vals = {k: prev_maps[k].get(s_id, 0) for k in STATUS_COLS.keys()}
            s_delta = curr_maps['selesai'].get(s_id, 0) - prev_maps['selesai'].get(s_id, 0)
            
            s['delta_selesai'] = s_delta
            tot = s.get('total', 0)
            s['delta_pct'] = round((s_delta / tot * 100), 1) if tot > 0 else 0.0
            s['delta_details'] = make_deltas(c_vals, p_vals)

    # 2. Desa
    desa_by_kec = data.get('desa_by_kec', {})
    for kc_code, desa_list in desa_by_kec.items():
        for d in desa_list:
            d_code = d.get('code')
            child_sls = sls_by_desa.get(d_code, [])
            d_delta = sum(s.get('delta_selesai', 0) for s in child_sls)
            d['delta_selesai'] = d_delta
            tot = d.get('total', 0)
            d['delta_pct'] = round((d_delta / tot * 100), 1) if tot > 0 else 0.0
            
            # Aggregate status deltas
            agg_d = {}
            for s in child_sls:
                for sk, sv in s.get('delta_details', {}).items():
                    agg_d[sk] = agg_d.get(sk, 0) + sv
            d['delta_details'] = {k: v for k, v in agg_d.items() if v != 0}

    # 3. Kecamatan
    kec_by_kab = data.get('kec_by_kab', {})
    for kb_code, kec_list in kec_by_kab.items():
        for kc in kec_list:
            kc_code = kc.get('code')
            child_desas = desa_by_kec.get(kc_code, [])
            kc_delta = sum(d.get('delta_selesai', 0) for d in child_desas)
            kc['delta_selesai'] = kc_delta
            tot = kc.get('total', 0)
            kc['delta_pct'] = round((kc_delta / tot * 100), 1) if tot > 0 else 0.0
            
            agg_kc = {}
            for d in child_desas:
                for sk, sv in d.get('delta_details', {}).items():
                    agg_kc[sk] = agg_kc.get(sk, 0) + sv
            kc['delta_details'] = {k: v for k, v in agg_kc.items() if v != 0}

    # 4. Kabupaten
    kab_list = data.get('kab', [])
    for kb in kab_list:
        kb_code = kb.get('code')
        child_kecs = kec_by_kab.get(kb_code, [])
        kb_delta = sum(kc.get('delta_selesai', 0) for kc in child_kecs)
        kb['delta_selesai'] = kb_delta
        tot = kb.get('total', 0)
        kb['delta_pct'] = round((kb_delta / tot * 100), 1) if tot > 0 else 0.0

        agg_kb = {}
        for kc in child_kecs:
            for sk, sv in kc.get('delta_details', {}).items():
                agg_kb[sk] = agg_kb.get(sk, 0) + sv
        kb['delta_details'] = {k: v for k, v in agg_kb.items() if v != 0}
        
        details_str = ", ".join([f"{k}: {'+' if v > 0 else ''}{v:,}" for k, v in kb['delta_details'].items()])
        print(f"   * {kb.get('name')}: Delta={kb_delta:,} | Rincian: {details_str}")

    print(f"4. Menyimpan kembali ke {os.path.basename(REKAP_STATUS_JS)}...")
    with open(REKAP_STATUS_JS, 'w', encoding='utf-8') as f:
        f.write(f"window.REKAP_STATUS_DATA = {json.dumps(data, ensure_ascii=False)};\n")

    print(f"\n[SELESAI] Selesai dalam {time.time() - t0:.2f} detik!")

if __name__ == '__main__':
    main()
