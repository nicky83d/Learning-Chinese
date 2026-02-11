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

def translate_item(api_key, hanzi, pinyin):
    """Translate a Chinese word to Japanese via OpenAI"""
    try:
        prompt = f"Translate Chinese '{hanzi}' (pinyin: {pinyin}) to Japanese. Format response EXACTLY as: kanji: XXXX romaji: XXXX"
        
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 50,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=20
        )
        
        if resp.status_code == 429:
            logger.info("Rate limit hit, returning empty")
            return "", ""
        
        if resp.status_code != 200:
            logger.warning(f"API error {resp.status_code}")
            return "", ""
        
        content = resp.json()['choices'][0]['message']['content'].lower()
        kanji = romaji = ""
        
        for line in content.split('\n'):
            if 'kanji:' in line:
                kanji = line.split('kanji:')[1].strip().replace('xxx', '').replace('xxxx', '').strip()
            elif 'romaji:' in line:
                romaji = line.split('romaji:')[1].strip().replace('xxx', '').replace('xxxx', '').strip()
        
        return kanji, romaji
    except Exception as e:
        logger.error(f"Translation error: {e}")
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
    
    logger.info("Environment variables configured")
    
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
            max_overflow=5,
            connect_args={"connect_timeout": 10}
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
            SELECT id, hanzi, pinyin FROM vocabulary 
            WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
            ORDER BY id
        """))
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
    
    for idx, (item_id, hanzi, pinyin) in enumerate(items, 1):
        kanji, romaji = translate_item(api_key, hanzi, pinyin)
        
        if not kanji and not romaji:
            rate_limited += 1
            if idx > 100:  # Stop after limited attempts if rate limited
                logger.info(f"Rate limited, stopping at item {idx}")
                break
        else:
            # Update database
            try:
                session.execute(text("""
                    UPDATE vocabulary 
                    SET japanese_kanji = :k, japanese_romaji = :r
                    WHERE id = :id
                """), {"k": kanji, "r": romaji, "id": item_id})
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
