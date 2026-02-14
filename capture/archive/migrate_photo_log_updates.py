"""
Migration script to add user_id and image_data columns to PhotoLog table
Run this after deploying the code changes: python migrate_photo_log_updates.py
"""
from app_fixed import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("Migrating PhotoLog table...")
        
        try:
            # Add user_id column with foreign key constraint if it doesn't exist
            print("  - Checking for user_id column...")
            try:
                db.session.execute(text("""
                    ALTER TABLE photo_log 
                    ADD COLUMN user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL
                """))
                db.session.commit()
                print("    ✓ Added user_id column")
            except Exception as e:
                if "already exists" in str(e):
                    print("    ℹ user_id column already exists")
                else:
                    raise
            
            # Add image_data column if it doesn't exist
            print("  - Checking for image_data column...")
            try:
                db.session.execute(text("""
                    ALTER TABLE photo_log 
                    ADD COLUMN image_data BYTEA
                """))
                db.session.commit()
                print("    ✓ Added image_data column")
            except Exception as e:
                if "already exists" in str(e):
                    print("    ℹ image_data column already exists")
                else:
                    raise
            
            print("\n✓ PhotoLog migration complete!")
            print("  - user_id: tracks which user uploaded the photo")
            print("  - image_data: stores image bytes for persistence on Cloud Run")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
