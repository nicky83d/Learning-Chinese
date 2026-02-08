"""
Initialize or update the database schema.
Run this script to create the PhotoLog table if it doesn't exist.
"""
from app_fixed import app, db
from models import Vocabulary, PhotoLog

def init_db():
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Set is_approved=True for all existing vocabulary entries (backward compatibility)
        # This allows previously added words to be visible
        try:
            entries_without_status = Vocabulary.query.filter(Vocabulary.is_approved == None).count()
            if entries_without_status > 0:
                print(f"\nUpdating {entries_without_status} existing entries to is_approved=True...")
                Vocabulary.query.filter(Vocabulary.is_approved == None).update({'is_approved': True})
                db.session.commit()
                print(f"✓ Updated {entries_without_status} entries")
        except Exception as e:
            print(f"Note: {e}")
        
        # Check tables
        print("\nChecking tables:")
        print(f"  - Vocabulary entries: {Vocabulary.query.count()}")
        print(f"  - Approved vocabulary: {Vocabulary.query.filter_by(is_approved=True).count()}")
        print(f"  - Pending vocabulary: {Vocabulary.query.filter_by(is_approved=False).count()}")
        print(f"  - Photo logs: {PhotoLog.query.count()}")
        print("\nDatabase is ready!")

if __name__ == '__main__':
    init_db()
