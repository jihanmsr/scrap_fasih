-- =========================================================================
-- QUERY REKAPITULASI SUB-SLS FULL OPEN + NAMA PETUGAS
-- =========================================================================
-- Menampilkan rekapitulasi target Sub-SLS yang 100% masih OPEN (belum disentuh).
-- Dilengkapi dengan Nama Petugas (current_user_fullname) untuk masing-masing Sub-SLS.
-- Jika prelist di Sub-SLS tersebut belum di-assign, kolom nama_petugas akan kosong (NULL).
-- Jumlah baris akan sedikit di atas 723 (misal 800-an) jika dalam 1 Sub-SLS ada lebih dari 1 petugas.
-- AMAN ditarik sekaligus se-Sulteng tanpa filter Kabupaten.

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
    level_6_name AS nama_sub_sls,
    current_user_fullname AS nama_petugas,
    COUNT(assignment_id) AS jumlah_prelist
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'

  AND level_6_full_code IN (
      SELECT level_6_full_code
      FROM tgr_fd68e454.base_table_assignment
      WHERE is_active = 1 AND level_1_full_code = '72'
      GROUP BY level_6_full_code
      HAVING COUNT(assignment_id) = SUM(CASE WHEN assignment_status_alias = 'OPEN' THEN 1 ELSE 0 END)
  )
GROUP BY 
    level_2_full_code, level_2_name,
    level_3_full_code, level_3_name,
    level_4_full_code, level_4_name,
    level_5_full_code, level_5_name,
    level_6_full_code, level_6_name,
    current_user_fullname
ORDER BY 
    level_2_full_code, level_3_full_code, level_4_full_code, level_5_full_code;
