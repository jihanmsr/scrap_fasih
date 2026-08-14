-- =========================================================================
-- KUMPULAN QUERY EKSPLORASI DATA SENSUS EKONOMI 2026
-- Sesuai dengan Aturan Emas PPTX BPS dan Metadata SQL Lab
-- =========================================================================

-- -------------------------------------------------------------------------
-- 1. QUERY REKAP TOTAL PROVINSI (Melihat Nasib Target Prelist)
-- Fungsi: Menjawab pertanyaan "Kemana larinya ratusan ribu target ST2023?"
-- (Berapa yang Ditemukan, Tutup, Meninggal, Tidak Ditemukan secara total se-Sulteng).
-- -------------------------------------------------------------------------
SELECT 
    r.jenis_prelist,
    r.ada_keluarga_label AS status_keberadaan_keluarga,
    r.ada_bang_usaha_label AS status_keberadaan_usaha,
    COUNT(a.assignment_id) AS total_data
FROM tgr_fd68e454.base_table_assignment a
JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72' -- Kode Provinsi Sulteng
GROUP BY 
    r.jenis_prelist,
    r.ada_keluarga_label, 
    r.ada_bang_usaha_label
ORDER BY total_data DESC;


-- -------------------------------------------------------------------------
-- 2. QUERY REKAP TOTAL PER KABUPATEN/KOTA
-- Fungsi: Sama seperti di atas, tapi angkanya dipecah per Kabupaten/Kota.
-- -------------------------------------------------------------------------
SELECT 
    a.level_2_name AS kabupaten,
    r.jenis_prelist,
    r.ada_keluarga_label AS status_keberadaan_keluarga,
    r.ada_bang_usaha_label AS status_keberadaan_usaha,
    COUNT(a.assignment_id) AS total_data
FROM tgr_fd68e454.base_table_assignment a
JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72'
GROUP BY 
    a.level_2_name,
    r.jenis_prelist,
    r.ada_keluarga_label, 
    r.ada_bang_usaha_label
ORDER BY a.level_2_name ASC, total_data DESC;


-- -------------------------------------------------------------------------
-- 3. QUERY TARIK DATA MENTAH TIAP USAHA (Lengkap: Nama & Catatan Petugas)
-- Fungsi: Men-download daftar nama target satu per satu untuk membaca "Catatan Petugas" (Alasan kenapa hilang/tutup).
-- WAJIB menggunakan filter Kabupaten (level_2_full_code) di bawah agar SQL Lab tidak nge-hang.
-- -------------------------------------------------------------------------
SELECT 
    a.level_2_name AS kabupaten,
    a.level_4_name AS kecamatan,
    a.level_5_name AS desa,
    r.nama_kk AS nama_kepala_keluarga_saat_ini,
    r.nama_usaha_prelist AS nama_usaha_target_pusat,
    r.ada_keluarga_label AS status_keberadaan_keluarga,
    r.ada_bang_usaha_label AS status_keberadaan_usaha,
    a.assignment_status_alias AS status_dokumen,
    r.alasan_nr_label AS alasan_jika_menolak,
    r.catatan AS catatan_dari_petugas,
    a.current_user_fullname AS petugas_terakhir_yang_pegang,
    CONCAT('https://fasih-sm.bps.go.id/app/assignment-detail/', a.assignment_id) AS link_fasih
FROM tgr_fd68e454.base_table_assignment a
JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified  
WHERE a.is_active = 1                               
  AND a.level_1_full_code = '72'                    
  AND r.jenis_prelist = 'keluarga'                  
  
  -- GANTI KODE DI BAWAH INI UNTUK KABUPATEN LAIN:
  -- 7201(Bangkep), 7202(Banggai), 7203(Morowali), 7204(Poso), 7205(Donggala), 
  -- 7206(Tolitoli), 7207(Buol), 7208(Parimo), 7209(Tojo), 7210(Sigi), 
  -- 7211(Balut), 7212(Morut), 7271(Palu)
  AND a.level_2_full_code = '7204'               
  
  -- OPSI TAMBAHAN (Jika data terpotong limit 9000 baris SQL Lab):
  -- Aktifkan (hapus tanda --) baris di bawah ini untuk menarik per KECAMATAN
  -- AND a.level_4_name = 'PAMONA PUSELEMBA'
ORDER BY a.level_4_name, a.level_5_name;


-- -------------------------------------------------------------------------
-- 4. QUERY MENGUNGKAP "BOTTLENECK" PENGAWAS (DRAFT, REJECT, SUBMITTED)
-- Fungsi: Melihat daftar Usaha Pertanian (UTP) yang secara riil sudah DITEMUKAN pencacah, tapi dokumennya tertahan/ditolak oleh Pengawas.
-- -------------------------------------------------------------------------
SELECT 
    a.level_2_name AS kabupaten,
    a.level_5_name AS desa,
    s.nama_usaha,
    s.pengusaha,
    s.kbli_akhir,
    s.keberadaan_usaha_label AS kondisi_usaha,
    a.assignment_status_alias AS status_dokumen,
    r.catatan_pml AS catatan_pengawas,
    r.catatan AS catatan_petugas,
    a.current_user_fullname AS petugas_terakhir_yang_pegang
FROM tgr_fd68e454.base_table_assignment a
JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id AND a.date_modified = r.assignment_date_modified
JOIN tgr_fd68e454.se2026_nested s 
  ON a.assignment_id = s.assignment_id AND a.date_modified = s.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72'
  AND s.kategori = 'A'
  AND a.assignment_status_alias IN ('REJECTED BY Pengawas', 'DRAFT', 'SUBMITTED BY Pencacah')

  -- GANTI KODE DI BAWAH INI UNTUK KABUPATEN LAIN:
  -- 7201(Bangkep), 7202(Banggai), 7203(Morowali), 7204(Poso), 7205(Donggala), 
  -- 7206(Tolitoli), 7207(Buol), 7208(Parimo), 7209(Tojo), 7210(Sigi), 
  -- 7211(Balut), 7212(Morut), 7271(Palu)
  AND a.level_2_full_code = '7202' -- Contoh: Banggai

  -- OPSI TAMBAHAN (Jika data terpotong limit 9000 baris SQL Lab):
  -- Aktifkan (hapus tanda --) baris di bawah ini untuk menarik per KECAMATAN
  -- AND a.level_4_name = 'LUWUK'
ORDER BY a.level_2_name, a.level_5_name;

-- -------------------------------------------------------------------------
-- 7. QUERY REKAP PENEMUAN "USAHA BARU" DI LAPANGAN
-- Fungsi: Melihat berapa banyak Usaha Baru yang ditemukan oleh pencacah (baik di dalam target Keluarga maupun di luar target).
-- -------------------------------------------------------------------------
SELECT 
    a.level_2_name AS kabupaten,
    r.jenis_prelist AS sumber_target_awal,
    COUNT(s.assignment_id) AS total_usaha_baru_ditemukan
FROM tgr_fd68e454.base_table_assignment a
JOIN tgr_fd68e454.root_table r
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
JOIN tgr_fd68e454.se2026_nested s
  ON a.assignment_id = s.assignment_id 
  AND a.date_modified = s.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72' 
  AND s.kategori = 'A' -- Merujuk ke Blok A (Keterangan Usaha)
  AND s.keberadaan_usaha_label = '2. Baru'
GROUP BY 
    a.level_2_name,
    r.jenis_prelist
ORDER BY total_usaha_baru_ditemukan DESC;
