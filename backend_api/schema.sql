CREATE TABLE dashboard_store (
    `key` VARCHAR(255) PRIMARY KEY,
    `value` LONGTEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE anomali_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kab_code VARCHAR(100),
    kec_code VARCHAR(100),
    desa_code VARCHAR(100),
    sls_code VARCHAR(100),
    nama_petugas VARCHAR(255),
    jenis_anomali VARCHAR(255),
    nama_krt VARCHAR(255),
    catatan TEXT,
    tindak_lanjut TEXT,
    status_anomali INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignment_id VARCHAR(255),
    total_pengeluaran BIGINT,
    biaya_produksi BIGINT,
    pct_biaya FLOAT,
    waktu_anomali TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (assignment_id, jenis_anomali)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(255),
    name VARCHAR(255),
    kab_name VARCHAR(255),
    kabupaten VARCHAR(255),
    kecamatan VARCHAR(255),
    desa VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(255),
    survey_status VARCHAR(255),
    status VARCHAR(255),
    timestamp VARCHAR(255),
    `order` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'Administrator', 'admin');

CREATE TABLE granular_targets (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
