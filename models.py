# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100), nullable=False)
    
    # ← CHANGE THESE TO nullable=True
    hanzi = db.Column(db.String(50), nullable=True, default='')
    pinyin = db.Column(db.String(100), nullable=True, default='')
    english = db.Column(db.String(200), nullable=True, default='')
    french = db.Column(db.String(200), nullable=True, default='')
    
    # Keep example sentences nullable too (or set default='')
    sent_hanzi = db.Column(db.String(100), nullable=True, default='')
    sent_pinyin = db.Column(db.String(150), nullable=True, default='')
    sent_english = db.Column(db.String(200), nullable=True, default='')
    sent_french = db.Column(db.String(200), nullable=True, default='')
    
    # Quiz explanation field (cached from AI)
    explanation = db.Column(db.Text, nullable=True, default='')
    
    # Visibility/approval status - hide until admin approves
    is_approved = db.Column(db.Boolean, nullable=False, default=False)


class PhotoLog(db.Model):
    """Logs all photo upload attempts for admin review."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_ip = db.Column(db.String(50), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
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