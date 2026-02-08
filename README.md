# Vocab Lab - Chinese-French Vocabulary Learning Platform

A production-ready Flask web application for learning Chinese with French and English translations. Features AI-powered photo OCR, quiz generation, and pronunciation practice.

## ✨ Features

- **Multi-language Vocabulary Database**: Chinese (Hanzi + Pinyin) ↔ English ↔ French
- **Photo Upload & OCR**: Upload textbook/flashcard photos → Google Vision OCR → AI processing → Admin approval
- **AI-Powered Quiz**: GPT-generated quizzes with semantically similar distractors
- **Speech Recognition**: Google Speech-to-Text for pronunciation validation
- **Admin Dashboard**: Review and manage user-uploaded vocabulary with visual OCR feedback
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud account (Vision API + Speech-to-Text API)
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd website
```

2. **Create virtual environment**
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Set up Google Cloud credentials**
- Download service account JSON from Google Cloud Console
- Set path in `.env`: `GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json`

6. **Initialize database**
```bash
python init_db.py
```

7. **Run the application**
```bash
# Development
python app_fixed.py

# Production
gunicorn app_fixed:app --bind 0.0.0.0:8000
```

Visit `http://localhost:5000` (development) or `http://localhost:8000` (production)

## 🔐 Admin Access

Default admin endpoint: `/admin/login`

**First-time setup:**
1. Generate a secure password hash:
```python
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```
2. Add to `.env`:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<paste-bcrypt-hash>
```

## 📁 Project Structure

```
website/
├── app_fixed.py           # Main Flask application
├── models.py              # SQLAlchemy database models
├── config.py              # Configuration management
├── extract_data.py        # Initial data import
├── init_db.py            # Database initialization
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── templates/            # HTML templates
│   ├── index.html        # Main application
│   ├── admin.html        # Admin dashboard
│   ├── admin_login.html  # Admin authentication
│   └── ...
├── static/               # CSS and assets
├── uploads/              # User-uploaded photos
├── logs/                 # Application logs
└── instance/             # SQLite database (dev)
```

## 🛠️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_ENV` | No | `development` or `production` (default: development) |
| `SECRET_KEY` | Yes (prod) | Flask secret key for sessions |
| `DATABASE_URL` | No | Database connection string (default: SQLite) |
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4o-mini |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to Google Cloud service account JSON |
| `ADMIN_USERNAME` | Yes | Admin login username |
| `ADMIN_PASSWORD` | Yes | Bcrypt-hashed admin password |
| `REDIS_URL` | No | Redis connection for rate limiting |
| `CORS_ORIGINS` | No | Allowed CORS origins (comma-separated) |

## 📚 API Endpoints

### Public
- `GET /` - Homepage
- `GET /search?q=&field=` - Search vocabulary
- `POST /upload_photo` - Upload photo for OCR
- `POST /quiz/options` - Get quiz question
- `POST /transcribe_audio` - Speech recognition

### Admin (Authentication Required)
- `POST /admin/login` - Admin login
- `GET /admin` - Admin dashboard
- `GET /admin/logs` - List photo uploads
- `POST /admin/log/<id>/validate` - Approve upload
- `DELETE /admin/log/<id>/delete` - Delete upload

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete API documentation.

## 🚢 Production Deployment

Comprehensive deployment guide available in [DEPLOYMENT.md](DEPLOYMENT.md)

**Quick deploy to Heroku:**
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set FLASK_ENV=production SECRET_KEY=<key> ...
git push heroku main
heroku run python init_db.py
```

**Supported platforms:**
- Heroku
- Google Cloud Run
- AWS Elastic Beanstalk
- DigitalOcean App Platform
- Traditional VPS (Ubuntu + Nginx)

## 🔒 Security Features

- ✅ Environment-based configuration (no hardcoded secrets)
- ✅ Bcrypt password hashing
- ✅ Session-based admin authentication
- ✅ Rate limiting on sensitive endpoints
- ✅ CORS protection
- ✅ Input validation and sanitization
- ✅ Secure session cookies (HTTPS in production)

## 🧪 Testing

```bash
# Run tests (if implemented)
pytest

# Test production config locally
export FLASK_ENV=production
gunicorn app_fixed:app --bind 0.0.0.0:8000

# Health check
curl http://localhost:8000/health
```

## 📊 Monitoring

Application logs: `logs/photo_processing_YYYYMMDD.log`

**Recommended monitoring:**
- UptimeRobot (uptime)
- Papertrail (log aggregation)
- New Relic (APM)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

[Add your license here]

## 🆘 Troubleshooting

**Database errors?**
- Run `python init_db.py` to create/update tables
- Check `DATABASE_URL` format

**API errors?**
- Verify `OPENAI_API_KEY` is valid
- Ensure Google Cloud APIs are enabled
- Check API quotas and billing

**Upload errors?**
- Ensure `uploads/` directory exists and is writable
- Check `MAX_CONTENT_LENGTH` setting (16MB default)
- Verify Google Vision API credentials

**Authentication issues?**
- Verify `SECRET_KEY` is set in production
- Check `ADMIN_PASSWORD` is bcrypt-hashed
- Ensure cookies are enabled

## 📞 Support

For deployment questions, see [DEPLOYMENT.md](DEPLOYMENT.md)

For architecture details, see [.github/copilot-instructions.md](.github/copilot-instructions.md)

---

Made with ❤️ for language learners
