import openpyxl
import json
import os
import time
from datetime import datetime

def generate():
    start_time = time.time()
    excel_path = 'rekap_progress_petugas_keluarga_usaha_bangkos.xlsx'
    if not os.path.exists(excel_path):
        excel_path = 'rekap_progress_petugas_keberadaan_keluarga_dan_usaha.xlsx'
    print(f"Reading {excel_path}...")
    
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active
    
    rows = sheet.iter_rows(values_only=True)
    header = next(rows)
    
    pencacah_map = {}
    pengawas_map = {}
    kab_summary = {}
    prov_summary = {
        'sls_count': 0,
        'bu_dit': 0, 'bu_bar': 0, 'bu_tdk': 0, 'bu_tut': 0, 'bu_gan': 0, 'bu_pus': 0,
        'kl_dit': 0, 'kl_bar': 0, 'kl_tdk': 0, 'kl_men': 0, 'kl_eli': 0, 'kl_tem': 0, 'kl_khu': 0,
        'bang_kos': 0, 'bangkos_sls': 0,
        'tot_status': 0, 'tot_keb': 0, 'selisih': 0, 'anomali_sls': 0
    }
    
    total_sls_rows = 0
    
    for r in rows:
        total_sls_rows += 1
        sls = str(r[0] or '').strip()
        sub = str(r[1] or '').strip()
        kab_code = sls[:4] if len(sls) >= 4 else ''
        kec_code = sls[:7] if len(sls) >= 7 else ''
        
        # Statuses: r[2:14]
        status_sum = sum(int(x or 0) for x in r[2:14])
        
        bu_tdk = int(r[14] or 0)
        bu_dit = int(r[15] or 0)
        bu_bar = int(r[16] or 0)
        bu_tut = int(r[17] or 0)
        bu_gan = int(r[18] or 0)
        bu_pus = int(r[19] or 0)
        
        kl_tdk = int(r[20] or 0)
        kl_dit = int(r[21] or 0)
        kl_bar = int(r[22] or 0)
        kl_men = int(r[23] or 0)
        kl_eli = int(r[24] or 0)
        kl_tem = int(r[25] or 0)
        kl_khu = int(r[26] or 0)
        
        # Bangunan Kosong (kolom 27 di file bangkos)
        bang_kos = int(r[27] or 0) if len(r) > 27 and isinstance(r[27], (int, float)) else 0
        
        # Email petugas
        if len(r) >= 30 and '@' in str(r[28] or ''):
            pencacah = str(r[28] or '').strip().lower()
            pengawas = str(r[29] or '').strip().lower()
        else:
            pencacah = str(r[31] or '').strip().lower() if len(r) > 31 else ''
            pengawas = str(r[32] or '').strip().lower() if len(r) > 32 else ''
        
        tot_bu = bu_tdk + bu_dit + bu_bar + bu_tut + bu_gan + bu_pus
        tot_kl = kl_tdk + kl_dit + kl_bar + kl_men + kl_eli + kl_tem + kl_khu
        tot_keb = tot_bu + tot_kl
        selisih = status_sum - tot_keb
        is_anomali = (selisih != 0)
        
        # Province summary
        prov_summary['sls_count'] += 1
        prov_summary['bu_dit'] += bu_dit
        prov_summary['bu_bar'] += bu_bar
        prov_summary['bu_tdk'] += bu_tdk
        prov_summary['bu_tut'] += bu_tut
        prov_summary['bu_gan'] += bu_gan
        prov_summary['bu_pus'] += bu_pus
        prov_summary['kl_dit'] += kl_dit
        prov_summary['kl_bar'] += kl_bar
        prov_summary['kl_tdk'] += kl_tdk
        prov_summary['kl_men'] += kl_men
        prov_summary['kl_eli'] += kl_eli
        prov_summary['kl_tem'] += kl_tem
        prov_summary['kl_khu'] += kl_khu
        prov_summary['bang_kos'] += bang_kos
        if bang_kos > 0:
            prov_summary['bangkos_sls'] += 1
        prov_summary['tot_status'] += status_sum
        prov_summary['tot_keb'] += tot_keb
        prov_summary['selisih'] += selisih
        if is_anomali:
            prov_summary['anomali_sls'] += 1
            
        # Kabupaten summary
        if kab_code:
            if kab_code not in kab_summary:
                kab_summary[kab_code] = {
                    'sls_count': 0,
                    'bu_dit': 0, 'bu_bar': 0, 'bu_tdk': 0, 'bu_tut': 0, 'bu_gan': 0, 'bu_pus': 0,
                    'kl_dit': 0, 'kl_bar': 0, 'kl_tdk': 0, 'kl_men': 0, 'kl_eli': 0, 'kl_tem': 0, 'kl_khu': 0,
                    'bang_kos': 0, 'bangkos_sls': 0,
                    'tot_status': 0, 'tot_keb': 0, 'selisih': 0, 'anomali_sls': 0
                }
            ks = kab_summary[kab_code]
            ks['sls_count'] += 1
            ks['bu_dit'] += bu_dit
            ks['bu_bar'] += bu_bar
            ks['bu_tdk'] += bu_tdk
            ks['bu_tut'] += bu_tut
            ks['bu_gan'] += bu_gan
            ks['bu_pus'] += bu_pus
            ks['kl_dit'] += kl_dit
            ks['kl_bar'] += kl_bar
            ks['kl_tdk'] += kl_tdk
            ks['kl_men'] += kl_men
            ks['kl_eli'] += kl_eli
            ks['kl_tem'] += kl_tem
            ks['kl_khu'] += kl_khu
            ks['bang_kos'] += bang_kos
            if bang_kos > 0:
                ks['bangkos_sls'] += 1
            ks['tot_status'] += status_sum
            ks['tot_keb'] += tot_keb
            ks['selisih'] += selisih
            if is_anomali:
                ks['anomali_sls'] += 1
        
        # Full SLS detail representation:
        # 0: sls, 1: sub
        # 2: bu_dit, 3: bu_bar, 4: bu_tdk, 5: bu_tut, 6: bu_gan, 7: bu_pus
        # 8: kl_dit, 9: kl_bar, 10: kl_tdk, 11: kl_men, 12: kl_eli, 13: kl_tem, 14: kl_khu
        # 15: status_sum, 16: tot_keb, 17: selisih, 18: bang_kos
        sls_item = [
            sls, sub,
            bu_dit, bu_bar, bu_tdk, bu_tut, bu_gan, bu_pus,
            kl_dit, kl_bar, kl_tdk, kl_men, kl_eli, kl_tem, kl_khu,
            status_sum, tot_keb, selisih, bang_kos
        ]
        
        def update_petugas(target_dict, email, role):
            if not email: return
            if email not in target_dict:
                target_dict[email] = {
                    'email': email,
                    'role': role,
                    'kabs': set(),
                    'kecs': set(),
                    'sls_count': 0,
                    'bu_dit': 0, 'bu_bar': 0, 'bu_tdk': 0, 'bu_tut': 0, 'bu_gan': 0, 'bu_pus': 0,
                    'kl_dit': 0, 'kl_bar': 0, 'kl_tdk': 0, 'kl_men': 0, 'kl_eli': 0, 'kl_tem': 0, 'kl_khu': 0,
                    'bang_kos': 0, 'bangkos_sls': 0,
                    'tot_status': 0, 'tot_keb': 0, 'selisih': 0, 'anomali_count': 0,
                    'sls': []
                }
            p = target_dict[email]
            if kab_code: p['kabs'].add(kab_code)
            if kec_code: p['kecs'].add(kec_code)
            p['sls_count'] += 1
            p['bu_dit'] += bu_dit
            p['bu_bar'] += bu_bar
            p['bu_tdk'] += bu_tdk
            p['bu_tut'] += bu_tut
            p['bu_gan'] += bu_gan
            p['bu_pus'] += bu_pus
            p['kl_dit'] += kl_dit
            p['kl_bar'] += kl_bar
            p['kl_tdk'] += kl_tdk
            p['kl_men'] += kl_men
            p['kl_eli'] += kl_eli
            p['kl_tem'] += kl_tem
            p['kl_khu'] += kl_khu
            p['bang_kos'] += bang_kos
            if bang_kos > 0:
                p['bangkos_sls'] += 1
            p['tot_status'] += status_sum
            p['tot_keb'] += tot_keb
            p['selisih'] += selisih
            if is_anomali:
                p['anomali_count'] += 1
            p['sls'].append(sls_item)

        update_petugas(pencacah_map, pencacah, 'Pencacah')
        update_petugas(pengawas_map, pengawas, 'Pengawas')

    print(f"Processed {total_sls_rows} rows.")
    print(f"Pencacah: {len(pencacah_map)}, Pengawas: {len(pengawas_map)}")
    
    # Format for JSON output
    def serialize_dict(d):
        res = []
        for item in d.values():
            rec = dict(item)
            rec['kabs'] = sorted(list(rec['kabs']))
            rec['kecs'] = sorted(list(rec['kecs']))
            res.append(rec)
        return res

    pencacah_list = serialize_dict(pencacah_map)
    pengawas_list = serialize_dict(pengawas_map)
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    out_obj = {
        'timestamp': now_str,
        'total_sls': total_sls_rows,
        'summary_prov': prov_summary,
        'summary_kab': kab_summary,
        'pencacah': pencacah_list,
        'pengawas': pengawas_list
    }
    
    out_file = 'data_keberadaan_petugas.js'
    print(f"Writing to {out_file}...")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('window.DATA_KEBERADAAN_PETUGAS = ')
        json.dump(out_obj, f, separators=(',', ':'))
        f.write(';\n')
        
    file_size_mb = os.path.getsize(out_file) / 1024 / 1024
    print(f"Done! {out_file} generated successfully ({file_size_mb:.2f} MB) in {time.time() - start_time:.2f}s")

if __name__ == '__main__':
    generate()
