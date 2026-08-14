-- =========================================================================
-- QUERY REKAPITULASI SUB-SLS FULL OPEN (723 SUB-SLS)
-- =========================================================================
-- Karena ini berupa rekapitulasi (jumlah baris sekitar 723), 
-- AMAN untuk ditarik sekaligus se-Sulawesi Tengah tanpa filter Kabupaten.

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
    COUNT(assignment_id) AS jumlah_prelist
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'
GROUP BY 
    level_2_full_code, level_2_name,
    level_3_full_code, level_3_name,
    level_4_full_code, level_4_name,
    level_5_full_code, level_5_name,
    level_6_full_code, level_6_name
-- Filter: hanya munculkan Sub-SLS yang SEMUA prelist-nya masih berstatus OPEN
HAVING COUNT(assignment_id) = SUM(CASE WHEN assignment_status_alias = 'OPEN' THEN 1 ELSE 0 END)
ORDER BY 
    level_2_full_code, level_3_full_code, level_4_full_code, level_5_full_code;
