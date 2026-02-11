#!/usr/bin/env python3
"""
Simple direct migration - no Docker, just pure Python connection
Connects directly to production database and translates everything
"""
import os
import sys
import time
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv('.env', override=True)

# Get API key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env")
    sys.exit(1)

# Import requests
import requests

# Test 1: Check if we can connect to production database
print("\n[TEST 1] Attempting production database connection...")
try:
    from sqlalchemy import create_engine, text
    
    # Build connection string using .env variables 
    db_password = os.environ.get('DB_PASSWORD')
    db_url = f"postgresql+pg8000://postgres:{db_password}@34.52.239.163:5432/vocab"
    
    print(f"Connection URL: postgresql+pg8000://postgres:***@34.52.239.163:5432/vocab")
    
    engine = create_engine(db_url, echo=False, pool_pre_ping=True, pool_size=5)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM vocabulary"))
        count = result.scalar()
        print(f"[OK] Connected! Found {count} total vocabulary items")
        
        # Check how many need translation
        result = conn.execute(text("""
            SELECT COUNT(*) FROM vocabulary 
            WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
        """))
        untranslated = result.scalar()
        print(f"[OK] Items needing translation: {untranslated}")
        
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")
    sys.exit(1)

# Test 2: Check OpenAI API
print("\n[TEST 2] Testing OpenAI API...")
try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say 'OK' only"}],
            "max_tokens": 5,
        },
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"[OK] OpenAI API working")
    else:
        print(f"[FAILED] Status {response.status_code}: {response.text[:100]}")
        sys.exit(1)
except Exception as e:
    print(f"[FAILED] {e}")
    sys.exit(1)

print("\n" + "="*70)
print("ALL TESTS PASSED - Ready for production migration!")
print("="*70)
print("\nNow starting actual translation...")

from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

# Get ALL items needing translation
result = session.execute(text("""
    SELECT id, hanzi, pinyin, sent_hanzi FROM vocabulary 
    WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
    ORDER BY id
"""))
items = result.fetchall()

print(f"\nTranslating {len(items)} items...\n")

success = 0
failed = 0

for idx, (item_id, hanzi, pinyin, sent_hanzi) in enumerate(items, 1):
    try:
        # Translate word
        prompt = f"Translate Chinese '{hanzi}' (pinyin: {pinyin}) to Japanese. ONLY respond in exactly this format: kanji: [result] romaji: [result]"
        
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 50,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        
        if resp.status_code == 429:
            print(f"[{idx}] Rate limited. Waiting 60s...")
            time.sleep(60)
            continue
        
        if resp.status_code != 200:
            failed += 1
            if idx % 50 == 0:
                print(f"[{idx}] Error {resp.status_code}: skipping")
            continue
        
        content = resp.json()['choices'][0]['message']['content'].lower()
        kanji = romaji = ""
        
        for part in content.split('\n'):
            if 'kanji:' in part:
                kanji = part.split('kanji:')[1].strip()
            elif 'romaji:' in part:
                romaji = part.split('romaji:')[1].strip()
        
        # Update database
        session.execute(text("""
            UPDATE vocabulary 
            SET japanese_kanji = :k, japanese_romaji = :r,
                sent_japanese_kanji = :sk, sent_japanese_romaji = :sr
            WHERE id = :id
        """), {"k": kanji, "r": romaji, "sk": "", "sr": "", "id": item_id})
        
        if idx % 20 == 0:
            session.commit()
            print(f"[{idx}/{len(items)}] Translated {success+failed} items...")
            success += 1
        else:
            success += 1
            
    except Exception as e:
        failed += 1
        if idx % 50 == 0:
            print(f"[{idx}] Error: {str(e)[:40]}")

# Final commit
session.commit()
session.close()

print(f"\n✓ COMPLETE: {success} translated, {failed} failed")
print(f"Success rate: {success*100/(success+failed):.1f}%")
