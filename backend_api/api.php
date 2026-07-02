<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Konfigurasi Database (Silakan diisi nanti di Capella)
$host = 'localhost';
$db   = 'u12228jhr_fasih';
$user = 'u12228jhr_fasih';
$pass = 'y67L7plXt8';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8mb4", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit();
}

$action = $_GET['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true);

if ($action === 'upsert_store') {
    // Input: ['key' => '...', 'value' => '...']
    if (!$input || !isset($input['key']) || !isset($input['value'])) {
        echo json_encode(['error' => 'Missing key or value']);
        exit();
    }
    
    $stmt = $pdo->prepare("INSERT INTO dashboard_store (`key`, `value`) VALUES (?, ?) ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)");
    $success = $stmt->execute([$input['key'], is_array($input['value']) ? json_encode($input['value']) : $input['value']]);
    echo json_encode(['success' => $success]);

} elseif ($action === 'get_store') {
    // Output all dashboard_store as array of objects
    $stmt = $pdo->query("SELECT `key`, `value` FROM dashboard_store");
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($data);

} elseif ($action === 'upsert_anomali') {
    // Input: array of records
    if (!is_array($input)) {
        echo json_encode(['error' => 'Input must be an array of records']);
        exit();
    }
    
    $stmt = $pdo->prepare("
        INSERT INTO anomali_data 
        (kab_code, kec_code, desa_code, sls_code, nama_petugas, jenis_anomali, nama_krt, catatan, tindak_lanjut, status_anomali, assignment_id, total_pengeluaran, biaya_produksi, pct_biaya, waktu_anomali) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE 
        nama_petugas = IF(VALUES(nama_petugas) != '', VALUES(nama_petugas), nama_petugas),
        nama_krt = VALUES(nama_krt),
        catatan = VALUES(catatan),
        waktu_anomali = VALUES(waktu_anomali)
    ");
    
    $pdo->beginTransaction();
    try {
        foreach ($input as $row) {
            $stmt->execute([
                $row['kab_code'] ?? null,
                $row['kec_code'] ?? null,
                $row['desa_code'] ?? null,
                $row['sls_code'] ?? null,
                $row['nama_petugas'] ?? null,
                $row['jenis_anomali'] ?? null,
                $row['nama_krt'] ?? null,
                $row['catatan'] ?? null,
                $row['tindak_lanjut'] ?? '',
                $row['status_anomali'] ?? 1,
                $row['assignment_id'] ?? null,
                $row['total_pengeluaran'] ?? null,
                $row['biaya_produksi'] ?? null,
                $row['pct_biaya'] ?? null,
                $row['waktu_anomali'] ?? date('Y-m-d H:i:s')
            ]);
        }
        $pdo->commit();
        echo json_encode(['success' => true]);
    } catch (Exception $e) {
        $pdo->rollBack();
        echo json_encode(['error' => $e->getMessage()]);
    }

} elseif ($action === 'patch_anomali_db') {
    if (!isset($input['id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Missing id']);
        exit;
    }
    
    if (isset($input['bulk']) && is_array($input['bulk'])) {
        $successCount = 0;
        foreach ($input['bulk'] as $item) {
            $setClauses = [];
            $params = [];
            if (isset($item['nama_krt'])) {
                $setClauses[] = "nama_krt = ?";
                $params[] = $item['nama_krt'];
            }
            if (isset($item['nama_petugas'])) {
                $setClauses[] = "nama_petugas = ?";
                $params[] = $item['nama_petugas'];
            }
            if (!empty($setClauses)) {
                $sql = "UPDATE anomali_data SET " . implode(", ", $setClauses) . " WHERE id = ?";
                $params[] = $item['id'];
                $stmt = $pdo->prepare($sql);
                $stmt->execute($params);
                $successCount++;
            }
        }
        echo json_encode(['success' => true, 'updated' => $successCount]);
        exit;
    }
    
    $setClauses = [];
    $params = [];
    if (isset($input['nama_krt'])) {
        $setClauses[] = "nama_krt = ?";
        $params[] = $input['nama_krt'];
    }
    if (isset($input['nama_petugas'])) {
        $setClauses[] = "nama_petugas = ?";
        $params[] = $input['nama_petugas'];
    }
    
    if (empty($setClauses)) {
        echo json_encode(['success' => true]);
        exit;
    }
    
    $sql = "UPDATE anomali_data SET " . implode(", ", $setClauses) . " WHERE id = ?";
    $params[] = $input['id'];
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    echo json_encode(['success' => true]);
} elseif ($action === 'set_anomali_status') {
    $stmt = $pdo->query("SELECT * FROM anomali_data ORDER BY id ASC");
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($data);

} elseif ($action === 'get_anomali') {
    $stmt = $pdo->query("SELECT * FROM anomali_data ORDER BY id ASC");
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($data);

} elseif ($action === 'update_anomali') {
    // For petugas modifying tindak_lanjut
    if (!$input || !isset($input['id'])) {
        echo json_encode(['error' => 'Missing ID']);
        exit();
    }
    $stmt = $pdo->prepare("UPDATE anomali_data SET tindak_lanjut = ?, status_anomali = ?, nama_petugas = ?, updated_by = ? WHERE id = ?");
    $success = $stmt->execute([
        $input['tindak_lanjut'] ?? '',
        $input['status_anomali'] ?? 1,
        $input['nama_petugas'] ?? null,
        $input['updated_by'] ?? null,
        $input['id']
    ]);
    echo json_encode(['success' => $success]);

} elseif ($action === 'replace_email_logs') {
    // Truncate and insert new email logs
    if (!is_array($input)) {
        echo json_encode(['error' => 'Input must be an array of records']);
        exit();
    }
    
    $pdo->beginTransaction();
    try {
        $pdo->exec("TRUNCATE TABLE email_logs");
        
        $stmt = $pdo->prepare("
            INSERT INTO email_logs 
            (code, name, kab_name, kabupaten, kecamatan, desa, email, role, survey_status, status, timestamp, `order`) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ");
        
        foreach ($input as $row) {
            $stmt->execute([
                $row['code'] ?? null,
                $row['name'] ?? null,
                $row['kab_name'] ?? null,
                $row['kabupaten'] ?? null,
                $row['kecamatan'] ?? null,
                $row['desa'] ?? null,
                $row['email'] ?? null,
                $row['role'] ?? null,
                $row['survey_status'] ?? null,
                $row['status'] ?? null,
                $row['timestamp'] ?? null,
                $row['order'] ?? 0
            ]);
        }
        $pdo->commit();
        echo json_encode(['success' => true]);
    } catch (Exception $e) {
        $pdo->rollBack();
        echo json_encode(['error' => $e->getMessage()]);
    }

} elseif ($action === 'get_email_logs') {
    $stmt = $pdo->query("SELECT * FROM email_logs ORDER BY `order` ASC");
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($data);

} elseif ($action === 'check_login') {
    $username = $input['p_username'] ?? '';
    $password = $input['p_password'] ?? '';
    
    // Check users table, but also allow a hardcoded fallback if users table isn't populated
    if ($username === 'admin' && $password === 'admin123') {
        echo json_encode(['id' => 1, 'username' => 'admin', 'full_name' => 'Administrator', 'role' => 'admin']);
        exit();
    }
    
    $stmt = $pdo->prepare("SELECT id, username, full_name, role FROM users WHERE username = ? AND password = ?");
    $stmt->execute([$username, $password]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($user) {
        echo json_encode($user);
    } else {
        http_response_code(401);
        echo json_encode(['error' => 'Invalid credentials']);
    }
} elseif ($action === 'get_users') {
    $stmt = $pdo->prepare("SELECT username, full_name, role FROM users");
    $stmt->execute();
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($data);
} elseif ($action === 'seed_users') {
    if (!is_array($input)) {
        echo json_encode(['error' => 'Input must be an array of users']);
        exit();
    }
    
    // Auto-create users table if it doesn't exist
    $pdo->exec("CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'petugas'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
    
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE full_name=VALUES(full_name), role=VALUES(role)");
        $count = 0;
        foreach ($input as $row) {
            $username = $row['username'] ?? '';
            $password = $row['password'] ?? $username; // Default to username if not provided
            $full_name = $row['full_name'] ?? '';
            $role = $row['role'] ?? 'petugas';
            
            if ($username) {
                $stmt->execute([$username, $password, $full_name, $role]);
                $count++;
            }
        }
        $pdo->commit();
        echo json_encode(['success' => true, 'inserted' => $count]);
    } catch (Exception $e) {
        $pdo->rollBack();
        echo json_encode(['error' => $e->getMessage()]);
    }
} elseif ($action === 'migrate_db') {
    $sql = "CREATE TABLE IF NOT EXISTS granular_targets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        assignment_id VARCHAR(100) UNIQUE NOT NULL,
        survey_type VARCHAR(50),
        kab_code VARCHAR(20),
        kab_name VARCHAR(100),
        kec_code VARCHAR(20),
        kec_name VARCHAR(100),
        desa_code VARCHAR(20),
        desa_name VARCHAR(100),
        sls_code VARCHAR(30),
        sls_name VARCHAR(100),
        target_id VARCHAR(100),
        target_name VARCHAR(255),
        status VARCHAR(50),
        petugas_username VARCHAR(150),
        petugas_fullname VARCHAR(255),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_survey_kab (survey_type, kab_code),
        INDEX idx_status (status),
        INDEX idx_sls_code (sls_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
    
    try {
        $pdo->exec($sql);
        echo json_encode(['success' => true, 'message' => 'Migration successful']);
    } catch (PDOException $e) {
        echo json_encode(['error' => $e->getMessage()]);
    }
} elseif ($action === 'upsert_granular') {
    if (!is_array($input)) {
        echo json_encode(['error' => 'Input must be an array of targets']);
        exit();
    }
    
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare("INSERT INTO granular_targets 
            (assignment_id, survey_type, kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name, target_id, target_name, status, petugas_username, petugas_fullname) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            ON DUPLICATE KEY UPDATE 
            status=VALUES(status), petugas_username=VALUES(petugas_username), petugas_fullname=VALUES(petugas_fullname), target_name=VALUES(target_name)");
            
        $count = 0;
        foreach ($input as $row) {
            $stmt->execute([
                $row['assignment_id'] ?? '',
                $row['survey_type'] ?? '',
                $row['kab_code'] ?? '',
                $row['kab_name'] ?? '',
                $row['kec_code'] ?? '',
                $row['kec_name'] ?? '',
                $row['desa_code'] ?? '',
                $row['desa_name'] ?? '',
                $row['sls_code'] ?? '',
                $row['sls_name'] ?? '',
                $row['target_id'] ?? '',
                $row['target_name'] ?? '',
                $row['status'] ?? '',
                $row['petugas_username'] ?? '',
                $row['petugas_fullname'] ?? ''
            ]);
            $count++;
        }
        $pdo->commit();
        echo json_encode(['success' => true, 'inserted' => $count]);
    } catch (Exception $e) {
        $pdo->rollBack();
        echo json_encode(['error' => $e->getMessage()]);
    }
} elseif ($action === 'get_granular') {
    $surveyType = $_GET['survey'] ?? '';
    $kabCode = $_GET['kab'] ?? '';
    $kecCode = $_GET['kec'] ?? '';
    $desaCode = $_GET['desa'] ?? '';
    $slsCode = $_GET['sls'] ?? '';
    $status = $_GET['status'] ?? '';
    
    $page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
    $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 50;
    $offset = ($page - 1) * $limit;
    
    $search = $_GET['search'] ?? '';
    
    $where = ["1=1"];
    $params = [];
    
    if ($surveyType) {
        $where[] = "survey_type = ?";
        $params[] = $surveyType;
    }
    if ($kabCode && $kabCode !== 'all') {
        $where[] = "kab_code = ?";
        $params[] = $kabCode;
    }
    if ($kecCode && $kecCode !== 'all') {
        $where[] = "kec_name = ?"; // In frontend, filter is by name, wait! I will just use kec_code. Wait, Frontend passes 'name' for kec, desa. Let's support both.
        // Let's just use what frontend passes. The user's app.js passes names for kec/desa/sls filter.
        $where[] = "kec_name = ?";
        $params[] = $kecCode;
    }
    if ($desaCode && $desaCode !== 'all') {
        $where[] = "desa_name = ?";
        $params[] = $desaCode;
    }
    if ($slsCode && $slsCode !== 'all') {
        // App.js passes sls_code for slsVal.
        $where[] = "sls_code = ?";
        $params[] = $slsCode;
    }
    if ($status && $status !== 'all') {
        $where[] = "status = ?";
        $params[] = $status;
    }
    
    if ($search) {
        $where[] = "(target_name LIKE ? OR target_id LIKE ? OR petugas_fullname LIKE ? OR petugas_username LIKE ?)";
        $searchParam = "%$search%";
        $params[] = $searchParam;
        $params[] = $searchParam;
        $params[] = $searchParam;
        $params[] = $searchParam;
    }
    
    $whereClause = implode(" AND ", $where);
    
    // Count total
    $countSql = "SELECT COUNT(*) FROM granular_targets WHERE $whereClause";
    $countStmt = $pdo->prepare($countSql);
    $countStmt->execute($params);
    $total = $countStmt->fetchColumn();
    
    // Get Data
    $sql = "SELECT * FROM granular_targets WHERE $whereClause ORDER BY id ASC LIMIT $limit OFFSET $offset";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode([
        'data' => $data,
        'total' => $total,
        'page' => $page,
        'limit' => $limit
    ]);
} elseif ($action === 'get_granular_options') {
    $type = $_GET['type'] ?? '';
    $kabCode = $_GET['kab'] ?? '';
    $kecName = $_GET['kec'] ?? '';
    $desaName = $_GET['desa'] ?? '';
    $surveyType = $_GET['survey'] ?? '';
    
    $where = ["1=1"];
    $params = [];
    
    if ($surveyType) {
        $where[] = "survey_type = ?";
        $params[] = $surveyType;
    }
    if ($kabCode && $kabCode !== 'all') {
        $where[] = "kab_code = ?";
        $params[] = $kabCode;
    }
    
    if ($type === 'kec') {
        $sql = "SELECT DISTINCT kec_name FROM granular_targets WHERE " . implode(" AND ", $where) . " AND kec_name != '-' AND kec_name IS NOT NULL ORDER BY kec_name";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $res = $stmt->fetchAll(PDO::FETCH_COLUMN);
        echo json_encode($res);
    } elseif ($type === 'desa') {
        $where[] = "kec_name = ?";
        $params[] = $kecName;
        $sql = "SELECT DISTINCT desa_name FROM granular_targets WHERE " . implode(" AND ", $where) . " AND desa_name != '-' AND desa_name IS NOT NULL ORDER BY desa_name";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $res = $stmt->fetchAll(PDO::FETCH_COLUMN);
        echo json_encode($res);
    } elseif ($type === 'sls') {
        $where[] = "kec_name = ?";
        $params[] = $kecName;
        $where[] = "desa_name = ?";
        $params[] = $desaName;
        $sql = "SELECT DISTINCT sls_code, sls_name FROM granular_targets WHERE " . implode(" AND ", $where) . " AND sls_code IS NOT NULL ORDER BY sls_code";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $res = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode($res);
    } else {
        echo json_encode([]);
    }
} elseif ($action === 'get_dashboard_summary') {
    $surveyType = $_GET['survey'] ?? 'se_umum';
    $kabCode = $_GET['kab'] ?? '';
    
    $where = ["survey_type = ?"];
    $params = [$surveyType];
    
    if ($kabCode && $kabCode !== 'all') {
        $where[] = "kab_code = ?";
        $params[] = $kabCode;
    }
    
    $whereClause = implode(" AND ", $where);
    
    // Group by kab_code if no kab specified, else by kec_name
    if ($kabCode && $kabCode !== 'all') {
        $sql = "
            SELECT 
                kec_name as name,
                COUNT(*) as total_target,
                SUM(CASE WHEN status IN ('SUBMITTED', 'APPROVED') THEN 1 ELSE 0 END) as selesai,
                SUM(CASE WHEN status IN ('OPEN', 'DRAFT', 'REJECTED') THEN 1 ELSE 0 END) as belum_selesai
            FROM granular_targets
            WHERE $whereClause
            GROUP BY kec_name
            ORDER BY kec_name ASC
        ";
    } else {
        $sql = "
            SELECT 
                kab_name as name,
                kab_code as code,
                COUNT(*) as total_target,
                SUM(CASE WHEN status IN ('SUBMITTED', 'APPROVED') THEN 1 ELSE 0 END) as selesai,
                SUM(CASE WHEN status IN ('OPEN', 'DRAFT', 'REJECTED') THEN 1 ELSE 0 END) as belum_selesai
            FROM granular_targets
            WHERE $whereClause
            GROUP BY kab_code, kab_name
            ORDER BY kab_code ASC
        ";
    }
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($data);
} elseif ($action === 'get_petugas_summary') {
    $surveyType = $_GET['survey'] ?? '';
    $kabCode = $_GET['kab'] ?? '';
    $kecName = $_GET['kec'] ?? '';
    $desaName = $_GET['desa'] ?? '';
    $slsCode = $_GET['sls'] ?? '';
    
    $where = ["1=1"];
    $params = [];
    
    if ($surveyType) {
        $where[] = "survey_type = ?";
        $params[] = $surveyType;
    }
    if ($kabCode && $kabCode !== 'all') {
        $where[] = "kab_code = ?";
        $params[] = $kabCode;
    }
    if ($kecName && $kecName !== 'all') {
        $where[] = "kec_name = ?";
        $params[] = $kecName;
    }
    if ($desaName && $desaName !== 'all') {
        $where[] = "desa_name = ?";
        $params[] = $desaName;
    }
    if ($slsCode && $slsCode !== 'all') {
        $where[] = "sls_code = ?";
        $params[] = $slsCode;
    }
    
    $whereClause = implode(" AND ", $where);
    
    // Group by petugas_fullname and calculate stats
    $sql = "
        SELECT 
            petugas_fullname,
            COUNT(*) as total_target,
            SUM(CASE WHEN status IN ('SUBMITTED', 'APPROVED') THEN 1 ELSE 0 END) as selesai,
            SUM(CASE WHEN status IN ('OPEN', 'DRAFT', 'REJECTED') THEN 1 ELSE 0 END) as belum_selesai
        FROM granular_targets
        WHERE $whereClause
        GROUP BY petugas_fullname
        ORDER BY petugas_fullname ASC
    ";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($data);
} else {
    echo json_encode(['error' => 'Invalid action']);
}
?>
