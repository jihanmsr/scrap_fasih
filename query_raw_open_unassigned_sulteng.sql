-- =========================================================================
-- QUERY TARIK DATA MENTAH: KHUSUS STATUS OPEN & BELUM DI-ASSIGN
-- =========================================================================
-- Karena difilter khusus yang OPEN dan belum di-assign, datanya akan sedikit 
-- dan AMAN dari limit 9.000 baris SQL Lab.

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
  -- Filter khusus yang belum ada petugasnya
  AND (a.current_user_username IS NULL OR a.current_user_username = '')
ORDER BY 
    a.level_2_full_code, 
    a.level_3_full_code, 
    a.level_4_full_code, 
    a.level_5_full_code;
