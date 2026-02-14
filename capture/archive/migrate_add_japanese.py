#!/usr/bin/env python3
"""
Migration script to add Japanese translations to existing vocabulary.
Translates Chinese hanzi and example sentences to Japanese using OpenAI API.

Usage:
    python migrate_add_japanese.py [--dry-run]
    
Options:
    --dry-run   Show what would be translated without actually updating DB
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migrate_japanese.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("Starting Japanese Translation Migration")
logger.info("=" * 60)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
logger.info(f"Loading environment from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

try:
    import requests
    logger.info("Requests module imported successfully")
except ImportError as e:
    logger.error(f"Failed to import requests: {e}")
    sys.exit(1)

# Set OpenAI API key for use in translation function
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY not set in environment")
    sys.exit(1)

logger.info("OpenAI API key configured")

# Setup database connection directly (avoid importing app_fixed which has OpenAI initialization issues)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Get database URL from environment or use default SQLite
# Note: Flask defaults to instance/chinese_vocab.db, but direct SQLAlchemy uses the current dir
db_url = os.environ.get('DATABASE_URL')

# If no DATABASE_URL env var, try to find the right database file
if not db_url:
    # Check if instance folder has the main database
    instance_db_path = os.path.join(os.path.dirname(__file__), 'instance', 'chinese_vocab.db')
    root_db_path = os.path.join(os.path.dirname(__file__), 'chinese_vocab.db')
    
    if os.path.exists(instance_db_path) and os.path.getsize(instance_db_path) > 0:
        db_url = f'sqlite:///{instance_db_path.replace(chr(92), "/")}'  # Convert backslashes to forward slashes
        logger.info(f"Found instance database: {instance_db_path}")
    elif os.path.exists(root_db_path):
        db_url = f'sqlite:///{root_db_path.replace(chr(92), "/")}'
        logger.info(f"Found root database: {root_db_path}")
    else:
        db_url = 'sqlite:///instance/chinese_vocab.db'
        logger.info("Using default path: instance/chinese_vocab.db")

logger.info(f"Connecting to database: {db_url}")

try:
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Import models directly
try:
    from models import Vocabulary
    logger.info("Models imported successfully")
except Exception as e:
    logger.error(f"Failed to import models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def translate_to_japanese(text: str, context: str = "word", script_type: str = "both") -> tuple:
    """
    Translate text to Japanese using OpenAI API.
    Uses requests library directly to avoid openai library compatibility issues.
    
    Args:
        text: Text to translate (hanzi or English)
        context: Either 'word' or 'sentence' to provide better context
        script_type: 'kanji', 'romaji', or 'both' to specify what to generate
    
    Returns:
        Tuple of (kanji, romaji) or ('', '') if translation fails
    """
    import requests
    
    if not text or not text.strip():
        return ('', '')
    
    max_attempts = 3
    api_url = "https://api.openai.com/v1/chat/completions"
    
    for try_num in range(1, max_attempts + 1):
        try:
            # Create a prompt that asks for both kanji and romaji
            if context == "sentence":
                prompt = f"""Translate this Chinese sentence to Japanese. Return ONLY the translation in this format:
KANJI: [Japanese in kanji/hiragana]
ROMAJI: [Roman letters]

Chinese: {text}"""
            else:
                prompt = f"""Translate this Chinese word/phrase to Japanese. Return ONLY the translation in this format:
KANJI: [Japanese characters - kanji and hiragana as appropriate]
ROMAJI: [Roman letters]

Chinese: {text}"""
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 100,
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 429:
                logger.warning(f"Rate limit hit, waiting 30 seconds... (attempt {try_num}/{max_attempts})")
                time.sleep(30)
                continue
            elif response.status_code == 401:
                logger.error(f"Invalid API key")
                return ('', '')
            elif response.status_code >= 500:
                logger.warning(f"API error: status {response.status_code} (attempt {try_num}/{max_attempts})")
                time.sleep(5)
                continue
            elif response.status_code != 200:
                logger.warning(f"API error: {response.status_code} - {response.text} (attempt {try_num}/{max_attempts})")
                time.sleep(2)
                continue
            
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                logger.warning(f"No choices in response: {result}")
                continue
            
            translation_text = result['choices'][0]['message']['content'].strip()
            
            # Parse the response
            kanji = ''
            romaji = ''
            
            for line in translation_text.split('\n'):
                line = line.strip()
                if line.startswith('KANJI:'):
                    kanji = line.replace('KANJI:', '').strip()
                elif line.startswith('ROMAJI:'):
                    romaji = line.replace('ROMAJI:', '').strip()
            
            if kanji or romaji:
                return (kanji, romaji)
            else:
                logger.warning(f"Could not parse translation response: {translation_text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout (attempt {try_num}/{max_attempts})")
            time.sleep(2)
            continue
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error (attempt {try_num}/{max_attempts})")
            time.sleep(5)
            continue
        except Exception as e:
            logger.warning(f"Failed to translate '{text}': {e}")
            if try_num >= max_attempts:
                return ('', '')
            time.sleep(2)
            continue
    
    return ('', '')

def migrate_japanese_translations(dry_run=False):
    """
    Migrate all vocabulary items to add Japanese translations (both kanji and romaji).
    Only translates items that don't already have Japanese translations.
    """
    from sqlalchemy import inspect
    
    # First, ensure the columns exist
    logger.info("Ensuring database schema has Japanese columns...")
    
    try:
        # Check which columns already exist
        inspector = inspect(engine)
        vocab_columns = [col['name'] for col in inspector.get_columns('vocabulary')]
        
        columns_to_add = [
            ('japanese_kanji', "VARCHAR(200) DEFAULT ''"),
            ('japanese_romaji', "VARCHAR(200) DEFAULT ''"),
            ('sent_japanese_kanji', "VARCHAR(200) DEFAULT ''"),
            ('sent_japanese_romaji', "VARCHAR(200) DEFAULT ''"),
        ]
        
        for col_name, col_def in columns_to_add:
            if col_name not in vocab_columns:
                try:
                    session.execute(text(f"ALTER TABLE vocabulary ADD COLUMN {col_name} {col_def}"))
                    session.commit()
                    logger.info(f"[+] Added {col_name} column")
                except Exception as e:
                    session.rollback()
                    logger.warning(f"Could not add {col_name}: {e}")
            else:
                logger.info(f"[+] {col_name} column already exists")
        
        # Now get all vocabulary items that need Japanese translations
        items_needing_japanese = session.query(Vocabulary).filter(
            (Vocabulary.japanese_kanji == '') | (Vocabulary.japanese_kanji == None) |
            (Vocabulary.japanese_romaji == '') | (Vocabulary.japanese_romaji == None)
        ).all()
        
        logger.info(f"Found {len(items_needing_japanese)} vocabulary items needing Japanese translations")
        
        if not items_needing_japanese:
            logger.info("All vocabulary items already have Japanese translations!")
            return
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be saved")
        
        # Process each item
        translated_count = 0
        skipped_count = 0
        failed_count = 0
        
        for i, vocab in enumerate(items_needing_japanese, 1):
            try:
                logger.info(f"[{i}/{len(items_needing_japanese)}] Processing: {vocab.hanzi} ({vocab.pinyin})")
                
                # Translate the main word from hanzi
                if vocab.hanzi:
                    kanji, romaji = translate_to_japanese(vocab.hanzi, context="word")
                    if kanji or romaji:
                        vocab.japanese_kanji = kanji
                        vocab.japanese_romaji = romaji
                        logger.info(f"  [+] Word: {vocab.hanzi} -> {kanji} ({romaji})")
                        translated_count += 1
                    else:
                        logger.warning(f"  [-] Failed to translate word: {vocab.hanzi}")
                        failed_count += 1
                else:
                    skipped_count += 1
                
                # Translate the example sentence from hanzi if available
                if vocab.sent_hanzi:
                    sent_kanji, sent_romaji = translate_to_japanese(vocab.sent_hanzi, context="sentence")
                    if sent_kanji or sent_romaji:
                        vocab.sent_japanese_kanji = sent_kanji
                        vocab.sent_japanese_romaji = sent_romaji
                        logger.info(f"  [+] Sentence: {vocab.sent_hanzi[:30]}... -> {sent_kanji[:30]}... ({sent_romaji[:30]}...)")
                    else:
                        logger.warning(f"  [-] Failed to translate sentence: {vocab.sent_hanzi}")
                
                # Save to database (or skip if dry-run)
                if not dry_run:
                    session.commit()
                    logger.debug("Database commit successful")
                else:
                    logger.debug("(Dry run - not saving)")
                
            except Exception as e:
                logger.error(f"Error processing {vocab.hanzi}: {e}")
                if not dry_run:
                    session.rollback()
                failed_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration complete!")
        logger.info("=" * 60)
        logger.info(f"  [+] Successfully translated: {translated_count}")
        logger.info(f"  [.] Skipped: {skipped_count}")
        logger.info(f"  [-] Failed: {failed_count}")
        logger.info(f"  Total processed: {i}")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        logger.info("=" * 60)

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("Running in DRY RUN mode (no changes will be saved)")
    
    try:
        migrate_japanese_translations(dry_run=dry_run)
        logger.info("Migration finished successfully!")
        sys.exit(0)
    except KeyboardInterrupt:
        logger.warning("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

