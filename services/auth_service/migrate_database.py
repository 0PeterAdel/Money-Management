#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Auth System
Run with: python migrate_database.py
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database path (adjust if needed)
DB_PATH = Path(__file__).parent.parent.parent / "assistant.db"
BACKUP_PATH = Path(__file__).parent.parent.parent / f"assistant.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def get_table_columns(cursor, table_name):
    """Get list of columns for a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def column_exists(cursor, table_name, column_name):
    """Check if column exists in table"""
    columns = get_table_columns(cursor, table_name)
    return column_name in columns

def table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def migrate_database():
    """Run database migration"""
    
    print_header("Enhanced Auth System - Database Migration")
    
    # Check if database exists
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print("Creating new database...")
        # Create directory if needed
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup
    print(f"📦 Creating backup...")
    if DB_PATH.exists():
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Backup created: {BACKUP_PATH}")
    
    # Connect to database
    print(f"\n📊 Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        print_header("Step 1: Update Users Table")
        
        # Check if users table exists
        if not table_exists(cursor, 'users'):
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    hashed_password VARCHAR(255),
                    telegram_id INTEGER UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Users table created")
        
        # Add new columns if they don't exist
        columns_to_add = {
            'username': 'VARCHAR(50)',
            'email': 'VARCHAR(255)',
            'role': "VARCHAR(10) DEFAULT 'user'",
            'is_active': 'BOOLEAN DEFAULT 0',
            'is_banned': 'BOOLEAN DEFAULT 0',
            'updated_at': 'TIMESTAMP',
            'last_login': 'TIMESTAMP'
        }
        
        for column, column_type in columns_to_add.items():
            if not column_exists(cursor, 'users', column):
                print(f"  Adding column: {column}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {column_type}")
                print(f"  ✅ {column} added")
            else:
                print(f"  ⊘ {column} already exists")
        
        # Update existing users with default values
        print("\n  Updating existing users with default values...")
        cursor.execute("""
            UPDATE users 
            SET username = COALESCE(username, name),
                email = COALESCE(email, id || '@temp.local'),
                is_active = COALESCE(is_active, 1),
                role = COALESCE(role, 'user')
            WHERE username IS NULL OR email IS NULL
        """)
        print(f"  ✅ Updated {cursor.rowcount} user records")
        
        print_header("Step 2: Create OTP Codes Table")
        
        if not table_exists(cursor, 'otp_codes'):
            cursor.execute("""
                CREATE TABLE otp_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code VARCHAR(6) NOT NULL,
                    purpose VARCHAR(50) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            print("✅ OTP codes table created")
        else:
            print("⊘ OTP codes table already exists")
        
        print_header("Step 3: Create User Sessions Table")
        
        if not table_exists(cursor, 'user_sessions'):
            cursor.execute("""
                CREATE TABLE user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    refresh_token VARCHAR(500) UNIQUE NOT NULL,
                    device_info VARCHAR(255),
                    ip_address VARCHAR(45),
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            print("✅ User sessions table created")
        else:
            print("⊘ User sessions table already exists")
        
        print_header("Step 4: Create System Config Table")
        
        if not table_exists(cursor, 'system_config'):
            cursor.execute("""
                CREATE TABLE system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ System config table created")
            
            # Insert default configuration
            cursor.execute("""
                INSERT INTO system_config (key, value, description) VALUES
                    ('otp_method', 'disabled', 'OTP delivery method: disabled, telegram, or email'),
                    ('otp_expiry_minutes', '5', 'OTP code expiration time in minutes')
            """)
            print("✅ Default system configuration inserted")
        else:
            print("⊘ System config table already exists")
            # Update default values if they don't exist
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value, description) VALUES ('otp_method', 'disabled', 'OTP delivery method')")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value, description) VALUES ('otp_expiry_minutes', '5', 'OTP expiration time')")
        
        print_header("Step 5: Create Indexes")
        
        indexes = {
            'idx_users_username': 'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
            'idx_users_email': 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'idx_users_telegram_id': 'CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)',
            'idx_otp_codes_user_id': 'CREATE INDEX IF NOT EXISTS idx_otp_codes_user_id ON otp_codes(user_id)',
            'idx_otp_codes_expires': 'CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at)',
            'idx_user_sessions_user_id': 'CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)',
            'idx_user_sessions_token': 'CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token)',
            'idx_system_config_key': 'CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key)'
        }
        
        for index_name, sql in indexes.items():
            cursor.execute(sql)
            print(f"  ✅ {index_name}")
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        print_header("Migration Summary")
        
        # Display table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print("📋 Database Tables:")
        for table in tables:
            print(f"  • {table[0]}")
        
        # Display user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Total Users: {user_count}")
        
        # Display system config
        cursor.execute("SELECT key, value FROM system_config")
        configs = cursor.fetchall()
        print(f"\n⚙️  System Configuration:")
        for key, value in configs:
            print(f"  • {key}: {value}")
        
        print_header("✅ Migration Completed Successfully!")
        print(f"Backup saved at: {BACKUP_PATH}\n")
        
        return True
        
    except Exception as e:
        print_header("❌ Migration Failed!")
        print(f"Error: {e}")
        print("\nRolling back changes...")
        cursor.execute("ROLLBACK")
        print("✅ Rollback complete\n")
        
        # Restore from backup if exists
        if BACKUP_PATH.exists():
            print(f"You can restore from backup: {BACKUP_PATH}")
        
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
