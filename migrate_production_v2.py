#!/usr/bin/env python3
"""
Production migration script for Japanese translations.
Robust version with better error handling and logging.
"""
import os
import sys
import time
import requests
import logging

# Setup logging to stdout (will be captured by Cloud Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("=" * 70)
        logger.info("Japanese Translation Migration (Production - Simplified)")
        logger.info("=" * 70)
        
        # Get configuration from environment
        api_key = os.environ.get('OPENAI_API_KEY', '').strip()
        db_url = os.environ.get('DATABASE_URL', '').strip()
        
        if not api_key:
            logger.error("ERROR: OPENAI_API_KEY environment variable not set")
            return 1
        
        if not db_url:
            logger.error("ERROR: DATABASE_URL environment variable not set")
            return 1
        
        logger.info(f"API Key configured: {len(api_key)} characters")
        logger.info(f"Database URL: {db_url[:60]}...")
        
        # Import SQLAlchemy
        logger.info("Importing SQLAlchemy...")
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            logger.info("SQLAlchemy imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import SQLAlchemy: {e}")
            return 1
        
        # Connect to database
        logger.info("Connecting to production database...")
        try:
            # Create engine with minimal options for debugging
            engine = create_engine(
                db_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            logger.info("Testing database connection...")
            with engine.connect() as test_conn:
                test_result = test_conn.execute(text("SELECT 1"))
                test_val = test_result.scalar()
                logger.info(f"Database connection successful (test query returned: {test_val})")
        except Exception as e:
            logger.error(f"Failed to connect to database: {type(e).__name__}: {e}")
            logger.error("This is likely due to:")
            logger.error("  1. Incorrect database URL format")
            logger.error("  2. Network connectivity issues")
            logger.error("  3. Missing database driver (pg8000)")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return 1
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query items needing translation
        logger.info("Fetching vocabulary items needing Japanese translations...")
        try:
            result = session.execute(text("""
                SELECT id, hanzi, pinyin, sent_hanzi 
                FROM vocabulary 
                WHERE (japanese_kanji = '' OR japanese_kanji IS NULL)
                   OR (japanese_romaji = '' OR japanese_romaji IS NULL)
                LIMIT 10
                ORDER BY id
            """))
            items = result.fetchall()
            logger.info(f"Found {len(items)} items needing translation (limited to 10 for testing)")
        except Exception as e:
            logger.error(f"Error fetching items: {type(e).__name__}: {e}")
            session.close()
            return 1
        
        if not items:
            logger.info("All items already have Japanese translations!")
            session.close()
            return 0
        
        logger.info(f"Starting translation process...")
        
        # Simple translation test
        logger.info("Testing OpenAI API...")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Translate '你' to Japanese. Reply with only 'kanji: [result] romaji: [result]'"}],
            "temperature": 0.3,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=test_payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"OpenAI API test successful")
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return 1
        except requests.exceptions.Timeout:
            logger.error("OpenAI API request timed out")
            return 1
        except Exception as e:
            logger.error(f"OpenAI API test failed: {type(e).__name__}: {e}")
            return 1
        
        logger.info(f"\nWould translate {len(items)} items. Test passed!")
        logger.info("Migration script is ready to run.")
        session.close()
        return 0
        
    except Exception as e:
        logger.exception(f"Unexpected error in main: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    logger.info(f"\nMigration script exit code: {exit_code}")
    sys.exit(exit_code)
