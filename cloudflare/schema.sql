-- Cloudflare D1 資料庫結構
-- 建照資料表
CREATE TABLE building_permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_number TEXT NOT NULL UNIQUE,
    permit_year INTEGER NOT NULL,
    permit_type INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    
    -- 申請人資訊
    applicant_name TEXT,
    
    -- 設計人資訊
    designer_name TEXT,
    designer_company TEXT,
    
    -- 監造人資訊
    supervisor_name TEXT,
    supervisor_company TEXT,
    
    -- 承造人資訊
    contractor_name TEXT,
    contractor_company TEXT,
    
    -- 專任工程人員
    engineer_name TEXT,
    
    -- 基地資訊
    site_address TEXT,
    site_city TEXT,
    site_zone TEXT,
    site_area REAL,
    
    -- 系統欄位
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_permit_number ON building_permits(permit_number);
CREATE INDEX idx_year_sequence ON building_permits(permit_year, sequence_number);
CREATE INDEX idx_created_at ON building_permits(created_at);

-- 爬蟲執行記錄表
CREATE TABLE crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_date DATE NOT NULL UNIQUE,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    total_records INTEGER DEFAULT 0,
    new_records INTEGER DEFAULT 0,
    error_records INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT
);

CREATE INDEX idx_crawl_date ON crawl_logs(crawl_date);
CREATE INDEX idx_status ON crawl_logs(status);