#!/usr/bin/env python3
"""
Production migration script for Japanese translations.
Connects to PostgreSQL database and translates vocabulary using OpenAI API.

Deploy to Google Cloud with:
gcloud run jobs create migrate-japanese \
  --image gcr.io/chinese-website-482900/migrate-japanese:latest \
  --region europe-west1 \
  --set-env-vars DATABASE_URL='postgresql://...' \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest
"""
import os
import sys
import time
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY not set in environment")
    sys.exit(1)

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL not set in environment")
    sys.exit(1)

logger.info("=" * 60)
logger.info("Japanese Translation Migration (Production)")
logger.info("=" * 60)

# Import SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    logger.info("SQLAlchemy imported successfully")
except ImportError as e:
    logger.error(f"Failed to import SQLAlchemy: {e}")
    sys.exit(1)

# Connect to database
logger.info(f"Connecting to production database...")
try:
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Test connection
    session.execute(text("SELECT 1"))
    session.commit()
    logger.info("Database connection successful")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    sys.exit(1)

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
            logger.info("Rate limit hit (429), waiting 60 seconds...")
            time.sleep(60)
            return translate_to_japanese(text)  # Retry
        elif response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text[:100]}")
            return ('', '')
        
        result = response.json()
        if 'choices' not in result or not result['choices']:
            logger.error(f"No choices in response: {result}")
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
    
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout translating '{text}'")
        return ('', '')
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return ('', '')

# Get vocabulary items needing translation
logger.info("Fetching vocabulary items needing Japanese translations...")
try:
    result = session.execute(text("""
        SELECT id, hanzi, pinyin, sent_hanzi 
        FROM vocabulary 
        WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
           OR (japanese_romaji = '' OR japanese_romaji IS NULL)
        ORDER BY id
    """))
    items = result.fetchall()
    logger.info(f"Found {len(items)} items needing translation")
except Exception as e:
    logger.error(f"Error fetching items: {e}")
    session.close()
    sys.exit(1)

if not items:
    logger.info("All items already have Japanese translations!")
    session.close()
    sys.exit(0)

# Translate items
logger.info(f"Starting translation of {len(items)} items...\n")
translated_count = 0
failed_count = 0

for i, item in enumerate(items, 1):
    try:
        item_id, hanzi, pinyin, sent_hanzi = item
        logger.info(f"[{i}/{len(items)}] Processing: {hanzi} ({pinyin})")
        
        # Translate word
        kanji, romaji = translate_to_japanese(hanzi)
        if kanji or romaji:
            logger.info(f"  [+] Word: {kanji} ({romaji})")
            session.execute(text("""
                UPDATE vocabulary 
                SET japanese_kanji = :kanji, japanese_romaji = :romaji 
                WHERE id = :id
            """), {"kanji": kanji, "romaji": romaji, "id": item_id})
            translated_count += 1
        else:
            logger.warning(f"  [-] Failed to translate word")
            failed_count += 1
        
        # Translate sentence
        if sent_hanzi:
            sent_kanji, sent_romaji = translate_to_japanese(sent_hanzi)
            if sent_kanji or sent_romaji:
                logger.info(f"  [+] Sentence: {sent_kanji[:30]}... ({sent_romaji[:30]}...)")
                session.execute(text("""
                    UPDATE vocabulary 
                    SET sent_japanese_kanji = :kanji, sent_japanese_romaji = :romaji 
                    WHERE id = :id
                """), {"kanji": sent_kanji, "romaji": sent_romaji, "id": item_id})
            else:
                logger.warning(f"  [-] Failed to translate sentence")
        
        # Commit periodically
        if i % 10 == 0:
            session.commit()
            logger.info(f"  Committed {i} items")
    
    except Exception as e:
        logger.error(f"Error processing item {i}: {e}")
        failed_count += 1

# Final commit
try:
    session.commit()
    logger.info("Final commit successful")
except Exception as e:
    logger.error(f"Error on final commit: {e}")

session.close()

logger.info("\n" + "=" * 60)
logger.info("Migration complete!")
logger.info("=" * 60)
logger.info(f"[+] Successfully translated: {translated_count}")
logger.info(f"[-] Failed: {failed_count}")
logger.info(f"Total processed: {len(items)}")
logger.info("=" * 60)

sys.exit(0 if failed_count == 0 else 1)
