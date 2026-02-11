# Japanese Language Support - Implementation Guide  

## Overview

Your language learning application now supports **Japanese** translations alongside Chinese, Pinyin, English, and French. This document outlines the changes and how to complete the Japanese translation backfill.

## What's Changed

### 1. Database Schema Updates (`models.py`)

Added four new columns to the `Vocabulary` model:
- `japanese_kanji` - Japanese characters (kanji/hiragana)
- `japanese_romaji` - Romanized Japanese (ローマ字)
- `sent_japanese_kanji` - Japanese example sentence (kanji/hiragana)
- `sent_japanese_romaji` - Romanized example sentence

Added two new columns to the `PracticeResult` model:
- `word_japanese_kanji` - Japanese word during practice sessions
- `word_japanese_romaji` - Japanese romanization during practice sessions

All new columns are optional and default to empty strings, so the app works fine without translations.

### 2. Code Updates (`app_fixed.py`)

Updated all endpoints that deal with vocabulary data to include Japanese:
- **Vocabulary search** - Now searches in Japanese as well as English, French, Pinyin, Hanzi
- **Random word endpoints** - Include Japanese in returned data
- **Practice endpoints** - Store and return Japanese translations during practice
- **Admin update endpoint** - Can save/update Japanese translations  
- **Database schema creation** - Includes `word_japanese` column in  `practice_result` table

### 3. Data Extraction (`extract_data.py`)

Updated to handle three formats:
- **8-column tuples** (existing format): `(hanzi, pinyin, english, french, sent_hanzi, sent_pinyin, sent_english, sent_french)`
- **10-column tuples** (legacy single Japanese): adds `japanese, sent_japanese` between french and sent_hanzi
- **12-column tuples** (new format with dual Japanese): `(hanzi, pinyin, english, french, japanese_kanji, japanese_romaji, sent_hanzi, sent_pinyin, sent_english, sent_french, sent_japanese_kanji, sent_japanese_romaji)`

Existing data without Japanese will have empty strings for Japanese columns.

## Model Comparison

Perfect parallel structure:

| Language | Character/Visual System | Romanization System |
|----------|----------------------|-------------------|
| Chinese  | `hanzi`             | `pinyin`          |
| Japanese | `japanese_kanji`    | `japanese_romaji` |
| English  | `english` (no separate column) | N/A |
| French   | `french` (no separate column) | N/A |

## How to Backfill Japanese Translations

### Step 1: Prepare the Database

When you next start the app, it will automatically create the new database columns. No manual migration is needed for the schema.

### Step 2: Run the Japanese Translation Migration

Two options are available:

#### Option A: Full Migration (Recommended)
Automatically translates all vocabulary to Japanese (both kanji and romaji) using OpenAI's GPT-3.5-turbo API:

```bash
python migrate_add_japanese.py
```

This will:
1. Check all vocabulary items
2. For each item without Japanese:
   - Translate the hanzi word to Japanese kanji and romaji
   - Translate the example sentence to Japanese kanji and romaji
3. Save translations to the database
4. Log all progress to console and `migrate_japanese.log`

**Time estimate**: ~200-300 vocabulary items = 30-60 minutes (respects API rate limits)

**Cost estimate**: ~$1.00-$2.00 using gpt-3.5-turbo (double cost of single-system, still very economical)

#### Option B: Dry Run (Testing)
See what would be translated without saving changes:

```bash
python migrate_add_japanese.py --dry-run
```

This shows a preview of translations but doesn't update the database.

### Step 3: Verify Translations

After migration completes:
1. Start your app: `python app_fixed.py`
2. Search for a word you know was translated
3. View the word details - Japanese should now appear
4. Try searching by Japanese translation to confirm it's indexed

## Frontend Updates Needed

If you have a web frontend, update it to:

1. **Display both Japanese systems** in vocabulary lists and word details:
   ```html
   <div class="japanese-kanji">{{ word.japanese_kanji }}</div>
   <div class="japanese-romaji">{{ word.japanese_romaji }}</div>
   <div class="japanese-sentence-kanji">{{ word.sent_japanese_kanji }}</div>
   <div class="japanese-sentence-romaji">{{ word.sent_japanese_romaji }}</div>
   ```

2. **Add Japanese to search filters** (if you have a dropdown):
   ```html
   <option value="japanese_kanji">Japanese (Kanji)</option>
   <option value="japanese_romaji">Japanese (Romaji)</option>
   ```

3. **Update practice cards** to show/ask about both Japanese systems

4. **Show Japanese in quiz explanations** - display both kanji and romaji for complete learning

## Migration Script Details

### Features
- ✓ Automatic retry on API failures (3 attempts per word)
- ✓ Rate limiting respect (waits 30s on rate limit)
- ✓ Detailed logging to file + console
- ✓ Can be interrupted safely with Ctrl+C
- ✓ Dry-run mode for testing  
- ✓ Smart error handling

### Logs
Check `migrate_japanese.log` to see:
- Which words were successfully translated
- Which words failed  
- API errors and retry attempts
- Summary statistics

## API Endpoints - Updated Response Format

All vocabulary endpoints now return 6 languages instead of 4 (with 2 Japanese systems):

### Before (4 languages):
```json
{
  "id": 1,
  "hanzi": "我",
  "pinyin": "wǒ",
  "english": "I / me",
  "french": "je / moi",
  "sent_hanzi": "我是学生。",
  "sent_pinyin": "Wǒ shì xuéshēng.",
  "sent_english": "I am a student.",
  "sent_french": "Je suis étudiant.",
  "section": "Pronouns & Basics"
}
```

### After (6 languages with dual Japanese):
```json
{
  "id": 1,
  "hanzi": "我",
  "pinyin": "wǒ",
  "english": "I / me",
  "french": "je / moi",
  "japanese_kanji": "私",
  "japanese_romaji": "watashi",
  "sent_hanzi": "我是学生。",
  "sent_pinyin": "Wǒ shì xuéshēng.",
  "sent_english": "I am a student.",
  "sent_french": "Je suis étudiant.",
  "sent_japanese_kanji": "私は学生です。",
  "sent_japanese_romaji": "watashi wa gakusei desu.",
  "section": "Pronouns & Basics"
}
```

## Troubleshooting

### Migration Hangs or Crashes
- Make sure `.env` file has `OPENAI_API_KEY` set
- Check internet connection (API calls are required)
- Try `--dry-run` first to test without database changes
- Check `migrate_japanese.log` for specific errors

### Some Words Have Incomplete Japanese
- Some words may have only kanji or only romaji if the translation failed partially
- Re-run migration to retry failed translations
- Can manually add missing parts in admin panel if needed

### Frontend Not Showing Japanese
- Make sure your frontend code displays both `japanese_kanji` and `japanese_romaji` fields
- Check browser console for JavaScript errors
- Verify API is returning both Japanese formats in the response
- If displaying romanization, you can combine both: `{{ word.japanese_kanji }} ({{ word.japanese_romaji }})`

## Example Usage in Frontend

```javascript
// Fetch vocabulary with Japanese
async function getWord(wordId) {
  const response = await fetch(`/random_word`);
  const word = await response.json();
  
  // Now includes both Japanese systems
  console.log(word.japanese_kanji);        // "私"
  console.log(word.japanese_romaji);       // "watashi"
  console.log(word.sent_japanese_kanji);   // "私は学生です。"
  console.log(word.sent_japanese_romaji);  // "watashi wa gakusei desu."
}
```

## Editable Fields in Admin

The admin panel can now edit Japanese translations in two parts:
- Japanese Kanji (the character system)
- Japanese Romaji (the romanized system)

These can be manually corrected individually if the automatic translation isn't perfect.

## Need Help?

If issues occur during migration:
1. Check `migrate_japanese.log` for details
2. Ensure OpenAI API key is valid and has quota
3. Try running again - transient API errors will be retried automatically
4. If critical words are missing Japanese, you can edit them in the admin panel

Enjoy learning Japanese! 🎌
