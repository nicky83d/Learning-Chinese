"""
Database migration script to add the is_approved column to existing vocabulary table.
Run this script once to add the missing column to your database.
"""
import sqlite3
import os
from app_fixed import app, db
from models import Vocabulary, PhotoLog

def migrate_db():
    """Add is_approved column to vocabulary table if it doesn't exist."""
    db_path = 'instance/chinese_vocab.db'
    
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Connect to SQLite database directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if is_approved column exists
            cursor.execute("PRAGMA table_info(vocabulary)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_approved' not in columns:
                print("Adding is_approved column to vocabulary table...")
                cursor.execute("ALTER TABLE vocabulary ADD COLUMN is_approved BOOLEAN DEFAULT 0")
                conn.commit()
                print("✓ is_approved column added successfully!")
            else:
                print("✓ is_approved column already exists")
            
            # Now set all existing entries to is_approved=1 (True) for backward compatibility
            cursor.execute("UPDATE vocabulary SET is_approved = 1 WHERE is_approved IS NULL OR is_approved = 0")
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE is_approved = 1")
            approved_count = cursor.fetchone()[0]
            print(f"✓ Set {approved_count} existing vocabulary entries to approved")
            
            conn.close()
            
            # Now verify with SQLAlchemy
            print("\nVerifying with SQLAlchemy:")
            total = Vocabulary.query.count()
            approved = Vocabulary.query.filter_by(is_approved=True).count()
            pending = Vocabulary.query.filter_by(is_approved=False).count()
            
            print(f"  - Total vocabulary entries: {total}")
            print(f"  - Approved vocabulary: {approved}")
            print(f"  - Pending vocabulary: {pending}")
            print(f"  - Photo logs: {PhotoLog.query.count()}")
            print("\n✓ Database migration completed successfully!")
            
        except sqlite3.OperationalError as e:
            print(f"✗ Migration failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    migrate_db()
