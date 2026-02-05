"""Database migration script - Update schema from old to new format."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from src.database import engine, SessionLocal, Base
from src.logging_config import bot_logger


def migrate_database():
    """Migrate old database schema to new professional format."""
    
    db = SessionLocal()
    conn = engine.raw_connection()
    cursor = conn.cursor()
    
    try:
        # Get current table schema
        inspector = inspect(engine)
        files_columns = [col['name'] for col in inspector.get_columns('files')]
        
        bot_logger.info(f"Current files table columns: {files_columns}")
        
        # Check if new columns exist
        if 'file_mime_type' not in files_columns:
            bot_logger.info("Adding file_mime_type column...")
            cursor.execute("ALTER TABLE files ADD COLUMN file_mime_type VARCHAR(100)")
        
        if 'status' not in files_columns:
            bot_logger.info("Adding status column...")
            cursor.execute("ALTER TABLE files ADD COLUMN status VARCHAR(50) DEFAULT 'active'")
            cursor.execute("CREATE INDEX idx_file_status ON files(status)")
        
        if 'expires_at' not in files_columns:
            bot_logger.info("Adding expires_at column...")
            cursor.execute("ALTER TABLE files ADD COLUMN expires_at DATETIME")
            cursor.execute("CREATE INDEX idx_file_expires_at ON files(expires_at)")
        
        if 'total_download_size' not in files_columns:
            bot_logger.info("Adding total_download_size column...")
            cursor.execute("ALTER TABLE files ADD COLUMN total_download_size INTEGER DEFAULT 0")
        
        if 'is_public' not in files_columns:
            bot_logger.info("Adding is_public column...")
            cursor.execute("ALTER TABLE files ADD COLUMN is_public BOOLEAN DEFAULT 0")
        
        if 'checksum' not in files_columns:
            bot_logger.info("Adding checksum column...")
            cursor.execute("ALTER TABLE files ADD COLUMN checksum VARCHAR(128)")
        
        # Check if user_id column exists (new schema)
        if 'user_id' not in files_columns:
            bot_logger.info("Adding user_id column...")
            # First create the telegram_users table if it doesn't exist
            if 'telegram_users' not in inspector.get_table_names():
                bot_logger.info("Creating telegram_users table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telegram_users (
                        id VARCHAR(36) PRIMARY KEY,
                        telegram_user_id INTEGER NOT NULL UNIQUE,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX idx_user_telegram_id ON telegram_users(telegram_user_id)")
            
            # Add user_id column to files
            cursor.execute("ALTER TABLE files ADD COLUMN user_id VARCHAR(36)")
            cursor.execute("CREATE INDEX idx_file_user_id ON files(user_id)")
            
            # Migrate existing telegram_user_id to user_id (if column exists)
            if 'telegram_user_id' in files_columns:
                cursor.execute("""
                    UPDATE files SET user_id = telegram_user_id WHERE user_id IS NULL
                """)
        
        # Create indices if they don't exist
        existing_indices = [idx['name'] for idx in inspector.get_indexes('files')]
        
        indices_to_create = [
            ('idx_file_telegram_id', 'CREATE INDEX IF NOT EXISTS idx_file_telegram_id ON files(telegram_file_id)'),
            ('idx_file_created_at', 'CREATE INDEX IF NOT EXISTS idx_file_created_at ON files(created_at)'),
        ]
        
        for idx_name, idx_sql in indices_to_create:
            if idx_name not in existing_indices:
                bot_logger.info(f"Creating index {idx_name}...")
                cursor.execute(idx_sql)
        
        # Create download_history table if it doesn't exist
        if 'download_history' not in inspector.get_table_names():
            bot_logger.info("Creating download_history table...")
            cursor.execute("""
                CREATE TABLE download_history (
                    id VARCHAR(36) PRIMARY KEY,
                    file_id VARCHAR(36) NOT NULL,
                    user_id VARCHAR(36),
                    downloaded_bytes INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_agent VARCHAR(512),
                    ip_address VARCHAR(45),
                    FOREIGN KEY(file_id) REFERENCES files(id),
                    FOREIGN KEY(user_id) REFERENCES telegram_users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_file_id ON download_history(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_user_id ON download_history(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_created_at ON download_history(created_at)")
        
        # Create statistics table if it doesn't exist
        if 'statistics' not in inspector.get_table_names():
            bot_logger.info("Creating statistics table...")
            cursor.execute("""
                CREATE TABLE statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_files INTEGER DEFAULT 0,
                    total_size_bytes INTEGER DEFAULT 0,
                    active_files INTEGER DEFAULT 0,
                    total_downloads INTEGER DEFAULT 0,
                    total_downloads_bytes INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Insert initial record
            cursor.execute("INSERT INTO statistics DEFAULT VALUES")
        
        conn.commit()
        bot_logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        bot_logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        cursor.close()
        conn.close()
        db.close()


if __name__ == "__main__":
    bot_logger.info("Starting database migration...")
    if migrate_database():
        print("✅ Migration completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)
