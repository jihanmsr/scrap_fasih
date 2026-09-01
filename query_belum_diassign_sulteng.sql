SELECT
    assignment_id,
    kdkab,
    idsubsls,
    code_identity,
    data1,
    assignment_status_alias,
    mode,
    is_active,
    alamat_prelist,
    geotag_latitude,
    geotag_longitude,
    catatan,
    catatan_1,
    catatan_2,
    email_pencacah,
    email_pengawas,
    role,
    link_assignment
FROM (
    SELECT 
        b.assignment_id,
        b.level_2_full_code AS kdkab,
        CONCAT(b.level_5_full_code, b.level_6_code) AS idsubsls,
        b.assignment_status_alias,
        b.code_identity,
        b.data1,
        b.mode,
        b.is_active,
        r.alamat_prelist,
        r.geotag_latitude,
        r.geotag_longitude,
        r.geotag_accuracy,
        r.catatan,
        r.catatan_1,
        r.catatan_2,
        p.email_pencacah, p.email_pengawas,
        p.role,
        CONCAT('https://fasih-sm.bps.go.id/app/assignment/fd68e454-ba45-4b85-8205-f3bf777ded24/', b.assignment_id) AS link_assignment,
        ROW_NUMBER() OVER (
            ORDER BY b.assignment_id ASC
        ) AS rn
    FROM tgr_fd68e454.base_table_assignment b
    LEFT JOIN tgr_fd68e454.root_table r
        ON b.assignment_id = r.assignment_id
    LEFT JOIN (
        WITH responsibility AS (
            SELECT
                assignment_id,
                MAX(CASE WHEN current_survey_rolename = 'Pencacah' THEN current_user_id END) AS pencacah_id,
                MAX(CASE WHEN current_survey_rolename = 'Pengawas' THEN current_user_id END) AS pengawas_id,
                MAX(CASE WHEN current_survey_rolename = 'Pengawas' THEN current_survey_rolename END) AS role
            FROM tgr_fd68e454.base_table_assignment_responsibility
            GROUP BY assignment_id
        )
        SELECT
            u.assignment_id,
            u.role,
            u1.email AS email_pencacah,
            u2.email AS email_pengawas
        FROM responsibility u
        LEFT JOIN (
            SELECT
                user_id,
                MAX(email) AS email
            FROM tgr_fd68e454.base_table_user_allocation_new
            GROUP BY user_id
        ) u1
        ON u.pencacah_id = u1.user_id
        LEFT JOIN (
            SELECT
                user_id,
                MAX(email) AS email
            FROM tgr_fd68e454.base_table_user_allocation_new
            GROUP BY user_id
        ) u2
        ON u.pengawas_id = u2.user_id
    ) p ON b.assignment_id = p.assignment_id
) x
WHERE (email_pencacah IS NULL AND email_pengawas IS NULL AND role IS NULL) AND is_active = 1
ORDER BY rn
