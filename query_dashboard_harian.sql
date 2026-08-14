SELECT 
    level_2_full_code AS kode_kab,
    level_2_name AS nama_kab,
    level_3_full_code AS kode_kec,
    level_3_name AS nama_kec,
    COUNT(assignment_id) AS total_prelist,
    SUM(CASE WHEN assignment_status_alias = 'OPEN' THEN 1 ELSE 0 END) AS total_open,
    SUM(CASE WHEN assignment_status_alias = 'DRAFT' THEN 1 ELSE 0 END) AS total_draft,
    SUM(CASE WHEN assignment_status_alias LIKE '%SUBMITTED%' THEN 1 ELSE 0 END) AS total_submitted,
    SUM(CASE WHEN assignment_status_alias = 'APPROVED' THEN 1 ELSE 0 END) AS total_approved,
    SUM(CASE WHEN assignment_status_alias = 'REJECTED' THEN 1 ELSE 0 END) AS total_rejected,
    SUM(CASE WHEN assignment_status_alias = 'SUBMITTED_PENCACAH' OR assignment_status_alias = 'SUBMITTED' THEN 1 ELSE 0 END) AS total_submitted_pencacah,
    SUM(CASE WHEN assignment_status_alias = 'SUBMITTED_RESPONDENT' THEN 1 ELSE 0 END) AS total_submitted_respondent
FROM tgr_fd68e454.base_table_assignment
WHERE is_active = 1 
  AND level_1_full_code = '72'
GROUP BY 
    level_2_full_code, 
    level_2_name,
    level_3_full_code,
    level_3_name
ORDER BY 
    level_2_full_code ASC, 
    level_3_full_code ASC;
