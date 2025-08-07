-- 台中市建照資料庫結構
CREATE DATABASE IF NOT EXISTS taichung_building_permits CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE taichung_building_permits;

-- 建照資料表
CREATE TABLE building_permits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    permit_number VARCHAR(20) NOT NULL UNIQUE COMMENT '建照執照號碼',
    permit_year INT NOT NULL COMMENT '年份',
    permit_type INT NOT NULL COMMENT '類型(1=建照)',
    sequence_number INT NOT NULL COMMENT '編號',
    version_number INT NOT NULL COMMENT '版本號',
    
    -- 申請人資訊
    applicant_name VARCHAR(100) COMMENT '起造人姓名',
    
    -- 設計人資訊
    designer_name VARCHAR(100) COMMENT '設計人姓名',
    designer_company VARCHAR(200) COMMENT '設計人事務所',
    
    -- 監造人資訊
    supervisor_name VARCHAR(100) COMMENT '監造人姓名',
    supervisor_company VARCHAR(200) COMMENT '監造人事務所',
    
    -- 承造人資訊
    contractor_name VARCHAR(100) COMMENT '承造人姓名',
    contractor_company VARCHAR(200) COMMENT '承造廠商',
    
    -- 專任工程人員
    engineer_name VARCHAR(100) COMMENT '專任工程人員',
    
    -- 基地資訊
    site_address TEXT COMMENT '基地地址',
    site_city VARCHAR(50) COMMENT '地址城市',
    site_zone VARCHAR(100) COMMENT '使用分區',
    site_area DECIMAL(10,2) COMMENT '基地面積(平方公尺)',
    
    -- 系統欄位
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '爬取時間',
    
    INDEX idx_permit_number (permit_number),
    INDEX idx_year_sequence (permit_year, sequence_number),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='台中市建照資料表';

-- 爬蟲執行記錄表
CREATE TABLE crawl_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crawl_date DATE NOT NULL COMMENT '爬取日期',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '開始時間',
    end_time TIMESTAMP NULL COMMENT '結束時間',
    total_records INT DEFAULT 0 COMMENT '總爬取筆數',
    new_records INT DEFAULT 0 COMMENT '新增筆數',
    error_records INT DEFAULT 0 COMMENT '錯誤筆數',
    status ENUM('running', 'completed', 'failed') DEFAULT 'running' COMMENT '執行狀態',
    error_message TEXT COMMENT '錯誤訊息',
    
    UNIQUE KEY unique_crawl_date (crawl_date),
    INDEX idx_status (status),
    INDEX idx_crawl_date (crawl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='爬蟲執行記錄表';