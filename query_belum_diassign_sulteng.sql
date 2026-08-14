-- =========================================================================
-- QUERY MENDAPATKAN DAFTAR PRELIST YANG BELUM DI-ASSIGN KE PETUGAS
-- =========================================================================

-- OPSI 1: REKAPITULASI JUMLAH PRELIST BELUM DI-ASSIGN PER SUB-SLS
SELECT 
    level_2_full_code AS kode_kab,
    level_2_name AS kabupaten,
    level_3_name AS kecamatan,
    level_4_name AS desa,
    level_5_name AS sls,
    level_6_full_code AS kode_sub_sls,
    level_6_name AS nama_sub_sls,
    COUNT(assignment_id) AS jumlah_prelist_belum_diassign
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'
  -- Filter prelist yang belum memiliki petugas:
  AND (current_user_username IS NULL OR current_user_username = '')
GROUP BY 
    level_2_full_code,
    level_2_name,
    level_3_name,
    level_4_name,
    level_5_name,
    level_6_full_code,
    level_6_name
ORDER BY 
    level_2_full_code, 
    level_3_name, 
    level_4_name,
    level_5_name;


-- OPSI 2: TARIK DATA MENTAH (NAMA-NAMA PRELIST) YANG BELUM DI-ASSIGN
-- Menampilkan list data usaha/keluarga yang masih kosong petugasnya
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
    a.assignment_status_alias AS status_dokumen
FROM tgr_fd68e454.base_table_assignment a
LEFT JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72'
  -- Filter prelist yang belum memiliki petugas:
  AND (a.current_user_username IS NULL OR a.current_user_username = '')
ORDER BY a.level_2_full_code, a.level_3_name, a.level_4_name, a.level_5_name;
