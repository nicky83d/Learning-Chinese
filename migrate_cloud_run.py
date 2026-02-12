#!/usr/bin/env python3
"""
Production migration using Cloud SQL connection string
Must be run from Cloud Run where it can access the database
"""
import os
import sys
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _call_openai(api_key, prompt, max_tokens):
    """Call OpenAI API once and return (kanji, romaji)."""
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        timeout=20
    )

    if resp.status_code == 429:
        return None, None

    if resp.status_code != 200:
        logger.warning(f"API error {resp.status_code}: {resp.text[:120]}")
        return "", ""

    content = resp.json()['choices'][0]['message']['content'].lower()
    kanji = romaji = ""

    for line in content.split('\n'):
        if 'kanji:' in line:
            kanji = line.split('kanji:')[1].strip().replace('xxx', '').replace('xxxx', '').strip()
        elif 'romaji:' in line:
            romaji = line.split('romaji:')[1].strip().replace('xxx', '').replace('xxxx', '').strip()

    return kanji, romaji


def translate_item(api_key, hanzi, pinyin):
    """Translate a Chinese word to Japanese via OpenAI."""
    prompt = (
        f"Translate Chinese '{hanzi}' (pinyin: {pinyin}) to Japanese. "
        "Format response EXACTLY as: kanji: XXXX romaji: XXXX"
    )

    try:
        kanji, romaji = _call_openai(api_key, prompt, max_tokens=50)
        if kanji is None and romaji is None:
            logger.info("Rate limit hit, sleeping 60s then retrying once")
            time.sleep(60)
            kanji, romaji = _call_openai(api_key, prompt, max_tokens=50)
        return kanji or "", romaji or ""
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "", ""


def translate_sentence(api_key, hanzi_sentence):
    """Translate a Chinese sentence to Japanese via OpenAI."""
    prompt = (
        f"Translate this Chinese sentence to Japanese: '{hanzi_sentence}'. "
        "Format response EXACTLY as: kanji: XXXX romaji: XXXX"
    )

    try:
        kanji, romaji = _call_openai(api_key, prompt, max_tokens=120)
        if kanji is None and romaji is None:
            logger.info("Rate limit hit on sentence, sleeping 60s then retrying once")
            time.sleep(60)
            kanji, romaji = _call_openai(api_key, prompt, max_tokens=120)
        return kanji or "", romaji or ""
    except Exception as e:
        logger.error(f"Sentence translation error: {e}")
        return "", ""

def main():
    logger.info("="*70)
    logger.info("Japanese Migration - Cloud Run Version")
    logger.info("="*70)
    
    # Get environment
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    db_url = os.environ.get('DATABASE_URL', '').strip()
    
    if not api_key:
        logger.error("OPENAI_API_KEY not set!")
        return 1
    
    if not db_url:
        logger.error("DATABASE_URL not set!")
        return 1
    
    batch_limit = int(os.environ.get("BATCH_LIMIT", "100"))
    translate_sentences = os.environ.get("TRANSLATE_SENTENCES", "true").lower() == "true"

    logger.info(f"Environment variables configured (BATCH_LIMIT={batch_limit}, TRANSLATE_SENTENCES={translate_sentences})")
    
    # Import after env check
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        logger.info("SQLAlchemy imported")
    except ImportError as e:
        logger.error(f"Import failed: {e}")
        return 1
    
    # Connect
    logger.info("Connecting to database...")
    try:
        engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=5
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connected")
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return 1
    
    # Query
    Session = sessionmaker(bind=engine)
    session = Session()
    
    logger.info("Fetching untranslated items...")
    try:
        result = session.execute(text("""
            SELECT id, hanzi, pinyin, sent_hanzi
            FROM vocabulary
            WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
            ORDER BY id
            LIMIT :limit
        """), {"limit": batch_limit})
        items = result.fetchall()
        logger.info(f"Found {len(items)} items")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return 1
    
    if not items:
        logger.info("All items already translated!")
        return 0
    
    # Translate
    logger.info(f"Starting translation of {len(items)} items...")
    success = 0
    rate_limited = 0
    
    for idx, (item_id, hanzi, pinyin, sent_hanzi) in enumerate(items, 1):
        kanji, romaji = translate_item(api_key, hanzi, pinyin)
        sent_kanji, sent_romaji = "", ""

        if translate_sentences and sent_hanzi:
            sent_kanji, sent_romaji = translate_sentence(api_key, sent_hanzi)

        if not kanji and not romaji:
            rate_limited += 1
            if rate_limited >= 10:
                logger.info("Rate limited too often, stopping early")
                break
            continue

        # Update database
        try:
            session.execute(text("""
                UPDATE vocabulary
                SET japanese_kanji = :k,
                    japanese_romaji = :r,
                    sent_japanese_kanji = :sk,
                    sent_japanese_romaji = :sr
                WHERE id = :id
            """), {
                "k": kanji,
                "r": romaji,
                "sk": sent_kanji,
                "sr": sent_romaji,
                "id": item_id
            })
            success += 1

            if idx % 10 == 0:
                session.commit()
                logger.info(f"Progress: {idx}/{len(items)} - {success} translated")
        except Exception as e:
            logger.error(f"Update failed for {item_id}: {e}")
    
    session.commit()
    session.close()
    
    logger.info("="*70)
    logger.info(f"Migration complete: {success} translated")
    logger.info("="*70)
    
    return 0 if success > 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
