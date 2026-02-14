#!/usr/bin/env python3
"""
Fix Japanese migration - Clear bad data and re-translate all items properly.
The previous migration had issues:
1. sent_japanese_kanji contained Chinese text
2. sent_japanese_romaji contained Japanese kanji instead of romaji

This script:
1. Clears all Japanese sentence fields
2. Re-translates everything with better prompts
3. Validates output to ensure kanji/romaji are correct
"""
import os
import sys
import time
import re
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_romaji(text):
    """Check if text is mostly romaji (ASCII + common accents)."""
    if not text:
        return False
    # Count non-ASCII characters (excluding common romaji accent marks)
    non_ascii = 0
    for char in text:
        if ord(char) > 255:  # Outside Latin-1 range
            non_ascii += 1
    # Allow up to 10% non-ASCII (for any edge cases)
    return non_ascii / len(text) < 0.1

def is_japanese(text):
    """Check if text contains Japanese characters (hiragana, katakana, or kanji)."""
    if not text:
        return False
    # Japanese Unicode ranges
    for char in text:
        code = ord(char)
        # Hiragana: U+3040-U+309F
        # Katakana: U+30A0-U+30FF
        # CJK (Kanji): U+4E00-U+9FFF
        if (0x3040 <= code <= 0x309F) or (0x30A0 <= code <= 0x30FF) or (0x4E00 <= code <= 0x9FFF):
            return True
    return False

def _call_openai(api_key, prompt, max_tokens):
    """Call OpenAI API and return parsed response."""
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
        timeout=30
    )

    if resp.status_code == 429:
        return None, None, "rate_limit"

    if resp.status_code != 200:
        logger.warning(f"API error {resp.status_code}: {resp.text[:120]}")
        return "", "", "error"

    content = resp.json()['choices'][0]['message']['content'].strip()
    
    # Parse JAPANESE: and ROMAJI: labels
    japanese = ""
    romaji = ""
    
    # Try to find JAPANESE: label first
    jp_match = re.search(r"JAPANESE:\s*(.+?)(?=ROMAJI:|$)", content, re.IGNORECASE | re.DOTALL)
    rm_match = re.search(r"ROMAJI:\s*(.+?)$", content, re.IGNORECASE | re.DOTALL)
    
    if jp_match:
        japanese = jp_match.group(1).strip()
    if rm_match:
        romaji = rm_match.group(1).strip()
    
    # Fallback: line-by-line parsing
    if not japanese or not romaji:
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith('JAPANESE:'):
                japanese = line.split(':', 1)[1].strip()
            elif line.upper().startswith('ROMAJI:'):
                romaji = line.split(':', 1)[1].strip()
    
    return japanese, romaji, "ok"

def translate_word(api_key, hanzi, pinyin):
    """Translate a Chinese word to Japanese."""
    prompt = f"""Translate this Chinese word to Japanese.

Chinese: {hanzi} (pinyin: {pinyin})

Respond in EXACTLY this format:
JAPANESE: [Japanese word in kanji/hiragana]
ROMAJI: [Roman letter pronunciation]

Example for 你好 (nǐ hǎo):
JAPANESE: こんにちは
ROMAJI: konnichiwa"""

    try:
        japanese, romaji, status = _call_openai(api_key, prompt, max_tokens=60)
        
        if status == "rate_limit":
            logger.info("Rate limit hit, sleeping 60s...")
            time.sleep(60)
            japanese, romaji, status = _call_openai(api_key, prompt, max_tokens=60)
        
        # Validate
        if japanese and not is_japanese(japanese):
            logger.warning(f"Word translation not Japanese: {japanese}")
            japanese = ""
        if romaji and not is_romaji(romaji):
            logger.warning(f"Word romaji not ASCII: {romaji}")
            romaji = ""
            
        return japanese, romaji
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "", ""

def translate_sentence(api_key, sent_hanzi):
    """Translate a Chinese sentence to Japanese."""
    prompt = f"""Translate this Chinese sentence to Japanese.

Chinese sentence: {sent_hanzi}

Respond in EXACTLY this format:
JAPANESE: [Full Japanese sentence in kanji/hiragana]
ROMAJI: [Full sentence in roman letters only]

Example for 我是学生:
JAPANESE: 私は学生です
ROMAJI: watashi wa gakusei desu"""

    try:
        japanese, romaji, status = _call_openai(api_key, prompt, max_tokens=150)
        
        if status == "rate_limit":
            logger.info("Rate limit hit on sentence, sleeping 60s...")
            time.sleep(60)
            japanese, romaji, status = _call_openai(api_key, prompt, max_tokens=150)
        
        # Validate
        if japanese and not is_japanese(japanese):
            logger.warning(f"Sentence translation not Japanese: {japanese[:50]}")
            japanese = ""
        if romaji and not is_romaji(romaji):
            logger.warning(f"Sentence romaji not ASCII: {romaji[:50]}")
            romaji = ""
            
        return japanese, romaji
    except Exception as e:
        logger.error(f"Sentence translation error: {e}")
        return "", ""

def main():
    logger.info("="*70)
    logger.info("Japanese Migration FIX - Clearing bad data and re-translating")
    logger.info("="*70)
    
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    db_url = os.environ.get('DATABASE_URL', '').strip()
    
    if not api_key:
        logger.error("OPENAI_API_KEY not set!")
        return 1
    
    if not db_url:
        logger.error("DATABASE_URL not set!")
        return 1
    
    batch_limit = int(os.environ.get("BATCH_LIMIT", "50"))
    
    logger.info(f"BATCH_LIMIT={batch_limit}")
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        logger.info("SQLAlchemy imported")
    except ImportError as e:
        logger.error(f"Import failed: {e}")
        return 1
    
    logger.info("Connecting to database...")
    try:
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✓ Database connected")
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return 1
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check for env flag to skip clearing (for continued batches)
    skip_clear = os.environ.get("SKIP_CLEAR", "false").lower() == "true"
    
    if not skip_clear:
        # Clear all bad Japanese data only on first run
        logger.info("Clearing bad Japanese sentence data...")
        try:
            session.execute(text("""
                UPDATE vocabulary
                SET sent_japanese_kanji = '',
                    sent_japanese_romaji = ''
                WHERE sent_japanese_kanji != '' OR sent_japanese_romaji != ''
            """))
            session.commit()
            logger.info("✓ Cleared all Japanese sentence fields")
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            session.rollback()
    else:
        logger.info("Skipping clear (SKIP_CLEAR=true)")
    
    # Fetch items that need translation (empty or missing Japanese fields)
    logger.info("Fetching items to translate...")
    try:
        result = session.execute(text("""
            SELECT id, hanzi, pinyin, sent_hanzi
            FROM vocabulary
            WHERE hanzi IS NOT NULL AND hanzi != ''
              AND (
                  sent_japanese_kanji = '' OR sent_japanese_kanji IS NULL
                  OR sent_japanese_romaji = '' OR sent_japanese_romaji IS NULL
              )
            ORDER BY id
            LIMIT :limit
        """), {"limit": batch_limit})
        items = result.fetchall()
        logger.info(f"Found {len(items)} items to translate")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return 1
    
    if not items:
        logger.info("No items to translate!")
        return 0
    
    success = 0
    failed = 0
    
    for idx, (item_id, hanzi, pinyin, sent_hanzi) in enumerate(items, 1):
        logger.info(f"[{idx}/{len(items)}] Translating: {hanzi}")
        
        # Translate word
        jp_word, rm_word = translate_word(api_key, hanzi, pinyin or "")
        
        # Translate sentence if available
        jp_sent, rm_sent = "", ""
        if sent_hanzi:
            jp_sent, rm_sent = translate_sentence(api_key, sent_hanzi)
        
        if not jp_word and not rm_word:
            logger.warning(f"  ✗ Failed to translate word")
            failed += 1
            continue
        
        logger.info(f"  Word: {jp_word} ({rm_word})")
        if jp_sent:
            logger.info(f"  Sent: {jp_sent[:30]}... ({rm_sent[:30]}...)")
        
        # Update database
        try:
            session.execute(text("""
                UPDATE vocabulary
                SET japanese_kanji = :jk,
                    japanese_romaji = :jr,
                    sent_japanese_kanji = :sjk,
                    sent_japanese_romaji = :sjr
                WHERE id = :id
            """), {
                "jk": jp_word,
                "jr": rm_word,
                "sjk": jp_sent,
                "sjr": rm_sent,
                "id": item_id
            })
            success += 1
            
            if idx % 10 == 0:
                session.commit()
                logger.info(f"Progress: {idx}/{len(items)} - {success} success, {failed} failed")
                
        except Exception as e:
            logger.error(f"  ✗ Update failed: {e}")
            failed += 1
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
    
    session.commit()
    session.close()
    
    logger.info("="*70)
    logger.info(f"Migration complete: {success} success, {failed} failed")
    logger.info("="*70)
    
    return 0 if success > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
