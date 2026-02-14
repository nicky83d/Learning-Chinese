#!/usr/bin/env python3
"""
Final Japanese Translation Migration Script
Direct PostgreSQL + OpenAI integration with proper error handling
"""
import os
import sys
import time
import requests
import json

def main():
    # Get config from environment
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    db_url = os.environ.get('DATABASE_URL', '').strip()
    
    if not api_key or not db_url:
        print(f"ERROR: Missing environment variables")
        print(f"  OPENAI_API_KEY: {'set' if api_key else 'NOT SET'}")
        print(f"  DATABASE_URL: {'set' if db_url else 'NOT SET'}")
        return 1
    
    print("="*70)
    print("Japanese Translation Migration")
    print("="*70)
    
    try:
        import pg8000
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        print("[OK] Imports successful")
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        return 1
    
    # Connect to database
    print(f"\n[*] Connecting to database...")
    try:
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("[OK] Database connection verified")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return 1
    
    # Get items to translate
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n[*] Fetching items needing translation...")
    try:
        result = session.execute(text("""
            SELECT id, hanzi, pinyin, sent_hanzi, sent_pinyin
            FROM vocabulary 
            WHERE (japanese_kanji IS NULL OR japanese_kanji = '')
               OR (japanese_romaji IS NULL OR japanese_romaji = '')
            ORDER BY id
        """))
        items = result.fetchall()
        print(f"[OK] Found {len(items)} items needing translation")
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        session.close()
        return 1
    
    if not items:
        print("[OK] All items already translated!")
        session.close()
        return 0
    
    # Translate
    print(f"\n[*] Starting translation of {len(items)} items...")
    print("-" * 70)
    
    success_count = 0
    error_count = 0
    
    for idx, item in enumerate(items, 1):
        item_id, hanzi, pinyin, sent_hanzi, sent_pinyin = item
        
        try:
            # Translate word
            word_prompt = f"Translate Chinese '{hanzi}' (pinyin: {pinyin}) to Japanese. Format: KANJI: [result] ROMAJI: [result]"
            word_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": word_prompt}],
                    "temperature": 0.3,
                    "max_tokens": 60,
                },
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=15
            )
            
            if word_response.status_code == 429:
                print(f"[RATE_LIMIT] Item {idx}: Waiting 60s...")
                time.sleep(60)
                continue
            
            word_kanji = ""
            word_romaji = ""
            
            if word_response.status_code == 200:
                text = word_response.json()['choices'][0]['message']['content']
                for line in text.split('\n'):
                    if 'KANJI:' in line:
                        word_kanji = line.split('KANJI:')[1].strip()
                    elif 'ROMAJI:' in line:
                        word_romaji = line.split('ROMAJI:')[1].strip()
            
            # Translate sentence
            sent_kanji = ""
            sent_romaji = ""
            
            if sent_hanzi:
                sent_prompt = f"Translate Chinese sentence '{sent_hanzi}' to Japanese. Format: KANJI: [result] ROMAJI: [result]"
                sent_response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": sent_prompt}],
                        "temperature": 0.3,
                        "max_tokens": 150,
                    },
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    timeout=15
                )
                
                if sent_response.status_code == 200:
                    text = sent_response.json()['choices'][0]['message']['content']
                    for line in text.split('\n'):
                        if 'KANJI:' in line:
                            sent_kanji = line.split('KANJI:')[1].strip()
                        elif 'ROMAJI:' in line:
                            sent_romaji = line.split('ROMAJI:')[1].strip()
            
            # Update database
            session.execute(text("""
                UPDATE vocabulary 
                SET japanese_kanji = :kanji, 
                    japanese_romaji = :romaji,
                    sent_japanese_kanji = :sent_kanji,
                    sent_japanese_romaji = :sent_romaji
                WHERE id = :id
            """), {
                "id": item_id,
                "kanji": word_kanji,
                "romaji": word_romaji,
                "sent_kanji": sent_kanji,
                "sent_romaji": sent_romaji,
            })
            
            if idx % 10 == 0:
                session.commit()
                print(f"[OK] Translated {idx}/{len(items)} items (committed locally)")
            
            success_count += 1
            
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] Item {idx}")
            error_count += 1
        except Exception as e:
            print(f"[ERROR] Item {idx}: {str(e)[:50]}")
            error_count += 1
    
    # Final commit
    session.commit()
    session.close()
    
    print("-" * 70)
    print(f"\n[COMPLETE] Translated: {success_count}, Errors: {error_count}")
    print(f"Success rate: {success_count/len(items)*100:.1f}%")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
