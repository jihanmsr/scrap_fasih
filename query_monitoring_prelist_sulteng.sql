-- =========================================================================
-- QUERY MONITORING PRELIST SULTENG (DENGAN KODE, STATUS, DAN PETUGAS)
-- =========================================================================

-- OPSI 1: REKAPITULASI PER SUB-SLS DAN PETUGAS
-- Menampilkan total prelist, berapa yang selesai/belum, dan siapa petugasnya.
-- Jika belum di-assign, nama petugas akan kosong (NULL) dan masuk hitungan belum di-assign.
SELECT 
    level_2_full_code AS kode_kab,
    level_2_name AS kabupaten,
    level_3_full_code AS kode_kecamatan,
    level_3_name AS kecamatan,
    level_4_full_code AS kode_desa,
    level_4_name AS desa,
    level_5_full_code AS kode_sls,
    level_5_name AS sls,
    level_6_full_code AS kode_sub_sls,
    level_6_name AS sub_sls,
    current_user_fullname AS nama_petugas,
    COUNT(assignment_id) AS total_prelist,
    SUM(CASE WHEN assignment_status_alias IN ('SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'SUBMITTED RESPONDENT') THEN 1 ELSE 0 END) AS jumlah_selesai,
    SUM(CASE WHEN assignment_status_alias NOT IN ('SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'SUBMITTED RESPONDENT') THEN 1 ELSE 0 END) AS jumlah_belum_selesai,
    SUM(CASE WHEN current_user_username IS NULL OR current_user_username = '' THEN 1 ELSE 0 END) AS jumlah_belum_diassign
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'
GROUP BY 
    level_2_full_code,
    level_2_name,
    level_3_full_code,
    level_3_name,
    level_4_full_code,
    level_4_name,
    level_5_full_code,
    level_5_name,
    level_6_full_code,
    level_6_name,
    current_user_fullname
ORDER BY 
    level_2_full_code, 
    level_3_full_code, 
    level_4_full_code,
    level_5_full_code;


-- OPSI 2: TARIK DATA MENTAH LENGKAP (LISTING NAMA USAHA / KELUARGA)
-- Menampilkan satu-satu setiap prelist lengkap dengan petugas dan status selesainya.
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
    a.current_user_username AS email_petugas,
    a.assignment_status_alias AS status_dokumen,
    CASE 
        WHEN a.assignment_status_alias IN ('SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'SUBMITTED RESPONDENT') THEN 'Selesai'
        ELSE 'Belum Selesai' 
    END AS progres_penyelesaian
FROM tgr_fd68e454.base_table_assignment a
LEFT JOIN tgr_fd68e454.root_table r 
  ON a.assignment_id = r.assignment_id 
  AND a.date_modified = r.assignment_date_modified
WHERE a.is_active = 1
  AND a.level_1_full_code = '72'
ORDER BY 
    a.level_2_full_code, 
    a.level_3_full_code, 
    a.level_4_full_code, 
    a.level_5_full_code;
