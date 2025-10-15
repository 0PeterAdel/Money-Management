-- Database Migration for Enhanced Auth System
-- Run with: sqlite3 ../../assistant.db < migrate_db.sql

-- Backup reminder
.print '================================================'
.print 'Enhanced Auth System Database Migration'
.print '================================================'
.print ''
.print 'IMPORTANT: Backup your database first!'
.print 'Run: cp ../../assistant.db ../../assistant.db.backup'
.print ''

-- Start transaction
BEGIN TRANSACTION;

-- Add new columns to users table (if they don't exist)
-- Note: SQLite doesn't have ALTER COLUMN, so we check existence first

-- Add username column
ALTER TABLE users ADD COLUMN username VARCHAR(50);

-- Add email column  
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- Add role column
ALTER TABLE users ADD COLUMN role VARCHAR(10) DEFAULT 'user';

-- Add is_active column
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 0;

-- Add is_banned column
ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0;

-- Add updated_at column
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP;

-- Add last_login column
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- Update existing users with default values
UPDATE users 
SET username = name,
    email = id || '@temp.local',
    is_active = 1,
    role = 'user'
WHERE username IS NULL;

-- Create OTP codes table
CREATE TABLE IF NOT EXISTS otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    code VARCHAR(6) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create user sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create system config table
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
    ('otp_method', 'disabled', 'OTP delivery method: disabled, telegram, or email'),
    ('otp_expiry_minutes', '5', 'OTP code expiration time in minutes');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_otp_codes_user_id ON otp_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key);

-- Commit transaction
COMMIT;

-- Display results
.print ''
.print '================================================'
.print 'Migration Complete!'
.print '================================================'
.print ''
.print 'Tables created/updated:'
.tables

.print ''
.print 'Users table structure:'
.schema users

.print ''
.print 'System configuration:'
SELECT * FROM system_config;

.print ''
.print 'Migration successful! ✅'
.print ''
