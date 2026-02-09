"""
Migration script to add User and UserVocabulary tables
Run this after deploying the code changes: python migrate_add_users.py
"""
from app_fixed import app, db
from models import User, UserVocabulary

def migrate():
    with app.app_context():
        print("Creating new tables...")
        
        # Create only the new tables (won't affect existing ones)
        db.create_all()
        
        print("✓ Migration complete!")
        print("  - User table created")
        print("  - UserVocabulary table created")
        print("\nExisting vocabulary data is preserved.")

if __name__ == '__main__':
    migrate()
