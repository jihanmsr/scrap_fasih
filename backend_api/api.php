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

} else {
    echo json_encode(['error' => 'Invalid action']);
}
?>
