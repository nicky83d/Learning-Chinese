"""
Fix Japanese sentence fields that were swapped during migration.
The migration script put Japanese sentences in sent_japanese_romaji 
and Chinese/empty values in sent_japanese_kanji. This swaps them back.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment or use default
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:your_password@localhost:5432/vocab')

# For Cloud SQL with pg8000
if 'postgresql://' in database_url and '@/' in database_url:
    # Already has unix socket format
    pass
elif 'postgresql://' in database_url:
    # May need to convert for pg8000
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://')

print(f"Connecting to database...")
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Get count of items that need fixing
    result = session.execute(text("""
        SELECT COUNT(*) FROM vocabulary 
        WHERE sent_japanese_kanji != '' 
        OR sent_japanese_romaji != ''
    """))
    total = result.scalar()
    print(f"Found {total} items with Japanese sentence data to check")
    
    # Swap the sentence fields
    print("\nSwapping sent_japanese_kanji <-> sent_japanese_romaji...")
    session.execute(text("""
        UPDATE vocabulary 
        SET 
            sent_japanese_kanji = sent_japanese_romaji,
            sent_japanese_romaji = sent_japanese_kanji
        WHERE 
            sent_japanese_kanji != '' 
            OR sent_japanese_romaji != ''
    """))
    
    session.commit()
    print(f"✅ Successfully swapped Japanese sentence fields for {total} items")
    
    # Verify a sample
    print("\n=== Sample after fix ===")
    result = session.execute(text("""
        SELECT hanzi, sent_hanzi, sent_japanese_kanji, sent_japanese_romaji 
        FROM vocabulary 
        WHERE sent_japanese_kanji != '' 
        LIMIT 5
    """))
    
    for row in result:
        print(f"\n{row[0]}: {row[1]}")
        print(f"  JP Kanji: {row[2][:50]}...")
        print(f"  JP Romaji: {row[3][:50]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()

print("\n✅ Migration complete!")
