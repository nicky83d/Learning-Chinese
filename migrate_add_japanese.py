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
    import openai
    logger.info("OpenAI module imported successfully")
except ImportError as e:
    logger.error(f"Failed to import openai: {e}")
    sys.exit(1)

# Set OpenAI API key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY not set in environment")
    sys.exit(1)

openai.api_key = api_key
logger.info("OpenAI API key configured")

# Now import Flask app
try:
    logger.info("Importing Flask app...")
    from app_fixed import app, db
    from models import Vocabulary
    logger.info("Flask app and models imported successfully")
except Exception as e:
    logger.error(f"Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def translate_to_japanese(text: str, context: str = "word", script_type: str = "both") -> tuple:
    """
    Translate text to Japanese using OpenAI API.
    
    Args:
        text: Text to translate (hanzi or English)
        context: Either 'word' or 'sentence' to provide better context
        script_type: 'kanji', 'romaji', or 'both' to specify what to generate
    
    Returns:
        Tuple of (kanji, romaji) or ('', '') if translation fails
    """
    if not text or not text.strip():
        return ('', '')
    
    max_attempts = 3
    
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
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=100,
                timeout=30
            )
            
            translation_text = response.choices[0].message.content.strip()
            
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
                
        except openai.error.RateLimitError as e:
            logger.warning(f"Rate limit hit, waiting 30 seconds... (attempt {try_num}/{max_attempts})")
            time.sleep(30)
            continue
        except openai.error.APIError as e:
            logger.warning(f"API error: {e} (attempt {try_num}/{max_attempts})")
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
    with app.app_context():
        # Get all vocabulary items that need Japanese translations
        items_needing_japanese = Vocabulary.query.filter(
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
                        logger.info(f"  ✓ Word: {vocab.hanzi} → {kanji} ({romaji})")
                        translated_count += 1
                    else:
                        logger.warning(f"  ✗ Failed to translate word: {vocab.hanzi}")
                        failed_count += 1
                else:
                    skipped_count += 1
                
                # Translate the example sentence from hanzi if available
                if vocab.sent_hanzi:
                    sent_kanji, sent_romaji = translate_to_japanese(vocab.sent_hanzi, context="sentence")
                    if sent_kanji or sent_romaji:
                        vocab.sent_japanese_kanji = sent_kanji
                        vocab.sent_japanese_romaji = sent_romaji
                        logger.info(f"  ✓ Sentence: {vocab.sent_hanzi[:30]}... → {sent_kanji[:30]}... ({sent_romaji[:30]}...)")
                    else:
                        logger.warning(f"  ✗ Failed to translate sentence: {vocab.sent_hanzi}")
                
                # Save to database (or skip if dry-run)
                if not dry_run:
                    db.session.commit()
                    logger.debug("Database commit successful")
                else:
                    logger.debug("(Dry run - not saving)")
                
            except Exception as e:
                logger.error(f"Error processing {vocab.hanzi}: {e}")
                if not dry_run:
                    db.session.rollback()
                failed_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration complete!")
        logger.info("=" * 60)
        logger.info(f"  ✓ Successfully translated: {translated_count}")
        logger.info(f"  ⊘ Skipped: {skipped_count}")
        logger.info(f"  ✗ Failed: {failed_count}")
        logger.info(f"  Total processed: {i}")
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

