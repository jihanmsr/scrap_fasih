-- =========================================================================
-- QUERY MENDAPATKAN DATA MENTAH 15.164 PRELIST (DARI 760 SUB-SLS FULL OPEN)
-- =========================================================================
-- Karena jumlah totalnya 15.164 (Melebihi limit 9.000 baris SQL Lab), 
-- Anda WAJIB menarik datanya per Kabupaten dengan mengaktifkan (menghapus tanda --)
-- pada baris filter level_2_full_code.

SELECT 
    a.level_2_full_code AS kode_kab,
    a.level_2_name AS kabupaten,
    a.level_3_full_code AS kode_kecamatan,
    a.level_3_name AS kecamatan,
    a.level_4_full_code AS kode_desa,
    a.level_4_name AS desa,
    a.level_5_full_code AS kode_sls,
    a.level_5_name AS sls,
    a.level_6_full_code AS kode_sub_sls,
    a.level_6_name AS sub_sls,
    r.nama_kk AS nama_kepala_keluarga,
    r.nama_usaha_prelist AS nama_usaha,
    a.current_user_fullname AS nama_petugas,
    a.assignment_status_alias AS status_dokumen,
    'Belum Selesai' AS progres_penyelesaian
FROM tgr_fd68e454.base_table_assignment a
LEFT JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72'
  
  -- ================================================================
  -- WAJIB GANTI KODE KABUPATEN DI BAWAH INI SATU PER SATU (7201 s/d 7271)
  -- AGAR HASILNYA TIDAK TERPOTONG LIMIT 9.000 BARIS!
  -- ================================================================
  -- AND a.level_2_full_code = '7201'
  
  -- Filter Sub-SLS yang FULL OPEN (Semua assignment di Sub-SLS tersebut statusnya OPEN)
  AND a.level_6_full_code IN (
      SELECT level_6_full_code
      FROM tgr_fd68e454.base_table_assignment
      WHERE is_active = 1 
        AND level_1_full_code = '72'
      GROUP BY level_6_full_code
      HAVING COUNT(assignment_id) = SUM(CASE WHEN assignment_status_alias = 'OPEN' THEN 1 ELSE 0 END)
  )
ORDER BY 
    a.level_2_full_code, a.level_3_full_code, a.level_4_full_code, a.level_5_full_code;
