from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from models import db, Vocabulary, PhotoLog, User, UserVocabulary
from extract_data import extract_all_rows
from config import get_config
import unicodedata
import os
from google.cloud import vision
from google.cloud import speech
import openai
import re
import json
import time
import logging
from datetime import datetime
from math import ceil
from sqlalchemy import text
from io import BytesIO
from PIL import Image, ImageOps
from functools import wraps
from dotenv import load_dotenv
from urllib.parse import urlencode
import requests
import secrets
import bcrypt

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)

# Get configuration
config_class = get_config()
if os.environ.get('FLASK_ENV') == 'production':
    config_class.validate()

app = Flask(__name__)
app.config.from_object(config_class)

# Initialize extensions
db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['RATELIMIT_STORAGE_URL']
)

# Setup logging
logs_dir = app.config['LOG_DIR']
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, f"photo_processing_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))

fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Initialize OpenAI
if app.config['OPENAI_API_KEY']:
    openai.api_key = app.config['OPENAI_API_KEY']
else:
    logger.warning("OPENAI_API_KEY not set - photo upload features will not work")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

_db_populated = False

# --- helpers for language detection ---
_CHINESE_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")

def has_chinese(s: str) -> bool:
    """True if string contains any CJK Han character."""
    return bool(_CHINESE_RE.search(s or ""))

# Authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.method == 'GET' and request.accept_mimetypes.accept_html:
                return redirect(url_for('admin_login'))
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def _get_google_redirect_uri() -> str:
    configured = app.config.get('GOOGLE_REDIRECT_URI')
    if configured:
        return configured
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    host = request.headers.get('X-Forwarded-Host', request.host)
    return f"{scheme}://{host}/auth/google/callback"

def fold_pinyin(text: str, umlaut_to: str = 'u') -> str:
    if not text:
        return ''
    s = text.strip().lower()
    s = s.replace('u:', 'ü')
    if umlaut_to == 'u':
        s = s.replace('v', 'u')
    s = unicodedata.normalize('NFD', s)
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == 'u' and i + 1 < len(s) and s[i + 1] == '\u0308':
            out.append('v' if umlaut_to == 'v' else 'u')
            i += 2
            while i < len(s) and unicodedata.category(s[i]) == 'Mn':
                i += 1
            continue
        if unicodedata.category(ch) == 'Mn':
            i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)

def pinyin_query_variants(query: str) -> tuple[str, str]:
    q = (query or '').strip().casefold()
    if not q:
        return ('', '')
    return (fold_pinyin(q, 'u'), fold_pinyin(q, 'v'))


def fold_text(text: str) -> str:
    """Case- and accent-insensitive folding for search (é -> e, Ü -> u, ß -> ss)."""
    if not text:
        return ''
    s = unicodedata.normalize('NFKD', text)
    s = s.casefold()
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')

def create_tables_and_populate():
    global _db_populated
    if _db_populated:
        # Ensure all rows are approved even if already populated
        with app.app_context():
            Vocabulary.query.filter(Vocabulary.is_approved != True).update({'is_approved': True})
            db.session.commit()
        return
    with app.app_context():
        db.create_all()
        if Vocabulary.query.count() == 0:
            logger.info("Importing vocabulary data into database...")
            rows = extract_all_rows()
            if rows:
                for r in rows:
                    entry = Vocabulary(
                        section=r["section"],
                        hanzi=r["hanzi"] or '',
                        pinyin=r["pinyin"] or '',
                        english=r["english"] or '',
                        french=r["french"] or '',
                        sent_hanzi=r["sent_hanzi"] or '',
                        sent_pinyin=r["sent_pinyin"] or '',
                        sent_english=r["sent_english"] or '',
                        sent_french=r["sent_french"] or '',
                        is_approved=True,
                    )
                    db.session.add(entry)
                db.session.commit()
                # Safety: ensure all seeded rows are marked approved so they appear in search
                Vocabulary.query.filter(Vocabulary.is_approved != True).update({'is_approved': True})
                db.session.commit()
                logger.info(f"Imported {len(rows)} items.")
            else:
                logger.info("No data to import.")
        else:
            # Ensure any existing rows (e.g., after migrations) are approved
            Vocabulary.query.filter(Vocabulary.is_approved != True).update({'is_approved': True})
            db.session.commit()
        _db_populated = True

@app.route('/')
def index():
    create_tables_and_populate()
    return render_template('index.html')


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'
    
    return jsonify({
        "status": "healthy" if db_status == 'healthy' else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "environment": app.config.get('FLASK_ENV', 'unknown'),
        "version": "1.0.0"
    }), 200 if db_status == 'healthy' else 503



@app.route('/search')
def search():
    # Get parameters from the frontend request
    query = request.args.get('q', '').strip()
    field = request.args.get('field', 'all')
    
    # Get all approved vocabulary entries
    all_entries = Vocabulary.query.filter_by(is_approved=True).all()
    
    # Filter in Python with accent-insensitive comparison
    results = []
    if query:
        folded_query = fold_text(query)
        
        for entry in all_entries:
            match = False
            if field == 'english':
                match = folded_query in fold_text(entry.english)
            elif field == 'french':
                match = folded_query in fold_text(entry.french)
            elif field == 'pinyin':
                match = folded_query in fold_text(entry.pinyin)
            else:
                # "All fields" search: looks in English, French, Pinyin, and Hanzi
                match = (
                    folded_query in fold_text(entry.english) or
                    folded_query in fold_text(entry.french) or
                    folded_query in fold_text(entry.pinyin) or
                    query in entry.hanzi  # Hanzi stays as-is (no accent folding)
                )
            
            if match:
                results.append(entry)
    else:
        # If query is empty, return all entries
        results = all_entries
    
    # Convert database objects to a list of dictionaries for the frontend (added missing sentences)
    return jsonify([
        {
            "id": r.id,
            "section": r.section,
            "hanzi": r.hanzi,
            "pinyin": r.pinyin,
            "english": r.english,
            "french": r.french,
            "sent_hanzi": r.sent_hanzi,
            "sent_pinyin": r.sent_pinyin,
            "sent_english": r.sent_english,
            "sent_french": r.sent_french
        } for r in results
    ])

@app.route('/sections')
def get_sections():
    """Returns a list of unique categories for the dropdown filter."""
    sections = db.session.query(Vocabulary.section).distinct().all()
    # Flatten the list of tuples and remove None/Empty values
    return jsonify(sorted([s[0] for s in sections if s[0]]))

@app.route('/random_word')
def random_word():
    """Returns a random vocabulary word for practice."""
    # Get a random word from the database
    from sqlalchemy import func
    word = db.session.query(Vocabulary).filter_by(is_approved=True).order_by(func.random()).first()
    
    if not word:
        return jsonify({"error": "No words found"}), 404
    
    return jsonify({
        "id": word.id,
        "hanzi": word.hanzi,
        "pinyin": word.pinyin,
        "english": word.english,
        "french": word.french,
        "sent_hanzi": word.sent_hanzi,
        "sent_pinyin": word.sent_pinyin,
        "sent_english": word.sent_english,
        "sent_french": word.sent_french,
        "section": word.section
    })

@app.route('/random_words')
def random_words():
    """Returns multiple random vocabulary words for practice, optionally filtered by section."""
    from sqlalchemy import func
    
    section = request.args.get('section', 'all')
    limit = int(request.args.get('limit', 10))
    
    # Start with approved words query
    query = db.session.query(Vocabulary).filter_by(is_approved=True)
    
    # Filter by section if not 'all'
    if section and section != 'all':
        query = query.filter(Vocabulary.section == section)
    
    # Get random words with limit
    words = query.order_by(func.random()).limit(limit).all()
    
    if not words:
        return jsonify({"error": "No words found"}), 404
    
    return jsonify([{
        "id": word.id,
        "hanzi": word.hanzi,
        "pinyin": word.pinyin,
        "english": word.english,
        "french": word.french,
        "sent_hanzi": word.sent_hanzi,
        "sent_pinyin": word.sent_pinyin,
        "sent_english": word.sent_english,
        "sent_french": word.sent_french,
        "section": word.section
    } for word in words])

# Route to update a word (called by your Save button in the modal)
@app.route('/update', methods=['POST'])
def update_word():
    create_tables_and_populate()
    data = request.get_json(silent=True) or {}
    word_id = (data.get('id') or '').strip()

    if not word_id:
        return jsonify({"ok": False, "error": "id is required for updates"}), 400

    vocab = db.session.get(Vocabulary, word_id)
    if not vocab:
        return jsonify({"ok": False, "error": "Word not found"}), 404

    # Update fields (keep existing if missing)
    vocab.hanzi = (data.get('hanzi', vocab.hanzi) or '').strip()
    vocab.pinyin = (data.get('pinyin', vocab.pinyin) or '').strip()
    vocab.english = (data.get('english', vocab.english) or '').strip()
    vocab.french = (data.get('french', vocab.french) or '').strip()
    vocab.section = (data.get('section', vocab.section) or '').strip()
    vocab.sent_hanzi = (data.get('sent_hanzi', vocab.sent_hanzi) or '').strip()
    vocab.sent_pinyin = (data.get('sent_pinyin', vocab.sent_pinyin) or '').strip()
    vocab.sent_english = (data.get('sent_english', vocab.sent_english) or '').strip()
    vocab.sent_french = (data.get('sent_french', vocab.sent_french) or '').strip()

    if not vocab.section:
        return jsonify({"ok": False, "error": "Section cannot be empty"}), 400

    db.session.commit()
    return jsonify({"ok": True, "status": "success", "id": vocab.id})


@app.route('/delete', methods=['POST'])
def delete_word():
    create_tables_and_populate()
    data = request.get_json(silent=True) or {}
    word_id = data.get('id')

    if not word_id:
        return jsonify({"ok": False, "error": "id is required"}), 400

    vocab = db.session.get(Vocabulary, word_id)
    if not vocab:
        return jsonify({"ok": False, "error": "Word not found"}), 404

    db.session.delete(vocab)
    db.session.commit()
    return jsonify({"ok": True, "status": "deleted"})


@app.route('/add_word', methods=['POST'])
def add_word():
    create_tables_and_populate()
    payload = request.get_json(silent=True) or request.form.to_dict()
    def s(key): return (payload.get(key) or "").strip()

    section = s("section")
    if not section:
        return jsonify({"ok": False, "error": "Section required"}), 400
    if not (s("hanzi") or s("pinyin") or s("english") or s("french")):
        return jsonify({"ok": False, "error": "At least one word field required"}), 400

    entry = Vocabulary(
        section=section,
        hanzi=s("hanzi"),
        pinyin=s("pinyin"),
        english=s("english"),
        french=s("french"),
        sent_hanzi=s("sent_hanzi"),
        sent_pinyin=s("sent_pinyin"),
        sent_english=s("sent_english"),
        sent_french=s("sent_french"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"ok": True, "id": entry.id})






        


# ====================== PHOTO PROCESSING (FIXED) ======================

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s[:n] if len(s) > n else s

def _extract_first_json_array(text: str):
    """Robustly extract the first valid JSON array from model output, even if wrapped in markdown or extra text."""
    if not text:
        return None
    text = text.strip()

    # Remove common markdown code fences
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try parsing the entire response first
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
    except Exception:
        pass

    # Find the outermost array brackets
    depth = 0
    start = -1
    for i, c in enumerate(text):
        if c == '[':
            if depth == 0:
                start = i
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0 and start != -1:
                chunk = text[start:i+1]
                try:
                    obj = json.loads(chunk)
                    if isinstance(obj, list):
                        return obj
                except Exception:
                    pass
    return None


def _get_best_category_for_word(hanzi: str, english: str, french: str) -> str:
    """Use LLM to determine the most appropriate category for a word."""
    try:
        # Get existing categories
        sections = db.session.query(Vocabulary.section).filter_by(is_approved=True).distinct().all()
        category_list = [s[0] for s in sections if s[0]]
        
        if not category_list:
            return "Photo Imports"
        
        prompt = f"""Given this Chinese vocabulary word, select the MOST appropriate category from the list below.
Return ONLY the category name, nothing else.

Word:
- Chinese: {hanzi}
- English: {english}
- French: {french}

Available categories:
{", ".join(category_list)}

If none fit well, return: Photo Imports

Your answer (category name only):"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        category = response.choices[0].message.content.strip().strip('"\'')
        
        # Validate it's in our list
        if category in category_list:
            return category
        return "Photo Imports"
    except Exception as e:
        logger.warning(f"Could not determine category: {e}")
        return "Photo Imports"


def _llm_merge_lines_to_entries(lines: list[str], input_lang: str = 'chinese') -> list[dict]:
    """Use LLM to merge OCR lines into clean vocabulary entries with all fields."""
    api_key = os.getenv("OPENAI_API_KEY") or getattr(openai, "api_key", None)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    def make_prompt(lang: str) -> str:
        if lang == 'chinese':
            return f"""You are an expert at cleaning messy OCR output from Chinese vocabulary lists.

Your task: Return EXACTLY and ONLY a valid JSON array of vocabulary entries.
NO explanations, NO markdown, NO extra text, NO notes.

Each entry must be a JSON object with these exact keys (all strings, all required):
- "hanzi": Chinese characters (must contain at least one Han character)
- "pinyin": correct tone-marked pinyin (spaces between words for phrases)
- "english": English translation
- "french": French translation (translate from English if missing)
- "sent_hanzi": short natural example sentence using the word
- "sent_pinyin": pinyin for the example sentence
- "sent_english": English translation of the example sentence
- "sent_french": French translation of the example sentence

Rules:
- Produce ONE entry per individual word. If a line has multiple words (e.g., "书房 比 卧室 大"), split it into separate entries for every word (书房, 比, 卧室, 大) with their own translations and example sentences. Do NOT return the whole multi-word phrase as a single entry unless it is a fixed expression.
- Merge scattered lines that belong together (e.g., hanzi on one line, pinyin on next, English below).
- Fix obvious OCR errors in pinyin and Latin text.
- Ignore headings, page numbers, junk, single letters.
- Create a simple natural example sentence for each word if none exists.
- No duplicate entries (same hanzi or same meaning).

OCR lines:
{json.dumps(lines, ensure_ascii=False, indent=None)}

Return ONLY the JSON array. Start directly with [.

Example of correct output:
[{{"hanzi": "头", "pinyin": "tóu", "english": "head", "french": "tête", "sent_hanzi": "我的头疼。", "sent_pinyin": "Wǒ de tóu téng.", "sent_english": "My head hurts.", "sent_french": "J'ai mal à la tête."}}]"""
        if lang == 'french':
            return f"""You are an expert at cleaning messy OCR output from French-Chinese vocabulary lists.

Return EXACTLY and ONLY a valid JSON array. No extra text whatsoever.

Each entry must have:
- "french": French headword
- "english": English translation
- "hanzi": Chinese translation (must contain Han characters)
- "pinyin": tone-marked pinyin
- "sent_french": example sentence in French
- "sent_english": English translation of sentence
- "sent_hanzi": Chinese sentence
- "sent_pinyin": pinyin for Chinese sentence

Merge related lines, fix OCR errors, generate missing parts, no duplicates.

OCR lines:
{json.dumps(lines, ensure_ascii=False, indent=None)}

Return ONLY the JSON array starting with [."""
        raise ValueError("Unsupported input_lang")

    def call_llm(prompt: str, temp: float = 0.2, max_tokens: int = 1500):
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            error_msg = str(e).lower()
            if "dns" in error_msg or "origin" in error_msg or "cloudflare" in error_msg or "cannot resolve" in error_msg:
                raise RuntimeError("Cannot reach OpenAI API. Check internet connection and firewall settings.")
            elif "401" in error_msg or "unauthorized" in error_msg or "api key" in error_msg.lower():
                raise RuntimeError("OpenAI API key is invalid. Check OPENAI_API_KEY environment variable.")
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                raise RuntimeError("OpenAI API rate limit reached. Please wait a moment and try again.")
            else:
                raise RuntimeError(f"OpenAI API error: {error_msg[:100]}")

    prompt = make_prompt(input_lang)
    text = call_llm(prompt)
    entries = _extract_first_json_array(text)

    if entries is None:
        # Retry once with a stricter reminder
        retry_prompt = prompt + "\n\nYour previous attempt was invalid. Respond with ONLY a JSON array. No text outside the brackets."
        text = call_llm(retry_prompt, temp=0.1, max_tokens=1800)
        entries = _extract_first_json_array(text)

    if entries is None:
        logger.error("Raw LLM output for debugging:")
        logger.error(text[:2000])  # Log more context
        raise RuntimeError("Could not parse JSON from LLM output.")

    # Clean and validate
    cleaned = []
    seen_hanzi = set()
    seen_pinyin = set()
    seen_english = set()
    seen_french = set()
    for e in entries:
        if not isinstance(e, dict):
            continue
        hanzi = _normalize_ws(e.get("hanzi", ""))
        if not hanzi or not has_chinese(hanzi):
            continue
        norm_hanzi = unicodedata.normalize("NFKC", hanzi)
        norm_pinyin = fold_text(e.get("pinyin", ""))
        norm_english = fold_text(e.get("english", ""))
        norm_french = fold_text(e.get("french", ""))

        # Deduplicate across all key fields (not just hanzi)
        if (
            (norm_hanzi and norm_hanzi in seen_hanzi) or
            (norm_pinyin and norm_pinyin in seen_pinyin) or
            (norm_english and norm_english in seen_english) or
            (norm_french and norm_french in seen_french)
        ):
            continue

        item = {
            "hanzi": _clip(hanzi, 50),
            "pinyin": _clip(_normalize_ws(e.get("pinyin", "")), 100),
            "english": _clip(_normalize_ws(e.get("english", "")), 200),
            "french": _clip(_normalize_ws(e.get("french", "")), 200),
            "sent_hanzi": _clip(_normalize_ws(e.get("sent_hanzi", "")), 100),
            "sent_pinyin": _clip(_normalize_ws(e.get("sent_pinyin", "")), 150),
            "sent_english": _clip(_normalize_ws(e.get("sent_english", "")), 200),
            "sent_french": _clip(_normalize_ws(e.get("sent_french", "")), 200),
        }
        # Require core fields
        if all(item.values()):
            if norm_hanzi:
                seen_hanzi.add(norm_hanzi)
            if norm_pinyin:
                seen_pinyin.add(norm_pinyin)
            if norm_english:
                seen_english.add(norm_english)
            if norm_french:
                seen_french.add(norm_french)
            cleaned.append(item)

    return cleaned


def _find_existing_vocab(entry: dict):
    hanzi = entry.get("hanzi") or ""
    pinyin = (entry.get("pinyin") or "").strip()
    english = (entry.get("english") or "").strip()
    french = (entry.get("french") or "").strip()

    q = Vocabulary.query
    if hanzi:
        hit = q.filter(Vocabulary.hanzi == hanzi).first()
        if hit:
            return hit
    if pinyin:
        hit = q.filter(Vocabulary.pinyin.ilike(pinyin)).first()
        if hit:
            return hit
    if english:
        hit = q.filter(Vocabulary.english.ilike(english)).first()
        if hit:
            return hit
    if french:
        hit = q.filter(Vocabulary.french.ilike(french)).first()
        if hit:
            return hit
    return None


def _upsert_full_entry(section: str, entry: dict):
    row = _find_existing_vocab(entry)
    created = False
    if row is None:
        row = Vocabulary(section=section)
        created = True

    if not getattr(row, "section", None):
        row.section = section

    for field, maxlen in [
        ("hanzi", 50), ("pinyin", 100), ("english", 200), ("french", 200),
        ("sent_hanzi", 100), ("sent_pinyin", 150), ("sent_english", 200), ("sent_french", 200),
    ]:
        new_val = (entry.get(field) or "").strip()
        if new_val and not (getattr(row, field) or "").strip():
            setattr(row, field, _clip(new_val, maxlen))

    if created:
        db.session.add(row)
        db.session.flush()  # populate row.id before returning
    else:
        # Ensure existing rows are attached so we can read their ids reliably
        db.session.flush()

    return created, row.id


def _extract_word_boxes(vision_response, image_path=None, image_width_override=None, image_height_override=None):
    """
    Extract word-level bounding boxes from Google Vision API response.
    Returns tuple: (word_boxes, image_width, image_height)
    where vertices are normalized to [0-1] for flexible canvas rendering.
    """
    
    word_boxes = []
    if not vision_response or not vision_response.text_annotations:
        return word_boxes, 1, 1
    
    # Prefer provided dimensions (already EXIF-rotated), fall back to file then Vision
    image_width = image_width_override or 1
    image_height = image_height_override or 1
    
    if (image_width == 1 or image_height == 1) and image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            image_width, image_height = img.size
            logger.info(f"Image dimensions from file: {image_width}x{image_height}")
        except Exception as e:
            logger.warning(f"Could not get image dimensions from file: {e}")
    
    # Fall back to Vision API page dimensions if file method failed
    if image_width == 1 and image_height == 1:
        if vision_response.full_text_annotation and vision_response.full_text_annotation.pages:
            pages = vision_response.full_text_annotation.pages
            if pages:
                if hasattr(pages[0], 'width') and hasattr(pages[0], 'height'):
                    image_width = pages[0].width or 1
                    image_height = pages[0].height or 1
                    logger.info(f"Vision API page dimensions: {image_width}x{image_height}")
    
    # Skip the first annotation (full text) and process word-level annotations
    for annotation in vision_response.text_annotations[1:]:
        text = annotation.description or ""
        
        # Extract vertices
        if hasattr(annotation, 'bounding_poly') and annotation.bounding_poly:
            vertices = annotation.bounding_poly.vertices
            if vertices:
                # Normalize vertices to [0, 1]
                normalized_vertices = []
                for vertex in vertices:
                    x = (vertex.x / image_width) if image_width > 0 else 0
                    y = (vertex.y / image_height) if image_height > 0 else 0
                    normalized_vertices.append({'x': x, 'y': y})
                
                if len(word_boxes) < 3:  # Log first few boxes for debugging
                    logger.info(f"Box '{text}': raw coords {[(v.x, v.y) for v in vertices]}, normalized {normalized_vertices}")
                
                word_boxes.append({
                    'text': text,
                    'vertices': normalized_vertices
                })
    
    return word_boxes, image_width, image_height


@app.route('/process_photo', methods=['POST'])
@limiter.limit("5 per hour")
def process_photo():
    logger.info("=== PHOTO PROCESSING STARTED ===")
    create_tables_and_populate()

    # Get user IP
    user_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
    
    # Create a PhotoLog entry
    photo_log = PhotoLog(
        user_ip=user_ip,
        timestamp=datetime.utcnow()
    )

    if 'photo' not in request.files:
        photo_log.error_message = "No photo in request"
        photo_log.status = 'rejected'
        db.session.add(photo_log)
        db.session.commit()
        return jsonify({"error": "No photo"}), 400
    
    file = request.files['photo']
    if file.filename == '':
        photo_log.error_message = "Empty filename"
        photo_log.status = 'rejected'
        db.session.add(photo_log)
        db.session.commit()
        return jsonify({"error": "Empty file"}), 400

    section = request.form.get('section') or "Photo Imports"
    photo_log.section = section
    photo_log.filename = file.filename
    logger.info(f"Received: {file.filename} | section={section}")

    # Read file once, save it, and pass to Vision API
    try:
        content = file.read()
        if not content:
            photo_log.error_message = "Empty file content"
            photo_log.status = 'rejected'
            db.session.add(photo_log)
            db.session.commit()
            return jsonify({"error": "Empty file"}), 400

        # Normalize orientation (apply EXIF) so Vision boxes match displayed image
        image_width = image_height = 1
        try:
            img = Image.open(BytesIO(content))
            img = ImageOps.exif_transpose(img)
            image_width, image_height = img.size
            buffer = BytesIO()
            fmt = img.format or 'JPEG'
            img.save(buffer, format=fmt)
            content = buffer.getvalue()
            logger.info(f"Applied EXIF orientation. Final image size: {image_width}x{image_height}")
        except Exception as e:
            logger.warning(f"Could not apply EXIF orientation: {e}")

        # Save uploaded (normalized) photo for inspection
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        safe_name = file.filename or f"upload_{int(time.time())}.jpg"
        save_path = os.path.join(uploads_dir, safe_name)
        try:
            with open(save_path, 'wb') as out_f:
                out_f.write(content)
            photo_log.image_path = save_path
            logger.info(f"Saved uploaded photo to: {save_path}")
        except Exception as e:
            logger.warning(f"Could not save uploaded photo: {e}")

        image = vision.Image(content=content)
        client = vision.ImageAnnotatorClient()
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)

        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        raw_lines = [_normalize_ws(line.strip().rstrip('.,;')) for line in full_text.split('\n') if line.strip()]
        ocr_excerpt = _clip(' '.join(full_text.split()), 400)
        photo_log.ocr_text = full_text
        
        # Extract word-level bounding boxes for visualization
        word_boxes, img_width, img_height = _extract_word_boxes(response, save_path, image_width, image_height)
        photo_log.image_width = img_width
        photo_log.image_height = img_height
        logger.info(f"Extracted {len(word_boxes)} words with bounding boxes.")
        
        logger.info(f"Extracted {len(raw_lines)} OCR lines.")
        if raw_lines:
            logger.info("OCR lines:")
            for i, ln in enumerate(raw_lines, start=1):
                logger.info(f"  {i}: {ln}")

        input_lang = 'chinese' if has_chinese(full_text) else 'french'
        photo_log.detected_language = input_lang
        logger.info(f"Detected input language: {input_lang}")

        entries = _llm_merge_lines_to_entries(raw_lines, input_lang=input_lang)
        logger.info(f"LLM successfully returned {len(entries)} clean entries.")

        created_count = updated_count = 0
        ids = []
        added_words = []
        # Track whether each entry is new or existing
        for e in entries:
            # Check if word exists before upserting
            existing = _find_existing_vocab(e)
            
            # Determine best category for new words
            if not existing:
                best_category = _get_best_category_for_word(
                    e.get('hanzi', ''),
                    e.get('english', ''),
                    e.get('french', '')
                )
                word_section = best_category
            else:
                word_section = section
            
            created, vid = _upsert_full_entry(word_section, e)
            e['is_new'] = created  # Mark each entry
            
            # Clear sentence fields for existing words (save AI costs)
            if not created:
                e['sent_hanzi'] = ''
                e['sent_pinyin'] = ''
                e['sent_english'] = ''
                e['sent_french'] = ''
            
            if created:
                created_count += 1
                # Record the main word for frontend confirmation
                try:
                    added_words.append((e.get('hanzi') or e.get('english') or e.get('french') or '').strip())
                except Exception:
                    added_words.append('')
            else:
                updated_count += 1
            ids.append(vid)
        
        # Save entries with is_new flags
        photo_log.entries_json = json.dumps(entries, ensure_ascii=False)
        
        # Mark word boxes based on whether the detected words are new or existing
        # Build a set of detected text for quick lookup
        detected_words_set = set()
        for e in entries:
            hanzi = (e.get('hanzi') or '').strip()
            english = (e.get('english') or '').strip()
            french = (e.get('french') or '').strip()
            if hanzi:
                detected_words_set.add(hanzi)
            if english:
                detected_words_set.add(english)
            if french:
                detected_words_set.add(french)
        
        # Mark each word box based on whether it matches a created word
        for box in word_boxes:
            box_text = (box.get('text') or '').strip()
            # Check if this word is in a created (new) entry
            box['is_new'] = any(
                box_text.lower() in (e.get('hanzi', '') or '').lower() or
                box_text.lower() in (e.get('english', '') or '').lower() or
                box_text.lower() in (e.get('french', '') or '').lower()
                for e in entries if e.get('is_new')
            )
        
        photo_log.word_boxes_json = json.dumps(word_boxes, ensure_ascii=False)

        photo_log.created_count = created_count
        photo_log.updated_count = updated_count
        photo_log.vocab_ids = ','.join(map(str, ids))
        
        # Auto-reject if no new words were added
        if created_count == 0:
            photo_log.status = 'rejected'
            photo_log.error_message = 'No new words detected - all vocabulary already exists in database'
            logger.info(f"=== AUTO-REJECTED: No new words (updated={updated_count}) ===")
        else:
            photo_log.status = 'pending'  # Admin needs to review
        
        db.session.add(photo_log)
        db.session.commit()
        logger.info(f"=== SUCCESS: created={created_count}, updated={updated_count} ===")
        return jsonify({
            "created": created_count,
            "updated": updated_count,
            "added": created_count,  # backward-compat for older frontends
            "total_entries": len(entries),
            "ids": ids,
            "entries_preview": entries[:10],
            "added_words": [w for w in added_words],
            "detected_language": input_lang,
            "ocr_excerpt": ocr_excerpt
        })

    except Exception as e:
        photo_log.error_message = str(e)
        photo_log.status = 'rejected'
        db.session.add(photo_log)
        db.session.commit()
        logger.error(f"ERROR: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Quick OCR preview (no logging), used to show OCR + language before full processing
@app.route('/ocr_preview', methods=['POST'])
@limiter.limit("10 per hour")
def ocr_preview():
    try:
        if 'photo' not in request.files:
            return jsonify({"error": "No photo"}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"error": "Empty file"}), 400

        content = file.read()
        if not content:
            return jsonify({"error": "Empty file content"}), 400

        image = vision.Image(content=content)
        client = vision.ImageAnnotatorClient()
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)

        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        input_lang = 'chinese' if has_chinese(full_text) else 'french'
        ocr_excerpt = _clip(' '.join(full_text.split()), 400)

        return jsonify({
            "ok": True,
            "filename": file.filename,
            "ocr_excerpt": ocr_excerpt,
            "detected_language": input_lang
        })
    except Exception as e:
        logger.error(f"OCR preview error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# ====================== ADMIN ENDPOINTS ======================

# Authentication routes
@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def admin_login():
    """Admin login endpoint"""
    if request.method == 'GET':
        return render_template('admin_login.html')

    return jsonify({"error": "Use Google login"}), 400
    
@app.route('/auth/google')
def google_auth_start():
    client_id = app.config.get('GOOGLE_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        return jsonify({"error": "Google OAuth not configured"}), 500

    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    session.permanent = True

    params = {
        "client_id": client_id,
        "redirect_uri": _get_google_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account"
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    return redirect(f"{auth_url}?{urlencode(params)}")


@app.route('/auth/google/callback')
def google_auth_callback():
    error = request.args.get('error')
    if error:
        return jsonify({"error": error}), 400

    state = request.args.get('state')
    if not state or state != session.get('oauth_state'):
        return jsonify({"error": "Invalid OAuth state"}), 400

    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    client_id = app.config.get('GOOGLE_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    token_url = "https://oauth2.googleapis.com/token"
    token_resp = requests.post(token_url, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": _get_google_redirect_uri(),
        "grant_type": "authorization_code"
    }, timeout=15)

    if token_resp.status_code != 200:
        logger.error(f"Google token error: {token_resp.text}")
        return jsonify({"error": "Failed to exchange code"}), 400

    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return jsonify({"error": "Missing access token"}), 400

    userinfo_resp = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15
    )

    if userinfo_resp.status_code != 200:
        logger.error(f"Google userinfo error: {userinfo_resp.text}")
        return jsonify({"error": "Failed to fetch user info"}), 400

    userinfo = userinfo_resp.json()
    email = userinfo.get('email')
    email_verified = userinfo.get('email_verified', True)
    given_name = userinfo.get('given_name', '')
    family_name = userinfo.get('family_name', '')
    full_name = userinfo.get('name', '')

    if not email or not email_verified:
        return jsonify({"error": "Google account not verified"}), 403

    # Check if email is in allowed list for admin
    allowed_emails = app.config.get('ADMIN_ALLOWED_EMAILS', [])
    is_admin = allowed_emails and email.lower() in allowed_emails
    
    # Create or update user
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            name=full_name,
            first_name=given_name,
            is_admin=is_admin,
            is_onboarded=False
        )
        db.session.add(user)
    else:
        user.last_login = datetime.utcnow()
        user.is_admin = is_admin  # Update admin status in case allowlist changed
        user.name = full_name or user.name
        user.first_name = given_name or user.first_name
    
    db.session.commit()

    # Set session
    session['user_id'] = user.id
    session['user_email'] = email
    session['user_first_name'] = user.first_name or given_name or 'User'
    session['is_admin'] = user.is_admin
    session['admin_logged_in'] = user.is_admin  # Keep for backward compatibility
    session.pop('oauth_state', None)
    
    # Redirect to onboarding if first time, otherwise to admin if admin or home
    if not user.is_onboarded:
        return redirect(url_for('index', onboarding='true'))
    elif user.is_admin:
        return redirect(url_for('admin_page'))
    else:
        return redirect(url_for('index'))


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    session.pop('oauth_state', None)
    return jsonify({"success": True, "message": "Logged out"})


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/preferences')
def preferences_page():
    """Render user preferences page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('admin_login'))
    return render_template('preferences.html')


@app.route('/admin/check-auth')
def admin_check_auth():
    """Check if admin is logged in"""
    return jsonify({"authenticated": session.get('admin_logged_in', False)})


@app.route('/admin')
@admin_required
def admin_page():
    """Render the admin dashboard page."""
    create_tables_and_populate()
    return render_template('admin.html')


@app.route('/admin/practice')
@admin_required
def admin_practice_page():
    """Render the practice recordings admin page."""
    create_tables_and_populate()
    return render_template('admin_practice.html')


@app.route('/admin/logs')
@admin_required
def get_admin_logs():
    """Get all photo upload logs for admin review."""
    try:
        logs = PhotoLog.query.order_by(PhotoLog.timestamp.desc()).all()
        return jsonify([{
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "user_ip": log.user_ip,
            "filename": log.filename,
            "section": log.section,
            "detected_language": log.detected_language,
            "status": log.status,
            "created_count": log.created_count,
            "updated_count": log.updated_count,
            "error_message": log.error_message
        } for log in logs])
    except Exception as e:
        logger.error(f"Error fetching admin logs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/log/<int:log_id>')
@admin_required
def get_log_details(log_id):
    """Get detailed information about a specific log entry."""
    try:
        if not log_id:
            return jsonify({"error": "Invalid log ID"}), 400
            
        log = db.session.get(PhotoLog, log_id)
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        # Parse entries JSON
        entries = []
        if log.entries_json:
            try:
                entries = json.loads(log.entries_json)
            except:
                entries = []
        
        # Parse word boxes JSON
        word_boxes = []
        if log.word_boxes_json:
            try:
                word_boxes = json.loads(log.word_boxes_json)
            except:
                word_boxes = []
        
        # Get vocabulary entries if they exist
        vocab_entries = []
        if log.vocab_ids and log.vocab_ids != 'None' and log.vocab_ids.strip():
            try:
                vocab_ids = [int(vid.strip()) for vid in log.vocab_ids.split(',') if vid.strip() and vid.strip() != 'None']
                for vid in vocab_ids:
                    vocab = db.session.get(Vocabulary, vid)
                    if vocab:
                        vocab_entries.append({
                            "id": vocab.id,
                            "hanzi": vocab.hanzi,
                            "pinyin": vocab.pinyin,
                            "english": vocab.english,
                            "french": vocab.french,
                            "sent_hanzi": vocab.sent_hanzi,
                            "sent_pinyin": vocab.sent_pinyin,
                            "sent_english": vocab.sent_english,
                            "sent_french": vocab.sent_french
                        })
            except ValueError as ve:
                logger.warning(f"Invalid vocab_ids format for log {log_id}: {log.vocab_ids} - {ve}")
        
        return jsonify({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "user_ip": log.user_ip,
            "filename": log.filename,
            "image_path": log.image_path,
            "image_width": log.image_width,
            "image_height": log.image_height,
            "section": log.section,
            "ocr_text": log.ocr_text,
            "detected_language": log.detected_language,
            "entries": entries,
            "word_boxes": word_boxes,
            "vocab_entries": vocab_entries,
            "status": log.status,
            "created_count": log.created_count,
            "updated_count": log.updated_count,
            "error_message": log.error_message
        })
    except Exception as e:
        logger.error(f"Error fetching log details: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/log/<int:log_id>/validate', methods=['POST'])
@admin_required
def validate_log(log_id):
    """Mark a log entry as validated and approve its vocabulary entries."""
    try:
        log = db.session.get(PhotoLog, log_id)
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        # Approve all vocabulary entries associated with this log
        if log.vocab_ids and log.vocab_ids != 'None' and log.vocab_ids.strip():
            try:
                vocab_ids = [int(vid.strip()) for vid in log.vocab_ids.split(',') if vid.strip() and vid.strip() != 'None']
                for vid in vocab_ids:
                    vocab = db.session.get(Vocabulary, vid)
                    if vocab:
                        vocab.is_approved = True
                        logger.info(f"Approved vocabulary entry {vid}: {vocab.hanzi}")
            except Exception as ve:
                logger.warning(f"Error approving vocabulary entries: {ve}")
        
        log.status = 'validated'
        db.session.commit()
        logger.info(f"Validated log {log_id} and approved associated vocabulary entries")
        return jsonify({"success": True, "status": "validated"})
    except Exception as e:
        logger.error(f"Error validating log: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/log/<int:log_id>/reject', methods=['POST'])
@admin_required
def reject_log(log_id):
    """Mark a log entry as rejected."""
    try:
        log = db.session.get(PhotoLog, log_id)
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        log.status = 'rejected'
        db.session.commit()
        return jsonify({"success": True, "status": "rejected"})
    except Exception as e:
        logger.error(f"Error rejecting log: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/log/<int:log_id>/delete', methods=['DELETE'])
@admin_required
def delete_log(log_id):
    """Delete a log entry, its associated vocabulary entries, and the uploaded photo."""
    try:
        log = db.session.get(PhotoLog, log_id)
        if not log:
            return jsonify({"error": "Log not found"}), 404
        
        deleted_vocab_count = 0
        
        # Delete associated vocabulary entries from the database
        if log.vocab_ids and log.vocab_ids != 'None' and log.vocab_ids.strip():
            try:
                vocab_ids = [int(vid.strip()) for vid in log.vocab_ids.split(',') if vid.strip() and vid.strip() != 'None']
                logger.info(f"Attempting to delete {len(vocab_ids)} vocabulary entries: {vocab_ids}")
                for vid in vocab_ids:
                    vocab = db.session.get(Vocabulary, vid)
                    if vocab:
                        logger.info(f"Deleting vocabulary entry ID {vid}: {vocab.hanzi}")
                        db.session.delete(vocab)
                        deleted_vocab_count += 1
                    else:
                        logger.warning(f"Vocabulary entry {vid} not found in database")
                # Commit vocabulary deletions
                db.session.commit()
                logger.info(f"Successfully deleted {deleted_vocab_count} vocabulary entries")
            except Exception as ve:
                logger.error(f"Error deleting vocabulary entries: {ve}")
                db.session.rollback()
                raise
        
        # Delete the uploaded image file if it exists
        if log.image_path:
            try:
                image_file_path = os.path.join(os.getcwd(), log.image_path)
                if os.path.exists(image_file_path):
                    os.remove(image_file_path)
                    logger.info(f"Deleted image file: {image_file_path}")
                else:
                    logger.warning(f"Image file not found: {image_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete image file {log.image_path}: {e}")
        
        # Delete the log entry
        db.session.delete(log)
        db.session.commit()
        logger.info(f"Deleted log entry {log_id}")
        return jsonify({"success": True, "message": f"Log, {deleted_vocab_count} vocabulary entries, and image deleted"})
    except Exception as e:
        logger.error(f"Error deleting log: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/db')
@admin_required
def admin_db():
    """Lightweight DB browser for admin (read-only)."""
    try:
        page = max(1, int(request.args.get('page', 1) or 1))
        page_size = 50
        selected_table = request.args.get('table')

        # Fetch available tables (exclude sqlite internal)
        tables = [row[0] for row in db.session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)).fetchall()]

        if not tables:
            return render_template('admin_db.html', tables=[], selected_table=None, columns=[], rows=[],
                                   page=1, page_count=1, total_rows=0)

        if selected_table not in tables:
            selected_table = tables[0]

        # Columns
        col_rows = db.session.execute(text(f"PRAGMA table_info({selected_table})")).fetchall()
        columns = [c[1] for c in col_rows]

        # Row count
        total_rows = db.session.execute(text(f"SELECT COUNT(*) FROM {selected_table}"))
        total_rows = total_rows.scalar() if total_rows else 0
        page_count = max(1, ceil(total_rows / page_size)) if total_rows else 1
        page = min(page, page_count)
        offset = (page - 1) * page_size

        # Rows (order by rowid desc for newest first)
        rows = db.session.execute(
            text(f"SELECT * FROM {selected_table} ORDER BY rowid DESC LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        ).mappings().all()

        return render_template(
            'admin_db.html',
            tables=tables,
            selected_table=selected_table,
            columns=columns,
            rows=rows,
            page=page,
            page_count=page_count,
            total_rows=total_rows,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error loading DB browser: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/admin/image/<int:log_id>')
def get_log_image(log_id):
    """Serve the uploaded image for a specific log entry."""
    try:
        log = db.session.get(PhotoLog, log_id)
        if not log or not log.image_path:
            return jsonify({"error": "Image not found"}), 404
        
        if not os.path.exists(log.image_path):
            return jsonify({"error": "Image file not found on server"}), 404
        
        return send_file(log.image_path, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        return jsonify({"error": str(e)}), 500


# ====================== QUIZ ENDPOINTS ======================

def _calculate_string_similarity(s1: str, s2: str) -> float:
    """Simple similarity metric: shared character count / max length."""
    if not s1 or not s2:
        return 0.0
    s1_lower = s1.lower()
    s2_lower = s2.lower()
    common = sum(1 for c in s1_lower if c in s2_lower)
    return common / max(len(s1_lower), len(s2_lower)) if max(len(s1_lower), len(s2_lower)) > 0 else 0.0

def _get_similar_options(correct_word_id: int, max_options: int = 3) -> list:
    """
    Fetch similar words from the database (by sound/appearance similarity).
    Returns list of word IDs (not including the correct word).
    """
    try:
        correct = db.session.get(Vocabulary, correct_word_id)
        if not correct:
            return []
        
        all_words = Vocabulary.query.filter_by(is_approved=True).all()
        candidates = [(w, _calculate_string_similarity(correct.pinyin, w.pinyin)) 
                      for w in all_words if w.id != correct_word_id and w.pinyin]
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N similar words
        return [w.id for w, _ in candidates[:max_options]]
    except Exception as e:
        logger.error(f"Error fetching similar options: {e}")
        return []

def _get_or_generate_explanation(word: Vocabulary) -> str:
    """
    Return cached explanation or generate one using OpenAI and cache it.
    """
    if word.explanation:
        return word.explanation
    
    try:
        prompt = f"""Provide a brief, concise explanation (1-2 sentences max) for why the student should remember the word:
Chinese: {word.hanzi}
Pinyin: {word.pinyin}
English: {word.english}
French: {word.french}

Explanation:"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        explanation = response.choices[0].message.content.strip()
        word.explanation = explanation
        db.session.commit()
        logger.info(f"Generated explanation for word {word.id}: {explanation[:50]}...")
        return explanation
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return "Keep practicing this word!"

@app.route('/quiz/options', methods=['POST'])
def get_quiz_options():
    """
    Given a correct word ID, return it along with 3 similar distractor options.
    Response format: {
        "correct_id": int,
        "correct_word": {...},
        "options": [
            {"id": int, "hanzi": str, "pinyin": str, "english": str, "french": str},
            ...
        ],
        "explanation": str
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        word_id = data.get('word_id')
        
        if not word_id:
            return jsonify({"error": "word_id required"}), 400
        
        correct = db.session.get(Vocabulary, word_id)
        if not correct:
            return jsonify({"error": "Word not found"}), 404
        
        # Get 3 similar words as distractors
        similar_ids = _get_similar_options(word_id, max_options=3)
        if len(similar_ids) < 3:
            # Fallback: add random words to reach 3 options
            all_ids = [w.id for w in Vocabulary.query.filter_by(is_approved=True).all() if w.id != word_id]
            import random
            while len(similar_ids) < 3 and all_ids:
                idx = random.randint(0, len(all_ids) - 1)
                if all_ids[idx] not in similar_ids:
                    similar_ids.append(all_ids[idx])
                all_ids.pop(idx)
        
        similar_ids = similar_ids[:3]
        distractors = [db.session.get(Vocabulary, wid) for wid in similar_ids]
        distractors = [w for w in distractors if w]
        
        # Shuffle options (including the correct answer)
        import random
        options = [correct] + distractors
        random.shuffle(options)
        
        explanation = _get_or_generate_explanation(correct)
        
        return jsonify({
            "correct_id": correct.id,
            "correct_word": {
                "id": correct.id,
                "hanzi": correct.hanzi,
                "pinyin": correct.pinyin,
                "english": correct.english,
                "french": correct.french,
                "sent_hanzi": correct.sent_hanzi,
                "sent_pinyin": correct.sent_pinyin,
                "sent_english": correct.sent_english,
                "sent_french": correct.sent_french,
            },
            "options": [
                {
                    "id": opt.id,
                    "hanzi": opt.hanzi,
                    "pinyin": opt.pinyin,
                    "english": opt.english,
                    "french": opt.french,
                } for opt in options
            ],
            "explanation": explanation
        })
    except Exception as e:
        logger.error(f"Error in get_quiz_options: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/quiz/check', methods=['POST'])
def check_quiz_answer():
    """
    Validate the user's answer choice.
    Request: {"correct_id": int, "selected_id": int}
    Response: {"correct": bool, "correct_id": int, "explanation": str}
    """
    try:
        data = request.get_json(silent=True) or {}
        correct_id = data.get('correct_id')
        selected_id = data.get('selected_id')
        
        if not correct_id or not selected_id:
            return jsonify({"error": "correct_id and selected_id required"}), 400
        
        is_correct = (correct_id == selected_id)
        
        correct_word = db.session.get(Vocabulary, correct_id)
        if not correct_word:
            return jsonify({"error": "Correct word not found"}), 404
        
        explanation = _get_or_generate_explanation(correct_word)
        
        return jsonify({
            "correct": is_correct,
            "correct_id": correct_id,
            "explanation": explanation
        })
    except Exception as e:
        logger.error(f"Error in check_quiz_answer: {e}")
        return jsonify({"error": str(e)}), 500

# ====================== SPEECH RECOGNITION ENDPOINT ======================

@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    """
    Server-side speech recognition using Google Speech-to-Text.
    Accepts audio file, transcribes it, and validates against expected text.
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        expected_text = request.form.get('expected_text', '')
        language_code = request.form.get('language_code', 'zh-CN')
        
        if not expected_text:
            return jsonify({"error": "Expected text is required"}), 400
        
        logger.info(f"Transcribing audio: language={language_code}, expected='{expected_text}'")
        
        # Read audio content
        audio_content = audio_file.read()
        
        if not audio_content:
            return jsonify({"error": "Empty audio file"}), 400
        
        # Initialize Google Speech client
        client = speech.SpeechClient()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=audio_content)
        
        # Configure recognition settings
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # Common for web browsers
            sample_rate_hertz=48000,
            language_code=language_code,
            enable_automatic_punctuation=False,
            model='default',
            use_enhanced=True if language_code in ['en-US', 'zh-CN'] else False
        )
        
        try:
            # Perform recognition
            response = client.recognize(config=config, audio=audio)
            
            if not response.results:
                logger.warning("No speech detected in audio")
                return jsonify({
                    "success": False,
                    "recognized": "",
                    "confidence": 0.0,
                    "is_correct": False,
                    "message": "No speech detected. Please try speaking louder and clearer."
                })
            
            # Get the best transcription
            transcript = response.results[0].alternatives[0].transcript
            confidence = response.results[0].alternatives[0].confidence
            
            logger.info(f"Recognized: '{transcript}' (confidence: {confidence:.2f})")
            
            # Validate pronunciation
            is_correct = _check_pronunciation_match(transcript, expected_text, language_code)
            
            return jsonify({
                "success": True,
                "recognized": transcript,
                "confidence": confidence,
                "is_correct": is_correct,
                "expected": expected_text
            })
            
        except Exception as speech_error:
            logger.error(f"Speech recognition error: {speech_error}")
            # Try with different audio encoding if webm fails
            if 'encoding' in str(speech_error).lower():
                config.encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
                try:
                    response = client.recognize(config=config, audio=audio)
                    if response.results:
                        transcript = response.results[0].alternatives[0].transcript
                        confidence = response.results[0].alternatives[0].confidence
                        is_correct = _check_pronunciation_match(transcript, expected_text, language_code)
                        return jsonify({
                            "success": True,
                            "recognized": transcript,
                            "confidence": confidence,
                            "is_correct": is_correct,
                            "expected": expected_text
                        })
                except:
                    pass
            
            return jsonify({
                "error": f"Speech recognition failed: {str(speech_error)[:100]}"
            }), 500
            
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def _check_pronunciation_match(recognized: str, expected: str, language_code: str) -> bool:
    """
    Check if recognized speech matches expected text.
    Same logic as frontend but on server.
    """
    def normalize_text(text):
        if not text:
            return ''
        text = text.lower().strip()
        text = re.sub(r'[.,!?;:\'"()\[\]{}]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    normalized_recognized = normalize_text(recognized)
    normalized_expected = normalize_text(expected)
    
    # Exact match
    if normalized_recognized == normalized_expected:
        return True
    
    # For Chinese, check character-by-character (ignoring spaces)
    if language_code.startswith('zh'):
        recognized_no_space = normalized_recognized.replace(' ', '')
        expected_no_space = normalized_expected.replace(' ', '')
        
        if recognized_no_space == expected_no_space:
            return True
        
        # Check if all expected characters are present
        expected_chars = list(expected_no_space)
        if expected_chars and all(char in recognized_no_space for char in expected_chars):
            return True
    
    # Calculate similarity (Levenshtein-based)
    similarity = _calculate_text_similarity(normalized_recognized, normalized_expected)
    return similarity >= 0.7

def _calculate_text_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    longer = s1 if len(s1) > len(s2) else s2
    shorter = s2 if len(s1) > len(s2) else s1
    
    if len(longer) == 0:
        return 1.0
    
    edit_distance = _get_edit_distance(longer, shorter)
    return (len(longer) - edit_distance) / len(longer)

def _get_edit_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    s1 = s1.lower()
    s2 = s2.lower()
    
    costs = []
    for i in range(len(s1) + 1):
        last_value = i
        for j in range(len(s2) + 1):
            if i == 0:
                costs.append(j)
            elif j > 0:
                new_value = costs[j - 1]
                if s1[i - 1] != s2[j - 1]:
                    new_value = min(min(new_value, last_value), costs[j]) + 1
                costs[j - 1] = last_value
                last_value = new_value
        if i > 0:
            costs[len(s2)] = last_value
    
    return costs[len(s2)]


# ====================== USER API ENDPOINTS ======================

@app.route('/api/user/check')
def check_user_auth():
    """Check if user is logged in and return user info"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"authenticated": False})
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"authenticated": False})
    
    return jsonify({
        "authenticated": True,
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name or "User",
        "is_admin": user.is_admin,
        "is_onboarded": user.is_onboarded
    })


@app.route('/api/user/sections')
def get_available_sections():
    """Get all available sections for onboarding"""
    sections = db.session.query(Vocabulary.section).filter_by(is_approved=True).distinct().all()
    return jsonify([{"name": s[0], "count": Vocabulary.query.filter_by(section=s[0], is_approved=True).count()} for s in sections if s[0]])


@app.route('/api/user/onboard', methods=['POST'])
def user_onboard():
    """Complete user onboarding and import selected categories"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json() or {}
    selected_sections = data.get('sections', [])  # List of section names
    
    # Import vocabulary from selected sections
    imported_count = 0
    if selected_sections:
        vocab_items = Vocabulary.query.filter(
            Vocabulary.section.in_(selected_sections),
            Vocabulary.is_approved == True
        ).all()
        
        for vocab in vocab_items:
            # Check if already added
            existing = UserVocabulary.query.filter_by(
                user_id=user.id,
                vocabulary_id=vocab.id
            ).first()
            if not existing:
                user_vocab = UserVocabulary(user_id=user.id, vocabulary_id=vocab.id)
                db.session.add(user_vocab)
                imported_count += 1
    
    # Mark user as onboarded
    user.is_onboarded = True
    db.session.commit()
    
    return jsonify({
        "success": True,
        "imported_count": imported_count,
        "message": f"Successfully imported {imported_count} words!"
    })


@app.route('/api/user/vocabulary')
def get_user_vocabulary():
    """Get vocabulary for the logged-in user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])  # Return empty for non-authenticated users
    
    # Get user's vocabulary IDs
    user_vocab = UserVocabulary.query.filter_by(user_id=user_id).all()
    vocab_ids = [uv.vocabulary_id for uv in user_vocab]
    
    if not vocab_ids:
        return jsonify([])
    
    # Get the actual vocabulary items
    vocab_items = Vocabulary.query.filter(Vocabulary.id.in_(vocab_ids)).all()
    
    return jsonify([{
        "id": v.id,
        "section": v.section,
        "hanzi": v.hanzi,
        "pinyin": v.pinyin,
        "english": v.english,
        "french": v.french,
        "sent_hanzi": v.sent_hanzi,
        "sent_pinyin": v.sent_pinyin,
        "sent_english": v.sent_english,
        "sent_french": v.sent_french
    } for v in vocab_items])


@app.route('/api/user/preferences', methods=['POST'])
def update_user_preferences():
    """Update user vocabulary preferences (add/remove categories)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json() or {}
    action = data.get('action')  # 'add' or 'remove'
    sections = data.get('sections', [])
    
    if action == 'add':
        # Add vocabulary from selected sections
        vocab_items = Vocabulary.query.filter(
            Vocabulary.section.in_(sections),
            Vocabulary.is_approved == True
        ).all()
        
        added_count = 0
        for vocab in vocab_items:
            existing = UserVocabulary.query.filter_by(
                user_id=user.id,
                vocabulary_id=vocab.id
            ).first()
            if not existing:
                user_vocab = UserVocabulary(user_id=user.id, vocabulary_id=vocab.id)
                db.session.add(user_vocab)
                added_count += 1
        
        db.session.commit()
        return jsonify({"success": True, "added": added_count, "message": f"Added {added_count} words"})
    
    elif action == 'remove':
        # Remove vocabulary from selected sections
        vocab_items = Vocabulary.query.filter(
            Vocabulary.section.in_(sections),
            Vocabulary.is_approved == True
        ).all()
        vocab_ids = [v.id for v in vocab_items]
        
        removed_count = UserVocabulary.query.filter(
            UserVocabulary.user_id == user.id,
            UserVocabulary.vocabulary_id.in_(vocab_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({"success": True, "removed": removed_count, "message": f"Removed {removed_count} words"})
    
    return jsonify({"error": "Invalid action"}), 400


@app.route('/api/user/imported-sections')
def get_user_imported_sections():
    """Get list of sections the user has imported"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])
    
    # Get all vocabulary IDs the user has
    user_vocab = UserVocabulary.query.filter_by(user_id=user_id).all()
    vocab_ids = [uv.vocabulary_id for uv in user_vocab]
    
    if not vocab_ids:
        return jsonify([])
    
    # Get unique sections
    sections = db.session.query(Vocabulary.section).filter(
        Vocabulary.id.in_(vocab_ids)
    ).distinct().all()
    
    return jsonify([s[0] for s in sections if s[0]])


if __name__ == '__main__':
    create_tables_and_populate()
    # Use config-based debug mode
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config['DEBUG'])