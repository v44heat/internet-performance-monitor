-- schema.sql
-- ==========
-- SQLite schema for Internet Performance Monitor Pro.
-- Stores every completed speed/quality test along with derived
-- network/ISP metadata and the computed internet health score.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS test_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime         TEXT    NOT NULL,              -- ISO-8601 timestamp
    download_speed   REAL    NOT NULL DEFAULT 0,    -- Mbps
    upload_speed     REAL    NOT NULL DEFAULT 0,    -- Mbps
    ping             REAL    NOT NULL DEFAULT 0,    -- ms
    jitter           REAL    NOT NULL DEFAULT 0,    -- ms
    packet_loss      REAL    NOT NULL DEFAULT 0,    -- %
    isp              TEXT,
    server           TEXT,
    city             TEXT,
    country          TEXT,
    ip_address       TEXT,
    network_type     TEXT,
    internet_score   REAL    NOT NULL DEFAULT 0     -- 0-100
);

CREATE INDEX IF NOT EXISTS idx_test_results_datetime
    ON test_results (datetime);

CREATE INDEX IF NOT EXISTS idx_test_results_isp
    ON test_results (isp);

CREATE TABLE IF NOT EXISTS app_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime    TEXT NOT NULL,
    level       TEXT NOT NULL,      -- INFO, WARNING, ERROR
    category    TEXT NOT NULL,      -- monitoring, export, database, notification
    message     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_events_datetime
    ON app_events (datetime);
