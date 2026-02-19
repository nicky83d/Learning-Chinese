import argparse
import json
import logging
import os
import re
import time
from typing import Optional, Tuple

import openai
from sqlalchemy import or_, and_

from app_fixed import app, db, Vocabulary, create_tables_and_populate


logger = logging.getLogger("backfill_japanese")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _has_japanese_value(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _extract_json_payload(text: str) -> Optional[dict]:
    text = (text or "").strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _translate_to_japanese(text: str, is_sentence: bool = False) -> Tuple[str, str]:
    prompt_type = "Chinese sentence" if is_sentence else "Chinese word or short phrase"
    prompt = f"""
Translate this {prompt_type} to natural Japanese.

Input:
{text}

Return ONLY valid JSON object with this exact shape:
{{"kanji":"...", "romaji":"..."}}

Rules:
- kanji can include kana as needed
- romaji must be lowercase Hepburn style
- no extra keys, no markdown, no explanation
""".strip()

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=180 if is_sentence else 80,
    )

    content = (completion.choices[0].message.content or "").strip()
    payload = _extract_json_payload(content)
    if not payload:
        raise RuntimeError(f"Could not parse translation JSON: {content[:200]}")

    kanji = (payload.get("kanji") or "").strip()
    romaji = (payload.get("romaji") or "").strip()
    if not kanji or not romaji:
        raise RuntimeError(f"Incomplete translation payload: {payload}")

    return kanji[:200], romaji[:200]


def _build_missing_query(only_approved: bool):
    conditions = [
        or_(Vocabulary.japanese_kanji == None, Vocabulary.japanese_kanji == ""),
        and_(
            Vocabulary.sent_hanzi != None,
            Vocabulary.sent_hanzi != "",
            or_(Vocabulary.sent_japanese_kanji == None, Vocabulary.sent_japanese_kanji == ""),
        ),
    ]

    q = Vocabulary.query.filter(or_(*conditions), Vocabulary.is_hidden != True)
    if only_approved:
        q = q.filter(Vocabulary.is_approved == True)
    return q


def main():
    parser = argparse.ArgumentParser(description="Backfill missing Japanese word/sentence fields in vocabulary.")
    parser.add_argument("--limit", type=int, default=500, help="Max number of rows to process")
    parser.add_argument("--batch-commit", type=int, default=25, help="Commit every N rows")
    parser.add_argument("--sleep", type=float, default=0.25, help="Sleep between API calls (seconds)")
    parser.add_argument("--only-approved", action="store_true", help="Only process approved rows")
    parser.add_argument("--no-sentences", action="store_true", help="Do not backfill sentence Japanese")
    parser.add_argument("--count-only", action="store_true", help="Only print counts, do not process")
    parser.add_argument("--dry-run", action="store_true", help="Simulate updates without writing to DB")
    args = parser.parse_args()

    with app.app_context():
        create_tables_and_populate()

        query = _build_missing_query(args.only_approved)
        total_missing = query.count()
        logger.info(f"Rows with missing Japanese fields: {total_missing}")

        if args.count_only:
            return

        rows = query.order_by(Vocabulary.id.asc()).limit(max(args.limit, 1)).all()
        if not rows:
            logger.info("Nothing to backfill.")
            return

        api_key = os.getenv("OPENAI_API_KEY") or app.config.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for backfill (unless using --count-only).")
        openai.api_key = api_key

        updated_rows = 0
        word_updates = 0
        sentence_updates = 0
        failed = 0

        for index, row in enumerate(rows, start=1):
            changed = False
            try:
                # Backfill main word
                if not _has_japanese_value(row.japanese_kanji) and (row.hanzi or "").strip():
                    kanji, romaji = _translate_to_japanese(row.hanzi, is_sentence=False)
                    row.japanese_kanji = kanji
                    row.japanese_romaji = romaji
                    changed = True
                    word_updates += 1
                    time.sleep(max(args.sleep, 0.0))

                # Backfill sentence
                if (
                    not args.no_sentences
                    and not _has_japanese_value(row.sent_japanese_kanji)
                    and (row.sent_hanzi or "").strip()
                ):
                    sent_kanji, sent_romaji = _translate_to_japanese(row.sent_hanzi, is_sentence=True)
                    row.sent_japanese_kanji = sent_kanji
                    row.sent_japanese_romaji = sent_romaji
                    changed = True
                    sentence_updates += 1
                    time.sleep(max(args.sleep, 0.0))

                if changed:
                    updated_rows += 1

                if index % max(args.batch_commit, 1) == 0:
                    if args.dry_run:
                        db.session.rollback()
                    else:
                        db.session.commit()
                    logger.info(f"Progress: {index}/{len(rows)} | updated_rows={updated_rows} failed={failed}")

            except Exception as error:
                failed += 1
                db.session.rollback()
                logger.warning(f"Failed row id={row.id}: {error}")

        if args.dry_run:
            db.session.rollback()
            logger.info("Dry run complete (no DB writes).")
        else:
            db.session.commit()
            logger.info("Backfill commit complete.")

        logger.info(
            f"Summary: scanned={len(rows)}, updated_rows={updated_rows}, "
            f"word_updates={word_updates}, sentence_updates={sentence_updates}, failed={failed}"
        )


if __name__ == "__main__":
    main()
