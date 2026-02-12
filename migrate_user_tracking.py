#!/usr/bin/env python3
"""
Migration script to add user tracking columns to vocabulary table.
Adds: added_by_user_id (FK to user.id), created_at (timestamp)
"""
import os
import sys

# For Cloud Run with Cloud SQL
def get_cloud_connection():
    import pg8000
    connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    unix_sock = f"/cloudsql/{connection_name}/.s.PGSQL.5432"
    print(f"Connecting to: {unix_sock}")
    return pg8000.connect(
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME', 'vocab'),
        unix_sock=unix_sock
    )

def get_local_connection():
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'chinese_vocab.db')
    return sqlite3.connect(db_path), 'sqlite'

def migrate():
    is_cloud = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    
    if is_cloud:
        print("Running on Cloud SQL (PostgreSQL)...")
        conn = get_cloud_connection()
        cursor = conn.cursor()
        db_type = 'postgres'
    else:
        print("Running on local SQLite...")
        conn, db_type = get_local_connection()
        cursor = conn.cursor()
    
    try:
        # Check if columns exist
        if db_type == 'postgres':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'vocabulary' AND column_name = 'added_by_user_id'
            """)
            has_added_by = cursor.fetchone() is not None
            
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'vocabulary' AND column_name = 'created_at'
            """)
            has_created_at = cursor.fetchone() is not None
        else:
            cursor.execute("PRAGMA table_info(vocabulary)")
            columns = [row[1] for row in cursor.fetchall()]
            has_added_by = 'added_by_user_id' in columns
            has_created_at = 'created_at' in columns
        
        # Add added_by_user_id if missing
        if not has_added_by:
            print("Adding added_by_user_id column...")
            if db_type == 'postgres':
                cursor.execute('ALTER TABLE vocabulary ADD COLUMN added_by_user_id INTEGER REFERENCES "user"(id)')
            else:
                cursor.execute('ALTER TABLE vocabulary ADD COLUMN added_by_user_id INTEGER')
            print("  ✓ added_by_user_id column added")
        else:
            print("  - added_by_user_id column already exists")
        
        # Add created_at if missing
        if not has_created_at:
            print("Adding created_at column...")
            if db_type == 'postgres':
                cursor.execute('ALTER TABLE vocabulary ADD COLUMN created_at TIMESTAMP')
            else:
                cursor.execute('ALTER TABLE vocabulary ADD COLUMN created_at TEXT')
            print("  ✓ created_at column added")
        else:
            print("  - created_at column already exists")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
        # Verify
        if db_type == 'postgres':
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
        else:
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
        count = cursor.fetchone()[0]
        print(f"  Vocabulary table has {count} rows")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrate()
