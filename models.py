# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100), nullable=False)
    
    # Track who added the word and when
    added_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    
    # ← CHANGE THESE TO nullable=True
    hanzi = db.Column(db.String(50), nullable=True, default='')
    pinyin = db.Column(db.String(100), nullable=True, default='')
    english = db.Column(db.String(200), nullable=True, default='')
    french = db.Column(db.String(200), nullable=True, default='')
    japanese_kanji = db.Column(db.String(200), nullable=True, default='')
    japanese_romaji = db.Column(db.String(200), nullable=True, default='')
    
    # Keep example sentences nullable too (or set default='')
    sent_hanzi = db.Column(db.String(100), nullable=True, default='')
    sent_pinyin = db.Column(db.String(150), nullable=True, default='')
    sent_english = db.Column(db.String(200), nullable=True, default='')
    sent_french = db.Column(db.String(200), nullable=True, default='')
    sent_japanese_kanji = db.Column(db.String(200), nullable=True, default='')
    sent_japanese_romaji = db.Column(db.String(200), nullable=True, default='')
    
    # Quiz explanation field (cached from AI)
    explanation = db.Column(db.Text, nullable=True, default='')
    
    # Visibility/approval status - hide until admin approves
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    # Global hide flag when a user deletes a word (admin still sees it)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)


class PhotoLog(db.Model):
    """Logs all photo upload attempts for admin review."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Track which user uploaded
    user_ip = db.Column(db.String(50), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)  # Legacy: kept for compatibility
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store actual image bytes in database
    image_width = db.Column(db.Integer, nullable=True)  # Actual image width
    image_height = db.Column(db.Integer, nullable=True)  # Actual image height
    section = db.Column(db.String(100), nullable=True)
    
    # OCR and processing results
    ocr_text = db.Column(db.Text, nullable=True)
    detected_language = db.Column(db.String(50), nullable=True)
    entries_json = db.Column(db.Text, nullable=True)  # JSON array of vocabulary entries created
    
    # Word-level bounding boxes from Vision API (for visualization)
    word_boxes_json = db.Column(db.Text, nullable=True)  # JSON array of {text, vertices, is_new}
    
    # Status and admin actions
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, validated, rejected
    created_count = db.Column(db.Integer, default=0)
    updated_count = db.Column(db.Integer, default=0)
    vocab_ids = db.Column(db.Text, nullable=True)  # Comma-separated IDs of created Vocabulary entries
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)


class User(db.Model):
    """User accounts with Google OAuth"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_onboarded = db.Column(db.Boolean, default=False)  # Track if user completed initial setup
    languages = db.Column(db.Text, nullable=True)  # JSON list of enabled languages
    visible_sections = db.Column(db.Text, nullable=True)  # JSON list of visible global sections; null = legacy all
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)


class PracticeScore(db.Model):
    """Track practice game scores for each user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # 'listening', 'words', 'speaking', 'drawing'
    score = db.Column(db.Integer, nullable=False, default=0)  # Number of correct answers
    total_questions = db.Column(db.Integer, nullable=False, default=0)  # Total questions in session
    percentage = db.Column(db.Float, nullable=True)  # Score percentage
    session_duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='practice_scores')
    results = db.relationship('PracticeResult', backref='practice_score', lazy='dynamic', cascade='all, delete-orphan')


class PracticeResult(db.Model):
    """Store individual question results for each practice session"""
    id = db.Column(db.Integer, primary_key=True)
    practice_score_id = db.Column(db.Integer, db.ForeignKey('practice_score.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)  # Order in the session
    
    # Word being tested
    vocabulary_id = db.Column(db.Integer, db.ForeignKey('vocabulary.id'), nullable=True)
    word_hanzi = db.Column(db.String(100), nullable=True)
    word_pinyin = db.Column(db.String(200), nullable=True)
    word_english = db.Column(db.String(300), nullable=True)
    word_french = db.Column(db.String(300), nullable=True)
    word_japanese_kanji = db.Column(db.String(300), nullable=True)
    word_japanese_romaji = db.Column(db.String(300), nullable=True)
    
    # Question and answer details
    question_type = db.Column(db.String(50), nullable=True)  # 'hanzi_to_pinyin', 'english_to_hanzi', 'speaking', 'drawing', etc.
    question_text = db.Column(db.Text, nullable=True)  # The question asked
    user_answer = db.Column(db.Text, nullable=True)  # What the user answered
    correct_answer = db.Column(db.Text, nullable=True)  # The correct answer
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    
    # AI feedback (cached from AIFeedback or generated)
    feedback = db.Column(db.Text, nullable=True)
    
    # Relationships
    vocabulary = db.relationship('Vocabulary', backref='practice_results')


class AIFeedback(db.Model):
    """Cache AI-generated feedback for common mistakes to reduce API costs"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Unique key for the mistake pattern
    game_type = db.Column(db.String(50), nullable=False)
    question_type = db.Column(db.String(50), nullable=True)
    correct_answer = db.Column(db.String(500), nullable=False)  # Normalized correct answer
    user_answer = db.Column(db.String(500), nullable=False)  # Normalized wrong answer
    
    # Cached feedback
    feedback_text = db.Column(db.Text, nullable=False)
    
    # Usage tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=1)  # How many times this cached feedback was reused
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Make the combination unique for lookup
    __table_args__ = (db.Index('idx_feedback_lookup', 'game_type', 'correct_answer', 'user_answer'),)