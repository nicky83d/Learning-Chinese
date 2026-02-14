#!/usr/bin/env python3
"""
Simple migration script to add Japanese translations using sqlite3 directly.
"""
import sqlite3
import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Setup logging
log_file = open('migrate_japanese.log', 'w', encoding='utf-8')

def log(msg):
    """Print to console and log file"""
    print(msg)
    log_file.write(msg + '\n')
    log_file.flush()

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)

# Get API key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    log("ERROR: OPENAI_API_KEY not set in environment")
    log_file.close()
    sys.exit(1)

log("=" * 60)
log("Japanese Translation Migration (SQLite)")
log("=" * 60)

# Connect to database
db_path = 'instance/chinese_vocab.db'
log(f"Connecting to {db_path}...")
try:
    db = sqlite3.connect(db_path, timeout=30)
    db.row_factory = sqlite3.Row
    log("Connected successfully")
except Exception as e:
    log(f"ERROR connecting to database: {e}")
    log_file.close()
    sys.exit(1)

log("Getting vocabulary items that need Japanese translations...")
cursor = db.cursor()

# Get count of all items
try:
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_count = cursor.fetchone()[0]
    log(f"Total vocabulary items: {total_count}")
except Exception as e:
    log(f"ERROR: {e}")
    log_file.close()
    sys.exit(1)

# Get items needing Japanese
try:
    cursor.execute("""
        SELECT id, hanzi, pinyin, sent_hanzi 
        FROM vocabulary 
        WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
           OR (japanese_romaji = '' OR japanese_romaji IS NULL)
    """)
    
    items = cursor.fetchall()
    log(f"Found {len(items)} items needing Japanese translations")
except Exception as e:
    log(f"ERROR: {e}")
    log_file.close()
    sys.exit(1)

if not items:
    log("All items already have Japanese translations!")
    log_file.close()
    sys.exit(0)

log(f"\nStarting translation of items...\n")

def translate_to_japanese(text):
    """Call OpenAI API to translate text to Japanese."""
    if not text or not text.strip():
        return ('', '')
    
    api_url = "https://api.openai.com/v1/chat/completions"
    
    prompt = f"""Translate this Chinese text to Japanese. Return ONLY the translation in this format:
KANJI: [Japanese in kanji/hiragana]
ROMAJI: [Roman letters]

Chinese: {text}"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 100,
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 429:
            log("Rate limit hit, waiting 30 seconds...")
            time.sleep(30)
            return translate_to_japanese(text)  # Retry
        elif response.status_code != 200:
            log(f"API error: {response.status_code} - {response.text[:100]}")
            return ('', '')
        
        result = response.json()
        if 'choices' not in result or not result['choices']:
            log(f"No choices in response")
            return ('', '')
        
        translation_text = result['choices'][0]['message']['content'].strip()
        
        kanji = ''
        romaji = ''
        for line in translation_text.split('\n'):
            line = line.strip()
            if line.startswith('KANJI:'):
                kanji = line.replace('KANJI:', '').strip()
            elif line.startswith('ROMAJI:'):
                romaji = line.replace('ROMAJI:', '').strip()
        
        return (kanji, romaji)
    
    except Exception as e:
        log(f"Translation error: {e}")
        return ('', '')

# Translate each item
cursor = db.cursor()
translated_count = 0

for i, item in enumerate(items, 1):
    log(f"[{i}/{len(items)}] Processing: {item['hanzi']} ({item['pinyin']})")
    
    # Translate word
    kanji, romaji = translate_to_japanese(item['hanzi'])
    if kanji or romaji:
        log(f"  [+] Word: {kanji} ({romaji})")
        try:
            cursor.execute("""
                UPDATE vocabulary 
                SET japanese_kanji = ?, japanese_romaji = ? 
                WHERE id = ?
            """, (kanji, romaji, item['id']))
            translated_count += 1
        except Exception as e:
            log(f"  ERROR updating {item['hanzi']}: {e}")
    else:
        log(f"  [-] Failed to translate word")
    
    # Translate sentence
    if item['sent_hanzi']:
        sent_kanji, sent_romaji = translate_to_japanese(item['sent_hanzi'])
        if sent_kanji or sent_romaji:
            log(f"  [+] Sentence: {sent_kanji[:30]}... ({sent_romaji[:30]}...)")
            try:
                cursor.execute("""
                    UPDATE vocabulary 
                    SET sent_japanese_kanji = ?, sent_japanese_romaji = ? 
                    WHERE id = ?
                """, (sent_kanji, sent_romaji, item['id']))
            except Exception as e:
                log(f"  ERROR updating sentence: {e}")
        else:
            log(f"  [-] Failed to translate sentence")
    
    try:
        db.commit()
    except Exception as e:
        log(f"  ERROR committing: {e}")

log("\n" + "=" * 60)
log(f"Migration complete! Translated {translated_count} items")
log("=" * 60)

db.close()
log_file.close()
