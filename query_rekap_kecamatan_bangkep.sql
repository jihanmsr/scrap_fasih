-- =========================================================================
-- QUERY REKAP SBR, UTP, KELUARGA (LEVEL KECAMATAN) - KHUSUS BANGGAI KEPULAUAN (7201)
-- =========================================================================

SELECT
    s.level_2_full_code AS kode_kab,
    s.level_3_full_code AS kode_kecamatan,
    s.nama_kecamatan,
    s.total_sbr,
    s.total_utp,
    a.total_keluarga
FROM (
    SELECT
        level_2_full_code,
        level_3_full_code,
        level_3_name AS nama_kecamatan,
        COUNT(CASE WHEN kategori != 'A' THEN 1 END) AS total_sbr,
        COUNT(CASE WHEN kategori = 'A' THEN 1 END) AS total_utp
    FROM tgr_fd68e454.se2026_nested
    WHERE level_2_full_code = '7201'
    GROUP BY level_2_full_code, level_3_full_code, level_3_name
) s
LEFT JOIN (
    SELECT
        level_2_full_code,
        level_3_full_code,
        COUNT(CASE WHEN ada_keluarga_value IN ('1','2') THEN 1 END) as total_keluarga
    FROM tgr_fd68e454.root_table 
    WHERE level_2_full_code = '7201'
    GROUP BY level_2_full_code, level_3_full_code
) a
    ON s.level_3_full_code = a.level_3_full_code
ORDER BY s.kode_kecamatan ASC;
