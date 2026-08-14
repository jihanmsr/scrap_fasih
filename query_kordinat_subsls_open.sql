-- =========================================================================
-- QUERY KOORDINAT SUB-SLS FULL OPEN (Untuk Mapping Peta Titik)
-- =========================================================================
SELECT 
    level_2_name AS kabupaten,
    level_3_name AS kecamatan,
    level_4_name AS desa,
    level_6_full_code AS kode_sub_sls,
    level_6_name AS nama_sub_sls,
    COUNT(assignment_id) AS jumlah_prelist,
    MAX(latitude) AS latitude,
    MAX(longitude) AS longitude
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'
GROUP BY 
    level_2_name,
    level_3_name,
    level_4_name,
    level_6_full_code, 
    level_6_name
HAVING COUNT(assignment_id) = SUM(CASE WHEN assignment_status_alias = 'OPEN' THEN 1 ELSE 0 END)
ORDER BY level_6_full_code;
